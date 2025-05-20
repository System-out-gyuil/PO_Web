import os
import django
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")
django.setup()
from main.models import Industry

# Excel 파일 경로
file_path = "/Users/user/Desktop/po/PO_Django/PO/업종_2025_05_21.xlsx"

# 엑셀 파일 읽기
df = pd.read_excel(file_path)

inserted_count = 0
for _, row in df.iterrows():
    big = row["대분류"]
    small = row["소분류"]

    # 중복 방지: 같은 레코드 없으면 저장
    if not Industry.objects.filter(big_category=big, small_category=small).exists():
        Industry.objects.create(big_category=big, small_category=small)
        inserted_count += 1

print(f"{inserted_count}개 업종 항목이 저장되었습니다.")