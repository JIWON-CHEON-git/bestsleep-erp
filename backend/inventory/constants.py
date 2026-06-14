"""시뮬레이션 전반에서 사용하는 상수와 선택지(choices) 정의.

매직 넘버/매직 스트링을 코드 곳곳에 흩어 두지 않기 위해 한 곳에 모은다.
"""

from __future__ import annotations


class ProductCategory:
    """제품 카테고리."""

    MATTRESS = "매트리스"
    TOPPER = "토퍼"
    FRAME = "프레임"
    PILLOW = "베개"

    CHOICES = [
        (MATTRESS, "매트리스"),
        (TOPPER, "토퍼"),
        (FRAME, "프레임"),
        (PILLOW, "베개"),
    ]


class ProductSize:
    """제품 사이즈."""

    SS = "SS"
    Q = "Q"
    K = "K"
    STD = "STD"

    CHOICES = [
        (SS, "SS"),
        (Q, "Q"),
        (K, "K"),
        (STD, "STD"),
    ]


class OrderStatus:
    """Order.status — 주문 자체의 생애주기 상태(취소 여부)."""

    ACTIVE = "active"
    CANCELLED = "cancelled"

    CHOICES = [
        (ACTIVE, "활성"),
        (CANCELLED, "취소"),
    ]


class ProductionOrderStatus:
    """ProductionOrder.status — 생산발주 입고 여부."""

    PENDING = "pending"
    RECEIVED = "received"

    CHOICES = [
        (PENDING, "입고 예정"),
        (RECEIVED, "입고 완료"),
    ]


class FulfillmentStatus:
    """OrderFulfillment.status — 고객 주문의 배송 결과 분류.

    - pending: 아직 재고 차감/출고가 이뤄지지 않음 (백오더 대기 포함)
    - normal: 희망배송일이 없고, 주문 당일 바로 출고됨
    - simple_delay: 희망배송일이 없고, 재고 부족으로 출고가 늦어짐
    - promise_kept: 희망배송일이 있고, 그 약속(목표 출고일)을 지킴
    - promise_broken: 희망배송일이 있고, 재고 부족으로 약속을 못 지킴
    - cancelled: 주문이 취소됨 (OrderFulfillment에는 저장되지 않는, API 표시용 값)
    """

    PENDING = "pending"
    NORMAL = "normal"
    SIMPLE_DELAY = "simple_delay"
    PROMISE_KEPT = "promise_kept"
    PROMISE_BROKEN = "promise_broken"
    CANCELLED = "cancelled"

    CHOICES = [
        (PENDING, "대기(백오더)"),
        (NORMAL, "정상"),
        (SIMPLE_DELAY, "단순 지연"),
        (PROMISE_KEPT, "약속 이행"),
        (PROMISE_BROKEN, "약속 불이행"),
    ]


class ProductStatus:
    """제품 목록 화면(G-1)에서 사용하는 재고 상태 분류 (계산값, DB에 저장하지 않음)."""

    NORMAL = "normal"
    WARNING = "warning"
    BELOW_REORDER = "below_reorder"
    SHORTAGE = "shortage"


# 제품 상태 "warning(임박)" 판정 배수.
# 재주문점의 WARNING_BUFFER_RATIO배 이하로 현재고가 내려오면, 아직 재주문점에
# 도달하지 않았더라도 "곧 발주가 발생할 수 있는 제품"으로 미리 보여준다.
# 예: 재주문점 12 → 12 * 1.2 = 14.4 → 현재고 14 이하면 warning.
WARNING_BUFFER_RATIO = 1.2
