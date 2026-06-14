from django.contrib import admin

from inventory.models import (
    DailyLedger,
    Order,
    OrderFulfillment,
    Product,
    ProductionOrder,
    SimulationConfig,
)

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(ProductionOrder)
admin.site.register(DailyLedger)
admin.site.register(OrderFulfillment)
admin.site.register(SimulationConfig)
