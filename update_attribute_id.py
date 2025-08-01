#!/usr/bin/env python
"""
Attribute ID 변경 스크립트
Attribute 테이블의 ID를 변경할 때 FK로 참조하는 모든 테이블들의 ID도 함께 변경합니다.
"""

import os
import sys
import django
from django.db import transaction
from django.db.models import Q

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PO.settings')
django.setup()

from diary.models import Attribute, AttributeValue, DropdownAttribute, CalendarSettings, KanbanSettings

def update_attribute_id(old_id, new_id, user_id=None):
    """
    Attribute ID를 변경하고 FK로 참조하는 모든 테이블들의 ID도 함께 변경합니다.
    
    Args:
        old_id (int): 변경할 Attribute의 기존 ID
        new_id (int): 변경할 Attribute의 새로운 ID
        user_id (int, optional): 특정 사용자의 Attribute만 변경할 경우 사용자 ID
    
    Returns:
        bool: 성공 여부
    """
    try:
        with transaction.atomic():
            print(f"=== Attribute ID 변경 시작 ===")
            print(f"기존 ID: {old_id} -> 새로운 ID: {new_id}")
            
            # 1. 기존 Attribute 확인
            if user_id:
                old_attribute = Attribute.objects.filter(id=old_id, user_id=user_id).first()
            else:
                old_attribute = Attribute.objects.filter(id=old_id).first()
            
            if not old_attribute:
                print(f"❌ ID {old_id}인 Attribute를 찾을 수 없습니다.")
                return False
            
            # 2. 새로운 ID가 이미 존재하는지 확인
            if user_id:
                existing_attribute = Attribute.objects.filter(id=new_id, user_id=user_id).first()
            else:
                existing_attribute = Attribute.objects.filter(id=new_id).first()
            
            if existing_attribute:
                print(f"❌ 새로운 ID {new_id}가 이미 존재합니다.")
                return False
            
            print(f"✅ 변경할 Attribute: {old_attribute.name} (사용자: {old_attribute.user.name if old_attribute.user else 'None'})")
            
            # 3. FK로 참조하는 테이블들 확인 및 변경
            affected_tables = []
            
            # AttributeValue 테이블 확인
            attribute_values = AttributeValue.objects.filter(attribute_id=old_id)
            if attribute_values.exists():
                affected_tables.append(f"AttributeValue: {attribute_values.count()}개 행")
            
            # DropdownAttribute 테이블 확인
            dropdown_attributes = DropdownAttribute.objects.filter(attribute_id=old_id)
            if dropdown_attributes.exists():
                affected_tables.append(f"DropdownAttribute: {dropdown_attributes.count()}개 행")
            
            # CalendarSettings 테이블 확인 (settings JSON 필드 내에서 attribute_id 참조 가능성)
            calendar_settings = CalendarSettings.objects.filter(
                settings__icontains=str(old_id)
            )
            if calendar_settings.exists():
                affected_tables.append(f"CalendarSettings: {calendar_settings.count()}개 행")
            
            # KanbanSettings 테이블 확인 (settings JSON 필드 내에서 attribute_id 참조 가능성)
            kanban_settings = KanbanSettings.objects.filter(
                settings__icontains=str(old_id)
            )
            if kanban_settings.exists():
                affected_tables.append(f"KanbanSettings: {kanban_settings.count()}개 행")
            
            print(f"📋 영향받는 테이블들:")
            for table in affected_tables:
                print(f"  - {table}")
            
            # 4. 실제 변경 작업 수행
            print(f"\n🔄 ID 변경 작업 시작...")
            
            # AttributeValue 테이블 업데이트
            if attribute_values.exists():
                updated_count = attribute_values.update(attribute_id=new_id)
                print(f"  ✅ AttributeValue: {updated_count}개 행 업데이트 완료")
            
            # DropdownAttribute 테이블 업데이트
            if dropdown_attributes.exists():
                updated_count = dropdown_attributes.update(attribute_id=new_id)
                print(f"  ✅ DropdownAttribute: {updated_count}개 행 업데이트 완료")
            
            # CalendarSettings 테이블 업데이트 (JSON 필드 내 attribute_id 변경)
            if calendar_settings.exists():
                updated_count = 0
                for setting in calendar_settings:
                    settings_data = setting.settings
                    if isinstance(settings_data, dict):
                        # JSON 필드 내에서 attribute_id를 찾아 변경
                        settings_str = str(settings_data)
                        if str(old_id) in settings_str:
                            # JSON 문자열에서 old_id를 new_id로 변경
                            import json
                            settings_str = settings_str.replace(str(old_id), str(new_id))
                            try:
                                setting.settings = json.loads(settings_str)
                                setting.save()
                                updated_count += 1
                            except json.JSONDecodeError:
                                print(f"  ⚠️ CalendarSettings ID {setting.id} JSON 파싱 오류")
                print(f"  ✅ CalendarSettings: {updated_count}개 행 업데이트 완료")
            
            # KanbanSettings 테이블 업데이트 (JSON 필드 내 attribute_id 변경)
            if kanban_settings.exists():
                updated_count = 0
                for setting in kanban_settings:
                    settings_data = setting.settings
                    if isinstance(settings_data, dict):
                        # JSON 필드 내에서 attribute_id를 찾아 변경
                        settings_str = str(settings_data)
                        if str(old_id) in settings_str:
                            # JSON 문자열에서 old_id를 new_id로 변경
                            import json
                            settings_str = settings_str.replace(str(old_id), str(new_id))
                            try:
                                setting.settings = json.loads(settings_str)
                                setting.save()
                                updated_count += 1
                            except json.JSONDecodeError:
                                print(f"  ⚠️ KanbanSettings ID {setting.id} JSON 파싱 오류")
                print(f"  ✅ KanbanSettings: {updated_count}개 행 업데이트 완료")
            
            # 5. 마지막으로 Attribute 테이블의 ID 변경
            # Django ORM에서는 직접 ID 변경이 어려우므로 새로운 객체 생성 후 기존 객체 삭제
            new_attribute = Attribute(
                id=new_id,
                name=old_attribute.name,
                user=old_attribute.user,
                attributeType=old_attribute.attributeType,
                assential=old_attribute.assential,
                detail=old_attribute.detail,
                sort_order=old_attribute.sort_order,
                view_select=old_attribute.view_select,
                cascade=old_attribute.cascade,
                width=old_attribute.width
            )
            new_attribute.save()
            
            # 기존 객체 삭제
            old_attribute.delete()
            
            print(f"\n✅ Attribute ID 변경 완료!")
            print(f"  기존 ID: {old_id} -> 새로운 ID: {new_id}")
            print(f"  속성명: {new_attribute.name}")
            
            return True
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def update_attribute_order(user_id, attribute_orders):
    """
    여러 Attribute의 순서를 한 번에 변경합니다.
    
    Args:
        user_id (int): 사용자 ID
        attribute_orders (list): [(old_id, new_id), ...] 형태의 리스트
    
    Returns:
        bool: 성공 여부
    """
    print(f"=== Attribute 순서 일괄 변경 시작 ===")
    print(f"사용자 ID: {user_id}")
    print(f"변경할 Attribute 개수: {len(attribute_orders)}")
    
    try:
        with transaction.atomic():
            for i, (old_id, new_id) in enumerate(attribute_orders, 1):
                print(f"\n[{i}/{len(attribute_orders)}] Attribute ID {old_id} -> {new_id} 변경 중...")
                
                success = update_attribute_id(old_id, new_id, user_id)
                if not success:
                    print(f"❌ Attribute ID {old_id} -> {new_id} 변경 실패")
                    return False
            
            print(f"\n✅ 모든 Attribute 순서 변경 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 일괄 변경 중 오류 발생: {str(e)}")
        return False

def show_user_attributes(user_id):
    """
    특정 사용자의 Attribute 목록을 보여줍니다.
    
    Args:
        user_id (int): 사용자 ID
    """
    attributes = Attribute.objects.filter(user_id=user_id).order_by('sort_order', 'id')
    
    print(f"=== 사용자 ID {user_id}의 Attribute 목록 ===")
    print(f"{'ID':<5} {'이름':<20} {'필수':<5} {'상세':<5} {'순서':<5}")
    print("-" * 50)
    
    for attr in attributes:
        essential = "✓" if attr.assential else ""
        detail = "✓" if attr.detail else ""
        print(f"{attr.id:<5} {attr.name:<20} {essential:<5} {detail:<5} {attr.sort_order:<5}")

if __name__ == "__main__":
    # 사용 예시
    
    # 1. 특정 사용자의 Attribute 목록 확인
    user_id = 1  # 변경할 사용자 ID
    show_user_attributes(user_id)
    
    # 2. 단일 Attribute ID 변경
    # old_id = 16
    # new_id = 18
    # success = update_attribute_id(old_id, new_id, user_id)
    # print(f"변경 결과: {'성공' if success else '실패'}")
    
    # 3. 여러 Attribute 순서 일괄 변경
    # attribute_orders = [
    #     (16, 18),  # ID 16을 18로 변경
    #     (17, 19),  # ID 17을 19로 변경
    #     # 추가 변경사항...
    # ]
    # success = update_attribute_order(user_id, attribute_orders)
    # print(f"일괄 변경 결과: {'성공' if success else '실패'}")
    
    print("\n=== 사용법 ===")
    print("1. 단일 Attribute ID 변경:")
    print("   update_attribute_id(old_id, new_id, user_id)")
    print("\n2. 여러 Attribute 순서 일괄 변경:")
    print("   update_attribute_order(user_id, [(old_id1, new_id1), (old_id2, new_id2), ...])")
    print("\n3. 사용자 Attribute 목록 확인:")
    print("   show_user_attributes(user_id)") 