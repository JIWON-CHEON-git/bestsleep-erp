"""REST API 뷰 (E단계: E-1 ~ E-7).

전부 함수 기반 뷰(``@api_view``)로 작성한다. 각 엔드포인트의 응답 형태가
서로 많이 달라 ViewSet으로 묶을 이점이 적고, 단순한 조회/액션 위주이기
때문이다.
"""

from __future__ import annotations

from datetime import date

from rest_framework.decorators import api_view
from rest_framework.response import Response

from inventory import selectors
from inventory.constants import FulfillmentStatus, OrderStatus
from inventory.models import DailyLedger, Order, Product, ProductionOrder
from inventory.serializers import (
    DailyLedgerSerializer,
    OrderSerializer,
    ProductionOrderSerializer,
    ProductSerializer,
)
from inventory.simulation import cancel_order, run_simulation


# ----------------------------------------------------------------------
# E-1. 대시보드
# ----------------------------------------------------------------------


@api_view(["GET"])
def dashboard(request):
    """GET /api/dashboard/?reference_date=YYYY-MM-DD

    기준일 시점의 전체 현황 요약.
    """

    reference_date = selectors.parse_reference_date(request.query_params.get("reference_date"))

    products_below_reorder = 0
    products_in_shortage = 0
    structural_shortage_products: list[str] = []

    for product in Product.objects.all():
        current_stock, available_stock = selectors.get_current_and_available_stock(
            product, reference_date
        )
        if current_stock <= product.reorder_point:
            products_below_reorder += 1
        if available_stock < 0:
            products_in_shortage += 1

        row = selectors.get_ledger_row(product, reference_date)
        if row is not None and row.structural_shortage_flag:
            structural_shortage_products.append(product.sku)

    active_production_orders = ProductionOrder.objects.filter(
        order_date__lte=reference_date, expected_arrival_date__gt=reference_date
    ).count()

    delayed_orders = 0
    broken_promise_orders = 0
    orders = Order.objects.filter(
        status=OrderStatus.ACTIVE, order_date__lte=reference_date
    ).select_related("fulfillment")
    for order in orders:
        fulfillment = getattr(order, "fulfillment", None)
        if fulfillment is None:
            continue
        if not selectors.is_order_pending_as_of(fulfillment, reference_date):
            continue
        if order.desired_delivery_date is None:
            delayed_orders += 1
        elif fulfillment.status == FulfillmentStatus.PROMISE_BROKEN:
            broken_promise_orders += 1

    return Response(
        {
            "reference_date": reference_date,
            "products_below_reorder": products_below_reorder,
            "products_in_shortage": products_in_shortage,
            "active_production_orders": active_production_orders,
            "delayed_orders": delayed_orders,
            "broken_promise_orders": broken_promise_orders,
            "structural_shortage_products": structural_shortage_products,
        }
    )


# ----------------------------------------------------------------------
# E-2. 제품 목록
# ----------------------------------------------------------------------


@api_view(["GET"])
def product_list(request):
    """GET /api/products/?reference_date=YYYY-MM-DD"""

    reference_date = selectors.parse_reference_date(request.query_params.get("reference_date"))
    products = Product.objects.all()
    serializer = ProductSerializer(
        products, many=True, context={"reference_date": reference_date}
    )
    return Response(serializer.data)


# ----------------------------------------------------------------------
# E-3. 제품별 원장
# ----------------------------------------------------------------------


@api_view(["GET"])
def product_ledger(request, sku: str):
    """GET /api/products/<sku>/ledger/?start=YYYY-MM-DD&end=YYYY-MM-DD

    start/end가 없으면 시뮬레이션 전체 기간을 반환한다.
    """

    try:
        product = Product.objects.get(pk=sku)
    except Product.DoesNotExist:
        return Response({"detail": "제품을 찾을 수 없습니다."}, status=404)

    rows = DailyLedger.objects.filter(product=product).order_by("date")

    start = request.query_params.get("start")
    end = request.query_params.get("end")
    if start:
        rows = rows.filter(date__gte=date.fromisoformat(start))
    if end:
        rows = rows.filter(date__lte=date.fromisoformat(end))

    rows = list(rows)

    production_orders_by_date: dict[date, list[ProductionOrder]] = {}
    for po in ProductionOrder.objects.filter(product=product):
        production_orders_by_date.setdefault(po.order_date, []).append(po)

    serializer = DailyLedgerSerializer(
        rows, many=True, context={"production_orders_by_date": production_orders_by_date}
    )
    return Response(serializer.data)


# ----------------------------------------------------------------------
# E-4. 생산발주 목록
# ----------------------------------------------------------------------


@api_view(["GET"])
def production_order_list(request):
    """GET /api/production-orders/?reference_date=&status=&sku=

    status는 기준일 시점으로 재계산된 값(pending/received)으로 필터링한다.
    """

    reference_date = selectors.parse_reference_date(request.query_params.get("reference_date"))
    queryset = ProductionOrder.objects.select_related("product").order_by(
        "expected_arrival_date", "id"
    ).filter(order_date__lte=reference_date)

    sku = request.query_params.get("sku")
    if sku:
        queryset = queryset.filter(product_id=sku)

    pos = list(queryset)

    status_filter = request.query_params.get("status")
    if status_filter:
        pos = [
            po
            for po in pos
            if selectors.get_production_order_display_status(po, reference_date) == status_filter
        ]

    serializer = ProductionOrderSerializer(
        pos, many=True, context={"reference_date": reference_date}
    )
    return Response(serializer.data)


# ----------------------------------------------------------------------
# E-5. 주문 목록
# ----------------------------------------------------------------------


@api_view(["GET"])
def order_list(request):
    """GET /api/orders/?reference_date=&status=&sku=&customer_name="""

    reference_date = selectors.parse_reference_date(request.query_params.get("reference_date"))
    queryset = Order.objects.select_related("product", "fulfillment").order_by(
        "order_date", "order_no"
    ).filter(order_date__lte=reference_date)

    sku = request.query_params.get("sku")
    if sku:
        queryset = queryset.filter(product_id=sku)

    customer_name = request.query_params.get("customer_name")
    if customer_name:
        queryset = queryset.filter(customer_name__icontains=customer_name)

    orders = list(queryset)

    status_filter = request.query_params.get("status")
    if status_filter:
        orders = [
            order
            for order in orders
            if selectors.get_order_view(order, reference_date)["status"] == status_filter
        ]

    serializer = OrderSerializer(orders, many=True, context={"reference_date": reference_date})
    return Response(serializer.data)


# ----------------------------------------------------------------------
# E-6. 주문 취소
# ----------------------------------------------------------------------


@api_view(["POST"])
def order_cancel(request, order_no: str):
    """POST /api/orders/<order_no>/cancel/

    body(선택): {"reference_date": "YYYY-MM-DD"} (없으면 시뮬레이션 시작일)

    is_cancellable 판정은 E-5와 동일한 기준(shipped_date IS NULL OR
    shipped_date > reference_date)을 사용한다.
    """

    reference_date = selectors.parse_reference_date(request.data.get("reference_date"))

    try:
        order = Order.objects.select_related("fulfillment").get(pk=order_no)
    except Order.DoesNotExist:
        return Response({"detail": "주문을 찾을 수 없습니다."}, status=404)

    if order.status == OrderStatus.CANCELLED:
        return Response({"detail": "이미 취소된 주문입니다."}, status=400)

    try:
        cancel_order(order, as_of_date=reference_date)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)

    return Response({"order_no": order_no, "status": OrderStatus.CANCELLED})


# ----------------------------------------------------------------------
# E-7. 시뮬레이션 재실행
# ----------------------------------------------------------------------


@api_view(["POST"])
def simulation_run(request):
    """POST /api/simulation/run/"""

    results = run_simulation()

    total_ledger_rows = sum(len(r.ledger) for r in results.values())
    total_production_orders = sum(len(r.production_orders) for r in results.values())
    total_orders = sum(len(r.orders) for r in results.values())

    return Response(
        {
            "products": len(results),
            "ledger_rows": total_ledger_rows,
            "production_orders": total_production_orders,
            "orders": total_orders,
        }
    )
