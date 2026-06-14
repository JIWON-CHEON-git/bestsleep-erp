"""inventory 앱의 API 라우팅 (E-1 ~ E-7)."""

from __future__ import annotations

from django.urls import path

from inventory import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("products/", views.product_list, name="product-list"),
    path("products/<str:sku>/ledger/", views.product_ledger, name="product-ledger"),
    path("production-orders/", views.production_order_list, name="production-order-list"),
    path("orders/", views.order_list, name="order-list"),
    path("orders/<str:order_no>/cancel/", views.order_cancel, name="order-cancel"),
    path("simulation/run/", views.simulation_run, name="simulation-run"),
]
