"""reference_date(기준일)에 의존하는 조회/가공 로직 (E단계 API용).

``simulation.py``는 reference_date와 무관하게 시뮬레이션 기간 전체를
한 번에 계산한 "결정론적 미래 결과"(DailyLedger/ProductionOrder/
OrderFulfillment)를 만든다.

이 모듈은 그 결과를 "오늘은 기준일(reference_date)이다"라는 관점에서
다시 해석해, 화면(E-1~E-5)에 보여줄 형태로 가공한다.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from django.db.models import Sum

from inventory.constants import (
    FulfillmentStatus,
    OrderStatus,
    ProductionOrderStatus,
    ProductStatus,
    WARNING_BUFFER_RATIO,
)
from inventory.estimation import estimate_fulfillment_date
from inventory.models import (
    DailyLedger,
    Order,
    OrderFulfillment,
    Product,
    ProductionOrder,
    SimulationConfig,
)


def get_default_reference_date() -> date:
    """기준일이 주어지지 않았을 때 사용할 기본값 (시뮬레이션 시작일)."""

    config = SimulationConfig.objects.first()
    if config is None:
        raise RuntimeError("SimulationConfig가 없습니다. 먼저 seed_data를 실행하세요.")
    return config.start_date


def parse_reference_date(value: Optional[str]) -> date:
    """쿼리 파라미터 문자열을 기준일로 변환한다. 비어있으면 기본값을 사용한다."""

    if not value:
        return get_default_reference_date()
    return date.fromisoformat(value)


def get_ledger_row(product: Product, reference_date: date) -> Optional[DailyLedger]:
    """기준일 시점의 DailyLedger 행.

    - 기준일이 시뮬레이션 시작일 이후면 해당 날짜 이하의 가장 최근 행.
    - 기준일이 시뮬레이션 시작일 이전이면 None (아직 시뮬레이션이 시작되지
      않은 상태 = 초기재고로 간주).
    - 기준일이 시뮬레이션 종료일 이후면 마지막 행으로 고정(clamp)된다
      (가장 최근 행이 그대로 반환됨).
    """

    return (
        DailyLedger.objects.filter(product=product, date__lte=reference_date)
        .order_by("-date")
        .first()
    )


def get_current_and_available_stock(product: Product, reference_date: date) -> tuple[int, int]:
    """기준일 시점의 (현재고, 가용재고)."""

    row = get_ledger_row(product, reference_date)
    if row is None:
        return product.initial_stock, product.initial_stock
    return row.closing_stock, row.available_stock


def get_incoming_quantity(product: Product, reference_date: date) -> int:
    """기준일 시점에 발주는 됐지만 아직 입고되지 않은 생산발주 수량의 합."""

    total = ProductionOrder.objects.filter(
        product=product,
        order_date__lte=reference_date,
        expected_arrival_date__gt=reference_date,
    ).aggregate(total=Sum("quantity"))["total"]
    return total or 0


def is_order_pending_as_of(fulfillment: OrderFulfillment, reference_date: date) -> bool:
    """기준일 시점에 아직 재고가 차감되지 않은(=백오더 대기) 상태인가."""

    return (
        fulfillment.stock_deducted_date is None
        or fulfillment.stock_deducted_date > reference_date
    )


def get_backorder_count(product: Product, reference_date: date) -> int:
    """기준일 시점에 이 제품에서 백오더 대기 중인 활성 주문 수.

    주문일이 기준일보다 미래인 주문은 "아직 접수되지 않은 주문"이므로
    백오더로 집계하지 않는다.
    """

    fulfillments = OrderFulfillment.objects.filter(
        order__product=product,
        order__status=OrderStatus.ACTIVE,
        order__order_date__lte=reference_date,
    ).select_related("order")
    return sum(1 for f in fulfillments if is_order_pending_as_of(f, reference_date))


def get_product_status(current_stock: int, product: Product) -> str:
    """제품 목록(E-2)의 재고 상태 분류.

    우선순위: shortage > below_reorder > warning > normal.

    재주문 로직(check_reorder_and_place_orders)이 매일 가용재고를 재주문점
    초과로 회복시켜 두기 때문에, 저장된 available_stock은 음수가 될 수 없다.
    따라서 "부족(품절)"은 현재고가 0인지로 판단한다.
    """

    if current_stock == 0:
        return ProductStatus.SHORTAGE
    if current_stock <= product.reorder_point:
        return ProductStatus.BELOW_REORDER
    if current_stock <= product.reorder_point * WARNING_BUFFER_RATIO:
        return ProductStatus.WARNING
    return ProductStatus.NORMAL


def get_production_order_display_status(po: ProductionOrder, reference_date: date) -> str:
    """기준일 시점의 입고 상태.

    DB의 ``status``/``received_date``는 시뮬레이션 전체(미래 포함) 기준이라
    기준일 시점과 다를 수 있으므로, ``expected_arrival_date``를 기준일과
    비교해 다시 계산한다.
    """

    if po.expected_arrival_date <= reference_date:
        return ProductionOrderStatus.RECEIVED
    return ProductionOrderStatus.PENDING


def get_order_view(order: Order, reference_date: date) -> dict:
    """주문 한 건을 기준일 관점에서 본 표시용 데이터로 변환한다 (E-5).

    - 취소된 주문: status="cancelled", 취소 불가.
    - 기준일 시점에 아직 재고가 차감되지 않은 주문(백오더 대기 또는 미래
      주문): status="pending", ``estimate_fulfillment_date``로 예상 입고일을
      계산해 ``expected_arrival_date``에 채운다. 항상 취소 가능.
    - 그 외(이미 재고가 차감된 주문): 시뮬레이션이 계산한 최종 결과를 그대로
      보여준다. ``shipped_date``가 기준일보다 미래면 아직 취소 가능
      (README 4-1절 참고).
    """

    if order.status == OrderStatus.CANCELLED:
        return {
            "status": FulfillmentStatus.CANCELLED,
            "stock_deducted_date": None,
            "shipped_date": None,
            "expected_arrival_date": None,
            "delay_days": 0,
            "root_cause": "주문 취소됨",
            "is_cancellable": False,
        }

    fulfillment: Optional[OrderFulfillment] = getattr(order, "fulfillment", None)

    if fulfillment is None or is_order_pending_as_of(fulfillment, reference_date):
        estimated_arrival = estimate_fulfillment_date(
            order.product, order.quantity, reference_date, exclude_order_no=order.order_no
        )
        if order.order_date > reference_date:
            root_cause = "주문일 이후 처리될 예정"
        elif estimated_arrival is not None:
            root_cause = f"재고 부족으로 대기 중 (예상 입고 {estimated_arrival.isoformat()})"
        else:
            root_cause = "재고 부족으로 대기 중 (추가 발주 필요)"

        return {
            "status": FulfillmentStatus.PENDING,
            "stock_deducted_date": None,
            "shipped_date": None,
            "expected_arrival_date": estimated_arrival,
            "delay_days": max((reference_date - order.order_date).days, 0),
            "root_cause": root_cause,
            "is_cancellable": True,
        }

    is_cancellable = fulfillment.shipped_date is None or fulfillment.shipped_date > reference_date

    return {
        "status": fulfillment.status,
        "stock_deducted_date": fulfillment.stock_deducted_date,
        "shipped_date": fulfillment.shipped_date,
        "expected_arrival_date": fulfillment.expected_arrival_date,
        "delay_days": fulfillment.delay_days,
        "root_cause": fulfillment.root_cause,
        "is_cancellable": is_cancellable,
    }


def get_ledger_event_text(row: DailyLedger, production_orders_by_date: dict[date, list[ProductionOrder]]) -> str:
    """원장(E-3) 한 행에 대한 "이벤트" 설명 문자열.

    예: "생산입고 +20; 발주 20개 (가용재고 10 ≤ 재주문점 12)"
    """

    events: list[str] = []
    if row.production_inbound > 0:
        events.append(f"생산입고 +{row.production_inbound}")
    for po in production_orders_by_date.get(row.date, []):
        events.append(f"발주 {po.quantity}개 ({po.trigger_reason})")
    if row.backorder_balance > 0:
        events.append(f"백오더 {row.backorder_balance}개 대기")
    return "; ".join(events)
