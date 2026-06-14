"""백오더 상태 주문의 "예상 출고일" 추정 (D-5).

운영자가 "이 주문 언제 나가요?"라고 물었을 때, 시뮬레이션을 다시 돌리지 않고도
현재 DB 상태(가장 최근 DailyLedger + 입고예정 ProductionOrder + 백오더 큐)만으로
빠르게 답하기 위한 함수.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from inventory.constants import OrderStatus
from inventory.models import DailyLedger, OrderFulfillment, ProductionOrder, Product


def estimate_fulfillment_date(
    product: Product,
    order_quantity: int,
    as_of_date: date,
    exclude_order_no: Optional[str] = None,
) -> Optional[date]:
    """이 제품에서 ``order_quantity``를 출고할 수 있게 되는 첫 날짜를 추정한다.

    절차:
        1. ``as_of_date`` 기준 가장 최근 DailyLedger.closing_stock을 "현재고"로 본다
           (없으면 제품의 초기재고).
        2. ``as_of_date`` 시점에 아직 재고가 차감되지 않은 백오더 큐
           (``stock_deducted_date IS NULL OR stock_deducted_date > as_of_date``인
           활성 주문, FIFO 순서) 중 ``exclude_order_no`` 이전 순서의 주문 수량을
           현재고에서 먼저 뺀다. (= 이 주문보다 먼저 처리되어야 하는 물량)
        3. 남은 재고로 ``order_quantity``를 못 채우면, ``as_of_date`` 시점에
           아직 입고되지 않은 ProductionOrder(``expected_arrival_date >
           as_of_date``)를 입고예정일 순으로 누적해 충족되는 첫 입고일을 반환한다.
        4. 어떤 입고로도 충족되지 않으면 None (= 추가 발주가 필요한 상태).

    주의: ``run_simulation()``은 전체 미래를 한 번에 계산하므로, DB의
    ``ProductionOrder.status``는 거의 항상 "received"이고
    ``OrderFulfillment.stock_deducted_date``도 거의 항상 채워져 있다(미래
    날짜라도). 따라서 "아직 처리되지 않음"은 DB의 status 필드가 아니라
    ``as_of_date``와의 날짜 비교로 판정한다.

    Args:
        product: 대상 제품.
        order_quantity: 충족해야 할 수량 (보통 백오더 상태 주문의 quantity).
        as_of_date: 기준일.
        exclude_order_no: 이 주문번호 "앞에 있는" 백오더만 선순위로 카운트한다.
            None이면 현재 백오더 큐 전체를 선순위로 간주한다(보수적 추정).

    Returns:
        충족 가능한 첫 날짜, 또는 None(추가 발주 필요).
    """

    ledger = (
        DailyLedger.objects.filter(product=product, date__lte=as_of_date)
        .order_by("-date")
        .first()
    )
    current_stock = ledger.closing_stock if ledger is not None else product.initial_stock

    backorders = (
        OrderFulfillment.objects.filter(
            order__product=product,
            order__status=OrderStatus.ACTIVE,
        )
        .select_related("order")
        .order_by("order__order_date", "order__order_no")
    )

    ahead_quantity = 0
    for fulfillment in backorders:
        if fulfillment.stock_deducted_date is not None and fulfillment.stock_deducted_date <= as_of_date:
            continue  # as_of_date 시점에 이미 재고 차감됨 -> 더 이상 "대기 중"이 아님
        if fulfillment.order_id == exclude_order_no:
            break
        ahead_quantity += fulfillment.order.quantity

    available_now = max(current_stock - ahead_quantity, 0)
    remaining = order_quantity - available_now
    if remaining <= 0:
        return as_of_date

    cumulative = 0
    pending_pos = ProductionOrder.objects.filter(
        product=product, expected_arrival_date__gt=as_of_date
    ).order_by("expected_arrival_date", "id")

    for po in pending_pos:
        cumulative += po.quantity
        if cumulative >= remaining:
            return po.expected_arrival_date

    return None
