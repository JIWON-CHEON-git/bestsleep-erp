"""재고흐름 시뮬레이션을 실행하고 결과를 DB에 반영한다.

사용법:
    python manage.py run_simulation
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from inventory.simulation import run_simulation


class Command(BaseCommand):
    help = "전체 제품에 대해 재고흐름 시뮬레이션을 실행하고 DailyLedger/ProductionOrder/OrderFulfillment를 갱신합니다."

    def handle(self, *args, **options) -> None:
        results = run_simulation()

        total_ledger_rows = sum(len(r.ledger) for r in results.values())
        total_pos = sum(len(r.production_orders) for r in results.values())
        total_orders = sum(len(r.orders) for r in results.values())

        self.stdout.write(
            self.style.SUCCESS(
                f"시뮬레이션 완료: 제품 {len(results)}개, "
                f"원장 {total_ledger_rows}행, 생산발주 {total_pos}건, "
                f"처리된 주문 {total_orders}건"
            )
        )
