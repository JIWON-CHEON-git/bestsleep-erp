"""시뮬레이션 엔진 핵심 동작 검증 (과제 H 섹션 H-1 ~ H-6).

순수 로직(ProductSpec/OrderState/simulate_product 등)은 DB 없이 테스트하고,
취소(H-6)처럼 DB 상태가 필요한 경우에만 ``@pytest.mark.django_db``를 사용한다.
"""

from __future__ import annotations

from datetime import date

import pytest

from inventory.constants import FulfillmentStatus, OrderStatus
from inventory.models import Order, OrderFulfillment, Product, ProductionOrder, SimulationConfig
from inventory.simulation import (
    OrderState,
    ProductSimState,
    ProductSpec,
    cancel_order,
    process_backorders,
    process_new_orders,
    run_simulation,
    simulate_product,
)

# 과제 명세의 BS-MAT-Q-002 스펙 (초기재고 15 / 안전재고 8 / 재주문점 12 /
# MOQ 20 / 생산LT 5일 / 배송LT 2일)
MAT_Q002 = ProductSpec(
    sku="BS-MAT-Q-002",
    reorder_point=12,
    moq=20,
    production_lead_time_days=5,
    delivery_lead_time_days=2,
    initial_stock=15,
)


# ----------------------------------------------------------------------
# H-1. 기본 케이스: 06-01 마감 재고 / 자동 발주 발생 / 입고예정일
# ----------------------------------------------------------------------


def test_h1_closing_stock_and_reorder_trigger():
    order = OrderState(
        order_no="ORD-0001",
        order_date=date(2026, 6, 1),
        quantity=5,
        desired_delivery_date=date(2026, 6, 5),
    )

    result = simulate_product(MAT_Q002, [order], date(2026, 6, 1), date(2026, 6, 1))
    row = result.ledger[0]

    # 06-01 마감 기말재고 = 15 - 5 = 10
    assert row.closing_stock == 10

    # 가용재고(10) <= 재주문점(12) -> 발주 1건(20개) 발생
    assert row.order_quantity_today == 20
    assert len(result.production_orders) == 1

    po = result.production_orders[0]
    assert po.quantity == 20
    # 입고예정일 = 발주일(06-01) + 생산리드타임(5일) = 06-06
    assert po.expected_arrival_date == date(2026, 6, 6)
    assert "ORD-0001 처리 후 가용재고 10개 → 재주문점(12) 이하" in po.trigger_reason


# ----------------------------------------------------------------------
# H-2. 부분출고 금지
# ----------------------------------------------------------------------


def test_h2_no_partial_shipment():
    state = ProductSimState(stock=6)
    order = OrderState(order_no="ORD-X", order_date=date(2026, 6, 1), quantity=8)

    shipped = process_new_orders(state, date(2026, 6, 1), [order])

    assert shipped == []
    assert state.stock == 6  # 재고 변화 없음
    assert state.backorder_queue == [order]
    assert order.stock_deducted_date is None


# ----------------------------------------------------------------------
# H-3. 희망배송일 보관 로직 (재고 차감일 != 배송 출발일)
# ----------------------------------------------------------------------


def test_h3_desired_delivery_date_warehousing():
    order = OrderState(
        order_no="ORD-0001",
        order_date=date(2026, 6, 1),
        quantity=5,
        desired_delivery_date=date(2026, 6, 5),
    )

    result = simulate_product(MAT_Q002, [order], date(2026, 6, 1), date(2026, 6, 3))
    fulfilled = result.orders["ORD-0001"]

    # 재고는 주문일(06-01)에 바로 차감되지만,
    assert fulfilled.stock_deducted_date == date(2026, 6, 1)
    # 트럭은 목표 출발일(희망배송일 06-05 - 배송LT 2일 = 06-03)에 출발
    assert fulfilled.shipped_date == date(2026, 6, 3)
    assert fulfilled.expected_arrival_date == date(2026, 6, 5)
    assert fulfilled.status == FulfillmentStatus.PROMISE_KEPT
    assert fulfilled.delay_days == 0


# ----------------------------------------------------------------------
# H-4. FIFO 백오더 처리
# ----------------------------------------------------------------------


def test_h4_fifo_ships_front_of_queue_first():
    o1 = OrderState(order_no="ORD-A", order_date=date(2026, 6, 1), quantity=5)
    o2 = OrderState(order_no="ORD-B", order_date=date(2026, 6, 1), quantity=2)
    state = ProductSimState(stock=6, backorder_queue=[o1, o2])

    shipped = process_backorders(state, date(2026, 6, 2))

    # 앞선 주문(ORD-A, 5개)이 먼저 출고되고, 남은 재고(1)로는 ORD-B(2개)를 못 채워 대기
    assert shipped == [o1]
    assert state.stock == 1
    assert state.backorder_queue == [o2]
    assert o1.stock_deducted_date == date(2026, 6, 2)
    assert o2.stock_deducted_date is None


def test_h4_fifo_does_not_skip_ahead_in_queue():
    o1 = OrderState(order_no="ORD-A", order_date=date(2026, 6, 1), quantity=5)
    o2 = OrderState(order_no="ORD-B", order_date=date(2026, 6, 1), quantity=1)
    state = ProductSimState(stock=3, backorder_queue=[o1, o2])

    shipped = process_backorders(state, date(2026, 6, 2))

    # ORD-A(5개)를 재고 3개로 채울 수 없으면, ORD-B(1개)는 채울 수 있어도 건너뛰지 않고 대기
    assert shipped == []
    assert state.stock == 3
    assert state.backorder_queue == [o1, o2]


# ----------------------------------------------------------------------
# H-5. 연속 발주 (구조적 재고 부족)
# ----------------------------------------------------------------------


def test_h5_consecutive_orders_for_structural_shortage():
    spec = ProductSpec(
        sku="TEST-SKU",
        reorder_point=5,
        moq=10,
        production_lead_time_days=3,
        delivery_lead_time_days=1,
        initial_stock=5,
    )
    # 재고(5)보다 훨씬 큰 주문 -> 백오더 40, 가용재고 = 5 + 0 - 40 = -35
    order = OrderState(order_no="ORD-BIG", order_date=date(2026, 6, 1), quantity=40)

    result = simulate_product(spec, [order], date(2026, 6, 1), date(2026, 6, 1))
    row = result.ledger[0]

    assert row.closing_stock == 5  # 부분출고 없음 -> 재고 그대로
    assert row.backorder_balance == 40
    assert row.structural_shortage_flag is True  # 발주 전 가용재고(-35) < 0

    # -35 -> +10 -> -25 -> +10 -> -15 -> +10 -> -5 -> +10 -> 5(<=5, 한 번 더) -> +10 -> 15(>5, 종료)
    # 총 5건 x 10개 = 50개 발주, 최종 가용재고 = -35 + 50 = 15
    assert len(result.production_orders) == 5
    assert all(po.quantity == 10 for po in result.production_orders)
    assert row.order_quantity_today == 50
    assert row.available_stock == 15


# ----------------------------------------------------------------------
# H-6. 주문 취소
# ----------------------------------------------------------------------


@pytest.mark.django_db
def test_h6_cancel_backordered_order_removes_from_queue():
    product = Product.objects.create(
        sku="TST-BACKORDER",
        name="테스트 제품",
        category="매트리스",
        size="Q",
        unit_price=100000,
        initial_stock=3,
        safety_stock=1,
        reorder_point=0,
        moq=10,
        production_lead_time_days=5,
        delivery_lead_time_days=2,
    )
    SimulationConfig.objects.create(start_date=date(2026, 6, 1), end_date=date(2026, 6, 5))
    order = Order.objects.create(
        order_no="ORD-T1",
        order_date=date(2026, 6, 1),
        product=product,
        quantity=5,
        customer_name="테스트",
    )
    # 아직 출고 전(백오더 대기) 상태를 직접 표현 — run_simulation으로 끝까지 돌리면
    # 자동발주가 누적되어 결국 기간 내 출고되므로(엔진 설계상 항상 해소됨),
    # cancel_order의 "출고 전(shipped_date IS NULL)" 분기 자체를 단위테스트한다.
    OrderFulfillment.objects.create(order=order, status=FulfillmentStatus.PENDING)

    cancel_order(order)

    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
    assert order.cancelled_at is not None
    # 취소 후 재시뮬레이션 결과에서 이 주문은 더 이상 존재하지 않음 (백오더 큐에서 제거됨)
    assert not OrderFulfillment.objects.filter(order_id="ORD-T1").exists()


@pytest.mark.django_db
def test_h6_cancel_shipped_order_raises_error():
    product = Product.objects.create(
        sku="TST-SHIPPED",
        name="테스트 제품2",
        category="매트리스",
        size="Q",
        unit_price=100000,
        initial_stock=10,
        safety_stock=1,
        reorder_point=0,
        moq=10,
        production_lead_time_days=5,
        delivery_lead_time_days=2,
    )
    SimulationConfig.objects.create(start_date=date(2026, 6, 1), end_date=date(2026, 6, 5))
    order = Order.objects.create(
        order_no="ORD-T2",
        order_date=date(2026, 6, 1),
        product=product,
        quantity=5,
        customer_name="테스트2",
    )

    run_simulation()

    fulfillment = OrderFulfillment.objects.get(order_id="ORD-T2")
    assert fulfillment.status == FulfillmentStatus.NORMAL
    assert fulfillment.shipped_date == date(2026, 6, 1)

    with pytest.raises(ValueError):
        cancel_order(order)

    order.refresh_from_db()
    assert order.status == OrderStatus.ACTIVE  # 변경되지 않음


# ----------------------------------------------------------------------
# 통합: 실제 시드 데이터로 run_simulation 핵심 수치 확인
# ----------------------------------------------------------------------


@pytest.mark.django_db
def test_full_simulation_with_seed_data_key_numbers():
    """엑셀 시드 데이터를 그대로 사용해 핵심 검증 수치 3가지를 확인한다."""

    from inventory.management.commands.seed_data import Command as SeedCommand

    SeedCommand().handle(excel=None)  # fallback 하드코딩 데이터 사용 (엑셀과 동일한 값)
    run_simulation()

    from inventory.models import DailyLedger

    ledger = DailyLedger.objects.get(product_id="BS-MAT-Q-002", date=date(2026, 6, 1))
    assert ledger.opening_stock == 15
    assert ledger.order_outbound == 5
    assert ledger.closing_stock == 10

    po = ProductionOrder.objects.filter(
        product_id="BS-MAT-Q-002", order_date=date(2026, 6, 1)
    ).first()
    assert po is not None
    assert po.quantity == 20
    assert po.expected_arrival_date == date(2026, 6, 6)

    fulfillment = OrderFulfillment.objects.get(order_id="ORD-0001")
    assert fulfillment.status == FulfillmentStatus.PROMISE_KEPT
    assert fulfillment.shipped_date == date(2026, 6, 3)
