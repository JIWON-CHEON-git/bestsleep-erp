"""현재 제품/주문/시뮬레이션 설정을 fixtures/initial_data.json으로 내보낸다.

엑셀 의존성을 줄이기 위한 보조 명령어. seed_data로 적재한 뒤 한 번 실행해두면,
이후에는 엑셀 없이도 다음으로 시드할 수 있다:

    python manage.py loaddata initial_data
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from django.core import serializers
from django.core.management.base import BaseCommand

from inventory.models import Order, Product, SimulationConfig

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "initial_data.json"


class Command(BaseCommand):
    help = "Product/Order/SimulationConfig를 inventory/fixtures/initial_data.json으로 내보냅니다."

    def handle(self, *args, **options) -> None:
        objects = list(Product.objects.all()) + list(Order.objects.all()) + list(
            SimulationConfig.objects.all()
        )

        buffer = StringIO()
        serializers.serialize("json", objects, stream=buffer, indent=2, ensure_ascii=False)

        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(buffer.getvalue(), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"내보내기 완료: {FIXTURE_PATH}"))
