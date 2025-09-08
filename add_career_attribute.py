#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PO.settings')
django.setup()

from diary.models import AttributeType, User, Attribute

def add_career_attribute():
    """각 사용자별로 경력 속성을 추가하는 함수"""
    
    # 1. AttributeType ID 4 확인
    try:
        attribute_type = AttributeType.objects.get(id=4)
        print(f"AttributeType ID 4: {attribute_type.name}")
    except AttributeType.DoesNotExist:
        print("AttributeType ID 4가 존재하지 않습니다.")
        print("사용 가능한 AttributeType 목록:")
        for at in AttributeType.objects.all():
            print(f"  ID: {at.id}, Name: {at.name}")
        return
    
    # 2. 모든 사용자 조회
    users = User.objects.all()
    print(f"\n총 {users.count()}명의 사용자가 있습니다.")
    
    if not users.exists():
        print("사용자가 없습니다.")
        return
    
    # 3. 각 사용자별로 경력 속성 추가
    for user in users:
        print(f"\n사용자 {user.name} (ID: {user.id}) 처리 중...")
        
        # 이미 경력 속성이 있는지 확인
        existing_career = Attribute.objects.filter(
            user=user, 
            name='경력'
        ).first()
        
        if existing_career:
            print(f"  이미 경력 속성이 존재합니다. (ID: {existing_career.id})")
            continue
        
        # 해당 사용자의 기존 속성들 조회
        user_attributes = Attribute.objects.filter(user=user).order_by('sort_order')
        
        # sort_order 계산 (가장 마지막 숫자 + 1)
        if user_attributes.exists():
            max_sort_order = user_attributes.aggregate(max_order=models.Max('sort_order'))['max_order']
            new_sort_order = (max_sort_order or 0) + 1
        else:
            new_sort_order = 1
        
        # detail_sort_order 계산 (개업년월 바로 뒤)
        # 먼저 '개업년월' 속성을 찾아서 그 detail_sort_order + 1을 사용
        opening_date_attr = Attribute.objects.filter(
            user=user, 
            name='개업년월'
        ).first()
        
        if opening_date_attr:
            new_detail_sort_order = opening_date_attr.detail_sort_order + 1
        else:
            # 개업년월이 없으면 가장 큰 detail_sort_order + 1
            max_detail_sort_order = user_attributes.aggregate(
                max_detail_order=models.Max('detail_sort_order')
            )['max_detail_order']
            new_detail_sort_order = (max_detail_sort_order or 0) + 1
        
        # 경력 속성 생성
        career_attribute = Attribute.objects.create(
            name='경력',
            user=user,
            attributeType=attribute_type,
            assential=True,
            detail=True,
            sort_order=new_sort_order,
            view_select={},
            cascade=False,
            width=180,
            detail_sort_order=new_detail_sort_order
        )
        
        print(f"  경력 속성 추가 완료 (ID: {career_attribute.id})")
        print(f"  sort_order: {new_sort_order}, detail_sort_order: {new_detail_sort_order}")

if __name__ == "__main__":
    from django.db import models
    add_career_attribute()
