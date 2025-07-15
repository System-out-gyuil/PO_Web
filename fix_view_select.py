#!/usr/bin/env python
import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PO.settings')
django.setup()

from diary.models import Attribute

# 모든 속성의 view_select를 기본값으로 설정
attributes = Attribute.objects.all()
print(f"총 {attributes.count()}개의 속성을 찾았습니다.")

for attr in attributes:
    # 실제 상태 ID들에 맞게 설정 (전체 탭 포함)
    default_view_select = {
        "0": True,    # 전체 탭
        "37": True,   # 진행중
        "38": True,   # 종결
        "39": True,   # 계약전
        "49": True,   # 의사없음
        "50": True,   # 조건부결
        "54": True,   # 부재중
        "55": True,   # 연락두절
    }
    
    attr.view_select = default_view_select
    attr.save()
    print(f"속성 '{attr.name}'의 view_select를 설정했습니다.")

attributes = Attribute.objects.all()

for attr in attributes:
    print(f"속성 '{attr.name}'의 view_select: {attr.view_select}")

print("모든 속성의 view_select 설정이 완료되었습니다.") 