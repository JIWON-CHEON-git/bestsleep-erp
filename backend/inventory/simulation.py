"""재고흐름 시뮬레이션 엔진.

핵심 아이디어
-------------
제품은 서로 독립적이다(공통 자재/캐파 제약 없음 — 과제 범위 8장 참고).
따라서 제품별로 시작일~종료일까지의 흐름을 독립적으로 계산한 뒤, 그 결과를
DB에 일괄 저장한다.

하루 처리 순서 (제품별, D-2 명세 그대로)::

    1. process_inbound_arrivals   - 오늘 입고예정 생산발주 처리 → 재고 증가
    2. process_backorders         - 백오더 큐 FIFO 출고 (부분출고 금지)
    3. process_new_orders          - 오늘 신규 주문 처리 (재고 있으면 즉시 차감)
    4. decide_ship_dates           - 오늘 차감된 주문들의 배송 출발일/상태 결정
    5. calculate_closing_state     - 기말재고/가용재고/백오더잔량 계산
    6. check_reorder_and_place_orders - 가용재고 ≤ 재주문점이면 발주(연속 가능)

계산 로직은 Django 모델에 의존하지 않는 순수 파이썬 자료구조
(OrderState, ProductionOrderState, ProductSpec, LedgerRow)로 동작하므로
DB 없이 단위 테스트할 수 있다. ``run_simulation()``만 DB I/O를 담당한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

from inventory.constants import FulfillmentStatus, ProductionOrderStatus

if TYPE_CHECKING:
    from inventory.models import Order


# ----------------------------------------------------------------------
# 순수 자료구조 (DB 비의존)
# ----------------------------------------------------------------------


@dataclass
class ProductSpec:
    """시뮬레이션에 필요한 제품 파라미터만 담은 값 객체."""

    sku: str
    reorder_point: int
    moq: int
    production_lead_time_days: int
    delivery_lead_time_days: int
    initial_stock: int


@dataclass
class OrderState:
    """시뮬레이션 동안 추적되는 주문 한 건의 상태."""

    order_no: str
    order_date: date
    quantity: int
    desired_delivery_date: Optional[date] = None

    stock_deducted_date: Optional[date] = None
    shipped_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    status: str = FulfillmentStatus.PENDING
    delay_days: int = 0
    root_cause: str = ""


@dataclass
class ProductionOrderState:
    """시뮬레이션 동안 생성/추적되는 생산발주 한 건의 상태."""

    order_date: date
    quantity: int
    expected_arrival_date: date
    trigger_reason: str
    status: str = ProductionOrderStatus.PENDING
    received_date: Optional[date] = None


@dataclass
class LedgerRow:
    """제품 한 건, 날짜 하루치의 DailyLedger 데이터."""

    date: date
    opening_stock: int
    production_inbound: int
    order_outbound: int
    closing_stock: int
    available_stock: int
    order_quantity_today: int
    backorder_balance: int
    structural_shortage_flag: bool


@dataclass
class ProductSimResult:
    """제품 한 건에 대한 전체 시뮬레이션 결과."""

    product: ProductSpec
    ledger: list[LedgerRow] = field(default_factory=list)
    production_orders: list[ProductionOrderState] = field(default_factory=list)
    orders: dict[str, OrderState] = field(default_factory=dict)


@dataclass
class ProductSimState:
    """시뮬레이션 진행 중 가변 상태(재고/큐)를 담는 내부 작업용 컨테이너."""

    stock: int
    pending_pos: list[ProductionOrderState] = field(default_factory=list)
    backorder_queue: list[OrderState] = field(default_factory=list)
    last_processed_order_no: Optional[str] = None


# ----------------------------------------------------------------------
# 6단계 함수
# ----------------------------------------------------------------------


def process_inbound_arrivals(state: ProductSimState, today: date) -> int:
    """1) 오늘이 입고예정일인 생산발주를 입고 처리하고 재고에 더한다.

    Returns:
        오늘 입고된 수량 합 (production_inbound).
    """

    inbound = 0
    for po in state.pending_pos:
        if po.status == ProductionOrderStatus.PENDING and po.expected_arrival_date == today:
            po.status = ProductionOrderStatus.RECEIVED
            po.received_date = today
            inbound += po.quantity
    state.stock += inbound
    return inbound


def process_backorders(state: ProductSimState, today: date) -> list[OrderState]:
    """2) 백오더 큐를 FIFO로 처리한다. 부분출고는 하지 않는다.

    큐 맨 앞 주문의 수량을 현재 재고로 감당할 수 없으면 즉시 멈춘다
    (뒤 주문이 더 작더라도 순서를 건너뛰지 않음 — FIFO 우선).

    Returns:
        오늘 재고가 차감(출고 확정)된 주문 목록.
    """

    shipped: list[OrderState] = []
    while state.backorder_queue and state.backorder_queue[0].quantity <= state.stock:
        order = state.backorder_queue.pop(0)
        state.stock -= order.quantity
        order.stock_deducted_date = today
        shipped.append(order)
    return shipped


def process_new_orders(
    state: ProductSimState, today: date, todays_orders: list[OrderState]
) -> list[OrderState]:
    """3) 오늘 주문일인 신규 주문을 처리한다.

    재고가 충분하면 즉시 차감(출고 확정), 부족하면 백오더 큐 끝에 추가한다.
    ``todays_orders``는 호출 전에 order_no 순으로 정렬되어 있어야 한다.

    Returns:
        오늘 재고가 차감(출고 확정)된 주문 목록.
    """

    shipped: list[OrderState] = []
    for order in todays_orders:
        if order.quantity <= state.stock:
            state.stock -= order.quantity
            order.stock_deducted_date = today
            shipped.append(order)
        else:
            state.backorder_queue.append(order)
    return shipped


def _build_delay_root_cause(
    order: OrderState,
    production_orders: list[ProductionOrderState],
    suffix_label: str,
) -> str:
    """지연/약속불이행 주문의 비고를 "생산 입고 대기 (MM-DD 발주 → MM-DD 입고, N일 {지연|초과})" 형식으로 만든다.

    재고 차감일(stock_deducted_date)과 입고예정일(expected_arrival_date)이 같은
    생산발주를, 이 주문을 해소한 발주로 본다(백오더는 입고일에 바로 FIFO
    출고되므로 두 날짜가 항상 일치한다 — README 4-2절 참고).
    일치하는 발주가 없으면(생산 대기 없이 배송리드타임만으로 지연된 경우)
    배송 관점의 사유로 대체한다.
    """

    resolving_po = next(
        (po for po in production_orders if po.expected_arrival_date == order.stock_deducted_date),
        None,
    )
    if resolving_po is None:
        return f"배송 리드타임으로 희망배송일 초과 ({order.delay_days}일 {suffix_label})"

    return (
        f"생산 입고 대기 ({resolving_po.order_date.strftime('%m-%d')} 발주 → "
        f"{resolving_po.expected_arrival_date.strftime('%m-%d')} 입고, "
        f"{order.delay_days}일 {suffix_label})"
    )


def decide_ship_dates(
    orders: list[OrderState],
    product: ProductSpec,
    production_orders: list[ProductionOrderState],
) -> None:
    """4) 오늘 재고가 차감된 주문들의 배송 출발일/도착예정일/상태를 결정한다 (D-3).

    - 희망배송일이 없으면: 재고 차감일에 바로 출발.
      주문일에 차감되었으면 정상(normal), 그렇지 않으면 단순지연(simple_delay).
    - 희망배송일이 있으면: 재고는 차감일에 빼두지만, 트럭은
      max(차감일, 희망배송일 - 배송LT)에 출발한다(창고 보관).
      목표 출발일 이내면 약속이행(promise_kept), 넘으면 약속불이행(promise_broken).
    """

    delivery_lt = timedelta(days=product.delivery_lead_time_days)

    for order in orders:
        assert order.stock_deducted_date is not None

        if order.desired_delivery_date is None:
            order.shipped_date = order.stock_deducted_date
            order.expected_arrival_date = order.shipped_date + delivery_lt

            if order.stock_deducted_date == order.order_date:
                order.status = FulfillmentStatus.NORMAL
                order.delay_days = 0
                order.root_cause = ""
            else:
                order.status = FulfillmentStatus.SIMPLE_DELAY
                order.delay_days = (order.stock_deducted_date - order.order_date).days
                order.root_cause = _build_delay_root_cause(order, production_orders, "지연")
        else:
            target_ship_date = order.desired_delivery_date - delivery_lt
            order.shipped_date = max(order.stock_deducted_date, target_ship_date)
            order.expected_arrival_date = order.shipped_date + delivery_lt

            if order.shipped_date <= target_ship_date:
                order.status = FulfillmentStatus.PROMISE_KEPT
                order.delay_days = 0
                order.root_cause = ""
            else:
                order.status = FulfillmentStatus.PROMISE_BROKEN
                order.delay_days = (order.expected_arrival_date - order.desired_delivery_date).days
                order.root_cause = _build_delay_root_cause(order, production_orders, "초과")


def calculate_closing_state(state: ProductSimState) -> tuple[int, int, int, bool]:
    """5) 기말재고/가용재고/백오더잔량/구조적 부족 여부를 계산한다.

    가용재고 = 기말재고 + 미입고 발주 합 - 백오더 잔량 (음수 허용).
    구조적 부족 플래그는 발주(6단계)를 적용하기 *전* 가용재고를 기준으로 판단한다
    (발주 후에는 가용재고가 재주문점을 넘도록 보정되어 항상 0 이상이 되기 때문).

    Returns:
        (closing_stock, available_stock_before_reorder, backorder_balance, structural_shortage_flag)
    """

    closing_stock = state.stock
    incoming_po_sum = sum(
        po.quantity for po in state.pending_pos if po.status == ProductionOrderStatus.PENDING
    )
    backorder_balance = sum(order.quantity for order in state.backorder_queue)
    available_stock = closing_stock + incoming_po_sum - backorder_balance
    structural_shortage_flag = available_stock < 0

    return closing_stock, available_stock, backorder_balance, structural_shortage_flag


def check_reorder_and_place_orders(
    state: ProductSimState,
    today: date,
    available_stock: int,
    product: ProductSpec,
) -> tuple[int, int]:
    """6) 가용재고가 재주문점 이하이면 MOQ 단위로 생산발주를 낸다.

    한 번으로 재주문점을 회복하지 못하면(구조적 부족 포함) 회복할 때까지
    같은 날 여러 건을 연속으로 발주한다.

    Returns:
        (order_quantity_today, available_stock_after_reorder)
    """

    production_lt = timedelta(days=product.production_lead_time_days)
    order_quantity_today = 0

    while available_stock <= product.reorder_point:
        if state.last_processed_order_no:
            reason = (
                f"{state.last_processed_order_no} 처리 후 가용재고 {available_stock}개 "
                f"→ 재주문점({product.reorder_point}) 이하"
            )
        else:
            reason = f"가용재고 {available_stock}개 → 재주문점({product.reorder_point}) 이하"
        po = ProductionOrderState(
            order_date=today,
            quantity=product.moq,
            expected_arrival_date=today + production_lt,
            trigger_reason=reason,
        )
        state.pending_pos.append(po)
        available_stock += product.moq
        order_quantity_today += product.moq

    return order_quantity_today, available_stock


# ----------------------------------------------------------------------
# 제품 단위 시뮬레이션
# ----------------------------------------------------------------------


def simulate_product(
    product: ProductSpec,
    orders: list[OrderState],
    start_date: date,
    end_date: date,
) -> ProductSimResult:
    """제품 한 건에 대해 start_date~end_date(포함)를 하루씩 진행한다.

    Args:
        product: 제품 파라미터.
        orders: 이 제품에 대한 활성(active) 주문 목록. 정렬은 함수 내부에서 보장한다.
        start_date: 시뮬레이션 시작일.
        end_date: 시뮬레이션 종료일(포함).

    Returns:
        제품의 일자별 원장, 생성된 생산발주, 주문별 처리 결과.
    """

    sorted_orders = sorted(orders, key=lambda o: (o.order_date, o.order_no))
    orders_by_date: dict[date, list[OrderState]] = {}
    for order in sorted_orders:
        orders_by_date.setdefault(order.order_date, []).append(order)

    state = ProductSimState(stock=product.initial_stock)
    result = ProductSimResult(product=product, orders={o.order_no: o for o in sorted_orders})

    current = start_date
    while current <= end_date:
        opening_stock = state.stock

        production_inbound = process_inbound_arrivals(state, current)

        shipped_from_backorder = process_backorders(state, current)
        shipped_new = process_new_orders(state, current, orders_by_date.get(current, []))
        newly_shipped = shipped_from_backorder + shipped_new
        order_outbound = sum(o.quantity for o in newly_shipped)

        if newly_shipped:
            state.last_processed_order_no = newly_shipped[-1].order_no

        decide_ship_dates(newly_shipped, product, state.pending_pos)

        closing_stock, available_before_reorder, backorder_balance, structural_shortage_flag = (
            calculate_closing_state(state)
        )

        order_quantity_today, available_after_reorder = check_reorder_and_place_orders(
            state, current, available_before_reorder, product
        )

        result.ledger.append(
            LedgerRow(
                date=current,
                opening_stock=opening_stock,
                production_inbound=production_inbound,
                order_outbound=order_outbound,
                closing_stock=closing_stock,
                available_stock=available_after_reorder,
                order_quantity_today=order_quantity_today,
                backorder_balance=backorder_balance,
                structural_shortage_flag=structural_shortage_flag,
            )
        )

        current += timedelta(days=1)

    for order in result.orders.values():
        if order.status == FulfillmentStatus.PENDING:
            order.root_cause = "입고 대기 중"

    result.production_orders = state.pending_pos
    return result


# ----------------------------------------------------------------------
# 시뮬레이션 기간 결정
# ----------------------------------------------------------------------


def determine_simulation_end_date(
    configured_end_date: date,
    orders: list[tuple[date, ProductSpec]],
) -> date:
    """종료일을 (설정된 종료일) vs (마지막 주문일 + 생산LT + 배송LT) 중 더 늦은 날로 정한다.

    Args:
        configured_end_date: SimulationConfig.end_date.
        orders: (order_date, 해당 주문의 제품 ProductSpec) 목록 — 활성 주문만.
    """

    latest = configured_end_date
    for order_date, product in orders:
        candidate = order_date + timedelta(
            days=product.production_lead_time_days + product.delivery_lead_time_days
        )
        if candidate > latest:
            latest = candidate
    return latest


# ----------------------------------------------------------------------
# DB 연동 (run_simulation)
# ----------------------------------------------------------------------


def run_simulation() -> dict[str, ProductSimResult]:
    """전체 제품에 대해 시뮬레이션을 실행하고 결과를 DB에 반영한다.

    기존의 자동 생성 데이터(DailyLedger 전체, ProductionOrder 전체,
    OrderFulfillment 전체)를 삭제한 뒤 새로 계산한 결과로 다시 채운다.
    Order(주문 원본)와 Product(제품마스터)는 건드리지 않는다.

    Returns:
        SKU -> ProductSimResult. (테스트/콘솔 검증용)
    """

    from django.db import transaction

    from inventory.constants import OrderStatus
    from inventory.models import (
        DailyLedger,
        Order,
        OrderFulfillment,
        Product,
        ProductionOrder,
        SimulationConfig,
    )

    config = SimulationConfig.objects.first()
    if config is None:
        raise RuntimeError("SimulationConfig가 없습니다. 먼저 seed_data를 실행하세요.")

    products = list(Product.objects.all())
    product_specs: dict[str, ProductSpec] = {
        p.sku: ProductSpec(
            sku=p.sku,
            reorder_point=p.reorder_point,
            moq=p.moq,
            production_lead_time_days=p.production_lead_time_days,
            delivery_lead_time_days=p.delivery_lead_time_days,
            initial_stock=p.initial_stock,
        )
        for p in products
    }

    active_orders = list(
        Order.objects.filter(status=OrderStatus.ACTIVE).select_related("product")
    )

    end_date = determine_simulation_end_date(
        config.end_date,
        [(o.order_date, product_specs[o.product_id]) for o in active_orders],
    )
    start_date = config.start_date

    orders_by_sku: dict[str, list[OrderState]] = {sku: [] for sku in product_specs}
    for o in active_orders:
        orders_by_sku[o.product_id].append(
            OrderState(
                order_no=o.order_no,
                order_date=o.order_date,
                quantity=o.quantity,
                desired_delivery_date=o.desired_delivery_date,
            )
        )

    results: dict[str, ProductSimResult] = {
        sku: simulate_product(spec, orders_by_sku[sku], start_date, end_date)
        for sku, spec in product_specs.items()
    }

    with transaction.atomic():
        OrderFulfillment.objects.all().delete()
        DailyLedger.objects.all().delete()
        ProductionOrder.objects.all().delete()

        ledger_rows: list[DailyLedger] = []
        po_objects: list[ProductionOrder] = []
        fulfillment_objects: list[OrderFulfillment] = []

        for sku, res in results.items():
            for row in res.ledger:
                ledger_rows.append(
                    DailyLedger(
                        product_id=sku,
                        date=row.date,
                        opening_stock=row.opening_stock,
                        production_inbound=row.production_inbound,
                        order_outbound=row.order_outbound,
                        closing_stock=row.closing_stock,
                        available_stock=row.available_stock,
                        order_quantity_today=row.order_quantity_today,
                        backorder_balance=row.backorder_balance,
                        structural_shortage_flag=row.structural_shortage_flag,
                    )
                )

            for po in res.production_orders:
                po_objects.append(
                    ProductionOrder(
                        product_id=sku,
                        order_date=po.order_date,
                        quantity=po.quantity,
                        expected_arrival_date=po.expected_arrival_date,
                        status=po.status,
                        received_date=po.received_date,
                        trigger_reason=po.trigger_reason,
                    )
                )

            for order_no, ostate in res.orders.items():
                fulfillment_objects.append(
                    OrderFulfillment(
                        order_id=order_no,
                        stock_deducted_date=ostate.stock_deducted_date,
                        shipped_date=ostate.shipped_date,
                        expected_arrival_date=ostate.expected_arrival_date,
                        status=ostate.status,
                        delay_days=ostate.delay_days,
                        root_cause=ostate.root_cause,
                    )
                )

        DailyLedger.objects.bulk_create(ledger_rows)
        ProductionOrder.objects.bulk_create(po_objects)
        OrderFulfillment.objects.bulk_create(fulfillment_objects)

    return results


# ----------------------------------------------------------------------
# 주문 취소 (D-4)
# ----------------------------------------------------------------------


def cancel_order(order: "Order", as_of_date: "Optional[date]" = None) -> None:
    """주문을 취소하고 시뮬레이션을 재실행한다 (D-4).

    - 기본(``as_of_date=None``)은 명세 그대로 출고 전
      (``OrderFulfillment.shipped_date`` 가 비어 있음)인 주문만 취소 가능.
    - ``as_of_date``(기준일)가 주어지면, ``shipped_date`` 가 설정되어 있어도
      그 날짜가 기준일보다 미래라면 취소를 허용한다. 시뮬레이션은 전체
      미래를 미리 계산해 두므로, "오늘(기준일)" 시점에서는 아직 출고되지
      않은 주문이기 때문이다 (README 4-1절 참고).
    - 취소된 주문은 ``Order.status='cancelled'`` 로 표시되어 다음
      ``run_simulation()`` 부터는 활성 주문 목록에서 제외된다.
      - 아직 재고가 차감되지 않았던(백오더) 주문은 재계산 시 백오더 큐에서
        자연히 사라진다.
      - 이미 재고가 차감되었던 주문은 재계산 시 그 차감 자체가 일어나지
        않으므로, 결과적으로 재고가 "복귀"된 것과 같은 효과를 갖는다.

    재고/큐 상태를 부분적으로 직접 수정하는 대신 전체 재시뮬레이션으로
    일관성을 보장한다(계산 일관성 우선, 데이터 규모가 작아 비용 부담 없음).

    Raises:
        ValueError: 취소 가능 시점이 지난(이미 출고된) 주문을 취소하려는 경우.
    """

    from django.utils import timezone

    from inventory.constants import OrderStatus

    fulfillment = getattr(order, "fulfillment", None)
    if fulfillment is not None and fulfillment.shipped_date is not None:
        if as_of_date is None or fulfillment.shipped_date <= as_of_date:
            raise ValueError("이미 출고된 주문은 취소할 수 없습니다.")

    order.status = OrderStatus.CANCELLED
    order.cancelled_at = timezone.now()
    order.save(update_fields=["status", "cancelled_at"])

    run_simulation()
