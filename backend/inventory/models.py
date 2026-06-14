"""재고흐름 ERP 도메인 모델.

전체 흐름: 주문(Order)이 재고를 줄이고, 재고가 재주문점 이하로 떨어지면
생산발주(ProductionOrder)가 발생하고, 생산리드타임 이후 입고되어 재고가
다시 채워진다. 매일의 재고 변화는 DailyLedger에 기록되고, 각 주문의
출고/배송 결과는 OrderFulfillment에 기록된다.
"""

from __future__ import annotations

from django.db import models

from inventory.constants import (
    FulfillmentStatus,
    OrderStatus,
    ProductCategory,
    ProductionOrderStatus,
    ProductSize,
)


class SimulationConfig(models.Model):
    """시뮬레이션 전역 설정 (시작일/종료일).

    엑셀 '파라미터' 시트에서 로드되는 단일 레코드(싱글톤)로 사용한다.
    """

    start_date = models.DateField(help_text="시뮬레이션 시작일")
    end_date = models.DateField(help_text="시뮬레이션 종료일 (필요 시 자동 연장됨)")

    def __str__(self) -> str:
        return f"SimulationConfig({self.start_date} ~ {self.end_date})"


class Product(models.Model):
    """제품마스터.

    SKU를 PK로 사용한다 (엑셀/주문 데이터가 SKU 기준으로 식별되기 때문).
    """

    sku = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=ProductCategory.CHOICES)
    size = models.CharField(max_length=10, choices=ProductSize.CHOICES)
    unit_price = models.IntegerField(help_text="단가 (표시용)")

    initial_stock = models.IntegerField(help_text="시뮬레이션 시작일의 초기 재고")
    safety_stock = models.IntegerField(help_text="안전재고")
    reorder_point = models.IntegerField(help_text="재주문점: 가용재고가 이 값 이하이면 발주")
    moq = models.IntegerField(help_text="생산 로트(최소 발주 단위)")
    production_lead_time_days = models.IntegerField(help_text="생산 리드타임(일)")
    delivery_lead_time_days = models.IntegerField(help_text="배송 리드타임(일)")

    class Meta:
        ordering = ["sku"]

    def __str__(self) -> str:
        return f"{self.sku} ({self.name} {self.size})"


class Order(models.Model):
    """고객 주문."""

    order_no = models.CharField(max_length=32, primary_key=True)
    order_date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    quantity = models.IntegerField()
    customer_name = models.CharField(max_length=50)
    desired_delivery_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=10, choices=OrderStatus.CHOICES, default=OrderStatus.ACTIVE
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order_date", "order_no"]

    def __str__(self) -> str:
        return self.order_no


class ProductionOrder(models.Model):
    """생산발주.

    재고가 재주문점 이하로 떨어졌을 때 시스템이 자동으로 생성한다.
    quantity는 항상 제품의 MOQ(생산 로트) 단위이다.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="production_orders"
    )
    order_date = models.DateField(help_text="발주일")
    quantity = models.IntegerField(help_text="발주수량 (MOQ 1회분)")
    expected_arrival_date = models.DateField(help_text="입고예정일 = 발주일 + 생산리드타임")

    status = models.CharField(
        max_length=10,
        choices=ProductionOrderStatus.CHOICES,
        default=ProductionOrderStatus.PENDING,
    )
    received_date = models.DateField(null=True, blank=True)

    trigger_reason = models.TextField(
        help_text='발주 트리거 사유. 예: "ORD-0007 처리 후 가용재고 2개 → 재주문점(12) 이하"'
    )

    class Meta:
        ordering = ["expected_arrival_date", "id"]

    def __str__(self) -> str:
        return f"PO#{self.id} {self.product_id} x{self.quantity} -> {self.expected_arrival_date}"


class DailyLedger(models.Model):
    """제품별 일자별 재고 원장.

    시뮬레이션이 하루씩 진행되며 제품마다 한 행씩 생성한다.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ledger_rows")
    date = models.DateField()

    opening_stock = models.IntegerField(help_text="기초재고 (전일 기말재고)")
    production_inbound = models.IntegerField(default=0, help_text="당일 생산입고(+)")
    order_outbound = models.IntegerField(default=0, help_text="당일 주문출고(-), 재고 차감 기준")
    closing_stock = models.IntegerField(help_text="기말재고")

    available_stock = models.IntegerField(
        help_text="가용재고 = 기말재고 + 미입고발주합 - 백오더잔량 (음수 허용)"
    )
    order_quantity_today = models.IntegerField(
        default=0, help_text="당일 발생한 생산발주 수량 합"
    )
    backorder_balance = models.IntegerField(
        default=0, help_text="당일 마감 시점의 백오더(미출고 주문) 잔량"
    )
    structural_shortage_flag = models.BooleanField(
        default=False, help_text="가용재고가 음수이면 True (구조적 재고 부족)"
    )

    class Meta:
        ordering = ["product", "date"]
        constraints = [
            models.UniqueConstraint(fields=["product", "date"], name="unique_ledger_per_day"),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} {self.date}: closing={self.closing_stock}"


class OrderFulfillment(models.Model):
    """주문 처리/배송 결과.

    Order와 1:1 관계. 시뮬레이션이 진행되며 채워진다.
    """

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="fulfillment", primary_key=True
    )

    stock_deducted_date = models.DateField(
        null=True, blank=True, help_text="재고가 실제로 차감된 날 (NULL이면 백오더 대기)"
    )
    shipped_date = models.DateField(null=True, blank=True, help_text="배송 출발일(출고일)")
    expected_arrival_date = models.DateField(
        null=True, blank=True, help_text="고객 도착예정일 = 출고일 + 배송리드타임"
    )

    status = models.CharField(
        max_length=20,
        choices=FulfillmentStatus.CHOICES,
        default=FulfillmentStatus.PENDING,
    )
    delay_days = models.IntegerField(default=0)
    root_cause = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"Fulfillment({self.order_id}: {self.status})"
