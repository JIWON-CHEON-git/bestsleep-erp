"""REST API(E단계) 응답 형태를 정의하는 시리얼라이저.

대부분의 필드는 ``reference_date``(기준일)에 의존하는 계산값이라
DB 컬럼을 그대로 노출하지 않고, ``inventory.selectors``의 함수를
호출해 채운다. 기준일은 ``context["reference_date"]``로 전달한다.
"""

from __future__ import annotations

from rest_framework import serializers

from inventory import selectors
from inventory.models import DailyLedger, Order, Product, ProductionOrder


class ProductSerializer(serializers.Serializer):
    """제품 목록(E-2) 한 행."""

    sku = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    size = serializers.CharField()
    safety_stock = serializers.IntegerField()
    reorder_point = serializers.IntegerField()
    current_stock = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    incoming_quantity = serializers.SerializerMethodField()
    backorder_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def _stocks(self, product: Product) -> tuple[int, int]:
        reference_date = self.context["reference_date"]
        return selectors.get_current_and_available_stock(product, reference_date)

    def get_current_stock(self, product: Product) -> int:
        return self._stocks(product)[0]

    def get_available_stock(self, product: Product) -> int:
        return self._stocks(product)[1]

    def get_incoming_quantity(self, product: Product) -> int:
        return selectors.get_incoming_quantity(product, self.context["reference_date"])

    def get_backorder_count(self, product: Product) -> int:
        return selectors.get_backorder_count(product, self.context["reference_date"])

    def get_status(self, product: Product) -> str:
        current_stock, available_stock = self._stocks(product)
        return selectors.get_product_status(current_stock, available_stock, product)


class DailyLedgerSerializer(serializers.Serializer):
    """제품별 일별 원장(E-3) 한 행."""

    date = serializers.DateField()
    opening_stock = serializers.IntegerField()
    production_inbound = serializers.IntegerField()
    order_outbound = serializers.IntegerField()
    closing_stock = serializers.IntegerField()
    available_stock = serializers.IntegerField()
    order_quantity_today = serializers.IntegerField()
    backorder_balance = serializers.IntegerField()
    structural_shortage_flag = serializers.BooleanField()
    events = serializers.SerializerMethodField()

    def get_events(self, row: DailyLedger) -> str:
        production_orders_by_date = self.context["production_orders_by_date"]
        return selectors.get_ledger_event_text(row, production_orders_by_date)


class ProductionOrderSerializer(serializers.Serializer):
    """생산발주 목록(E-4) 한 행."""

    id = serializers.IntegerField()
    sku = serializers.CharField(source="product_id")
    product_name = serializers.CharField(source="product.name")
    order_date = serializers.DateField()
    quantity = serializers.IntegerField()
    expected_arrival_date = serializers.DateField()
    received_date = serializers.DateField(allow_null=True)
    trigger_reason = serializers.CharField()
    status = serializers.SerializerMethodField()

    def get_status(self, po: ProductionOrder) -> str:
        return selectors.get_production_order_display_status(po, self.context["reference_date"])


class OrderSerializer(serializers.Serializer):
    """주문 목록(E-5) 한 행."""

    order_no = serializers.CharField()
    order_date = serializers.DateField()
    sku = serializers.CharField(source="product_id")
    product_name = serializers.CharField(source="product.name")
    quantity = serializers.IntegerField()
    customer_name = serializers.CharField()
    desired_delivery_date = serializers.DateField(allow_null=True)
    status = serializers.SerializerMethodField()
    stock_deducted_date = serializers.SerializerMethodField()
    shipped_date = serializers.SerializerMethodField()
    expected_arrival_date = serializers.SerializerMethodField()
    delay_days = serializers.SerializerMethodField()
    root_cause = serializers.SerializerMethodField()
    is_cancellable = serializers.SerializerMethodField()

    def _view(self, order: Order) -> dict:
        cache = self.context.setdefault("_order_view_cache", {})
        if order.order_no not in cache:
            cache[order.order_no] = selectors.get_order_view(order, self.context["reference_date"])
        return cache[order.order_no]

    def get_status(self, order: Order) -> str:
        return self._view(order)["status"]

    def get_stock_deducted_date(self, order: Order):
        return self._view(order)["stock_deducted_date"]

    def get_shipped_date(self, order: Order):
        return self._view(order)["shipped_date"]

    def get_expected_arrival_date(self, order: Order):
        return self._view(order)["expected_arrival_date"]

    def get_delay_days(self, order: Order) -> int:
        return self._view(order)["delay_days"]

    def get_root_cause(self, order: Order) -> str:
        return self._view(order)["root_cause"]

    def get_is_cancellable(self, order: Order) -> bool:
        return self._view(order)["is_cancellable"]
