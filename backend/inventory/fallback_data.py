"""엑셀 파일을 읽을 수 없을 때 사용하는 하드코딩 시드 데이터.

채용 과제 명세(섹션 F)에 기재된 값과 동일하다.
"""

from __future__ import annotations

from inventory.constants import ProductCategory, ProductSize

# (sku, name, category, size, unit_price, initial_stock, safety_stock,
#  reorder_point, moq, production_lead_time_days, delivery_lead_time_days)
PRODUCTS: list[tuple] = [
    ("BS-MAT-SS-001", "베이직 매트리스", ProductCategory.MATTRESS, ProductSize.SS, 350000, 20, 8, 12, 20, 5, 2),
    ("BS-MAT-Q-002", "베이직 매트리스", ProductCategory.MATTRESS, ProductSize.Q, 450000, 15, 8, 12, 20, 5, 2),
    ("BS-MAT-K-003", "베이직 매트리스", ProductCategory.MATTRESS, ProductSize.K, 550000, 10, 5, 8, 15, 5, 2),
    ("BS-MAT-Q-004", "프리미엄 포켓 매트리스", ProductCategory.MATTRESS, ProductSize.Q, 890000, 8, 4, 6, 10, 7, 3),
    ("BS-MAT-K-005", "프리미엄 포켓 매트리스", ProductCategory.MATTRESS, ProductSize.K, 1090000, 6, 3, 5, 10, 7, 3),
    ("BS-TOP-Q-006", "메모리폼 토퍼", ProductCategory.TOPPER, ProductSize.Q, 180000, 30, 10, 15, 30, 3, 2),
    ("BS-TOP-K-007", "메모리폼 토퍼", ProductCategory.TOPPER, ProductSize.K, 210000, 25, 10, 15, 30, 3, 2),
    ("BS-FRM-Q-008", "원목 프레임", ProductCategory.FRAME, ProductSize.Q, 320000, 12, 5, 8, 12, 10, 4),
    ("BS-FRM-K-009", "원목 프레임", ProductCategory.FRAME, ProductSize.K, 380000, 9, 4, 6, 10, 10, 4),
    ("BS-PIL-STD-010", "경추 베개", ProductCategory.PILLOW, ProductSize.STD, 59000, 60, 20, 30, 60, 2, 2),
]

# (order_no, order_date, sku, quantity, customer_name, desired_delivery_date or None)
ORDERS: list[tuple] = [
    ("ORD-0001", "2026-06-01", "BS-MAT-Q-002", 5, "김서연", "2026-06-05"),
    ("ORD-0002", "2026-06-01", "BS-TOP-Q-006", 8, "이준호", None),
    ("ORD-0003", "2026-06-01", "BS-PIL-STD-010", 10, "박민지", None),
    ("ORD-0004", "2026-06-02", "BS-MAT-Q-002", 4, "최우진", "2026-06-06"),
    ("ORD-0005", "2026-06-02", "BS-MAT-SS-001", 6, "정하늘", None),
    ("ORD-0006", "2026-06-02", "BS-MAT-K-005", 3, "강도윤", "2026-06-09"),
    ("ORD-0007", "2026-06-03", "BS-MAT-Q-002", 6, "윤서아", "2026-06-07"),
    ("ORD-0008", "2026-06-03", "BS-FRM-Q-008", 4, "임지후", None),
    ("ORD-0009", "2026-06-03", "BS-MAT-K-003", 5, "한가은", None),
    ("ORD-0010", "2026-06-04", "BS-MAT-Q-002", 5, "오수빈", "2026-06-08"),
    ("ORD-0011", "2026-06-04", "BS-MAT-K-005", 4, "신예준", "2026-06-11"),
    ("ORD-0012", "2026-06-04", "BS-TOP-K-007", 10, "권하준", None),
    ("ORD-0013", "2026-06-05", "BS-PIL-STD-010", 25, "문채원", None),
    ("ORD-0014", "2026-06-05", "BS-MAT-SS-001", 8, "배서준", None),
    ("ORD-0015", "2026-06-05", "BS-FRM-K-009", 5, "조유나", "2026-06-12"),
    ("ORD-0016", "2026-06-06", "BS-MAT-Q-002", 3, "남도현", None),
    ("ORD-0017", "2026-06-06", "BS-MAT-Q-004", 4, "유시우", None),
    ("ORD-0018", "2026-06-06", "BS-FRM-K-009", 4, "구하린", "2026-06-15"),
    ("ORD-0019", "2026-06-07", "BS-MAT-K-003", 4, "홍지원", None),
    ("ORD-0020", "2026-06-07", "BS-TOP-Q-006", 12, "전수아", None),
    ("ORD-0021", "2026-06-08", "BS-MAT-Q-002", 6, "고은우", None),
    ("ORD-0022", "2026-06-08", "BS-MAT-K-005", 3, "서지안", None),
    ("ORD-0023", "2026-06-08", "BS-PIL-STD-010", 20, "황민준", None),
    ("ORD-0024", "2026-06-09", "BS-MAT-SS-001", 5, "송하율", None),
    ("ORD-0025", "2026-06-09", "BS-FRM-Q-008", 5, "안서윤", None),
    ("ORD-0026", "2026-06-10", "BS-MAT-Q-002", 4, "류준서", None),
    ("ORD-0027", "2026-06-10", "BS-MAT-Q-004", 3, "백지아", None),
    ("ORD-0028", "2026-06-10", "BS-FRM-K-009", 3, "노이서", None),
    ("ORD-0029", "2026-06-11", "BS-TOP-K-007", 12, "심도경", None),
    ("ORD-0030", "2026-06-11", "BS-MAT-K-003", 4, "양하은", None),
    ("ORD-0031", "2026-06-12", "BS-MAT-Q-002", 5, "추서진", None),
    ("ORD-0032", "2026-06-12", "BS-PIL-STD-010", 30, "방예린", None),
    ("ORD-0033", "2026-06-13", "BS-MAT-SS-001", 6, "변지호", None),
    ("ORD-0034", "2026-06-13", "BS-MAT-K-005", 3, "선우주아", None),
    ("ORD-0035", "2026-06-14", "BS-MAT-Q-002", 4, "마하준", None),
]

SIMULATION_START_DATE = "2026-06-01"
SIMULATION_END_DATE = "2026-06-30"
