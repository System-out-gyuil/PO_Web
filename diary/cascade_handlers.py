from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Attribute, AttributeValue, User, Row
import json

def sync_cascade_attributes(request, row_id, attribute_name, new_value):
    """cascade가 true인 속성이 수정될 때 원본 행과 복제된 행들을 동기화"""
    try:
        # 사용자 가져오기
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # 수정된 행 조회
        modified_row = Row.objects.get(id=row_id)
        
        print(f"=== Cascade 동기화 시작 ===")
        print(f"수정된 행 ID: {row_id}")
        print(f"수정된 행의 original_row_ids: {modified_row.original_row_ids}")
        print(f"수정된 행의 copied_row_ids: {modified_row.copied_row_ids}")
        
        # cascade가 true인 속성 조회 (사용자 정보 포함)
        try:
            cascade_attribute = Attribute.objects.get(name=attribute_name, user=user, cascade=True)
            print(f"Cascade 속성 찾음: {attribute_name}")
        except Attribute.DoesNotExist:
            print(f"Cascade 속성을 찾을 수 없습니다: {attribute_name}")
            return 0  # cascade가 false인 속성이면 동기화하지 않음
        
        # === 개선된 관련 행 찾기 ===
        # 1. 수정된 행의 원본 행들
        original_rows = []
        for original_id in modified_row.original_row_ids:
            try:
                original_row = Row.objects.get(id=original_id)
                original_rows.append(original_row)
            except Row.DoesNotExist:
                print(f"원본 행 {original_id}를 찾을 수 없습니다.")
                continue
        
        # 2. 수정된 행의 복제된 행들
        copied_rows = []
        for copied_id in modified_row.copied_row_ids:
            try:
                copied_row = Row.objects.get(id=copied_id)
                copied_rows.append(copied_row)
            except Row.DoesNotExist:
                print(f"복제된 행 {copied_id}를 찾을 수 없습니다.")
                continue
        
        # 3. 원본 행들의 복제된 행들도 포함
        for original_row in original_rows:
            for copied_id in original_row.copied_row_ids:
                try:
                    copied_row = Row.objects.get(id=copied_id)
                    if copied_row not in copied_rows and copied_row.id != row_id:
                        copied_rows.append(copied_row)
                except Row.DoesNotExist:
                    continue
        
        # 4. 복제된 행들의 원본 행들도 포함
        for copied_row in copied_rows:
            for original_id in copied_row.original_row_ids:
                try:
                    original_row = Row.objects.get(id=original_id)
                    if original_row not in original_rows and original_row.id != row_id:
                        original_rows.append(original_row)
                except Row.DoesNotExist:
                    continue
        
        # 모든 관련 행들을 하나의 리스트로 합치기
        all_related_rows = original_rows + copied_rows
        unique_related_rows = []
        seen_ids = set()
        
        for row in all_related_rows:
            if row.id not in seen_ids and row.id != row_id:
                unique_related_rows.append(row)
                seen_ids.add(row.id)
        
        print(f"동기화할 관련 행들: {[row.id for row in unique_related_rows]}")
        
        # === 동기화 실행 ===
        synced_count = 0
        for row in unique_related_rows:
            print(f"행 {row.id}의 {attribute_name} 속성을 '{new_value}'로 업데이트 중...")
            
            # AttributeValue 조회 또는 생성
            attr_value, created = AttributeValue.objects.get_or_create(
                row=row,
                attribute=cascade_attribute,
                defaults={'value': new_value}
            )
            
            if not created:
                old_value = attr_value.value
                attr_value.value = new_value
                attr_value.save()
                print(f"  - 기존 값 '{old_value}' → 새 값 '{new_value}'로 변경")
            else:
                print(f"  - 새 값 '{new_value}'로 생성")
            
            synced_count += 1
        
        print(f"실제 동기화된 행 수: {synced_count}")
        print(f"=== Cascade 동기화 완료 ===")
        return synced_count
        
    except Exception as e:
        print(f"Cascade 동기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_cascade_attributes():
    """cascade가 true인 속성들의 목록을 반환"""
    return Attribute.objects.filter(cascade=True).values_list('name', flat=True)

@csrf_exempt
def toggle_cascade_attribute(request):
    """속성의 cascade 값을 토글하는 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        data = json.loads(request.body)
        attribute_name = data.get('attribute_name')
        
        if not attribute_name:
            return JsonResponse({'success': False, 'error': '속성명이 필요합니다.'})
        
        # 사용자 가져오기
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # 속성 조회
        try:
            attribute = Attribute.objects.get(name=attribute_name, user=user)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '속성을 찾을 수 없습니다.'})
        
        # cascade 값 토글
        attribute.cascade = not attribute.cascade
        attribute.save()
        
        return JsonResponse({
            'success': True,
            'cascade': attribute.cascade,
            'message': f'{attribute_name} 속성의 cascade가 {attribute.cascade}로 변경되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'토글 중 오류가 발생했습니다: {str(e)}'})

@require_GET
def get_cascade_attributes_list(request):
    """cascade가 true인 속성들의 목록을 반환하는 API"""
    try:
        # 사용자 가져오기
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # cascade가 true인 속성들 조회
        cascade_attributes = Attribute.objects.filter(
            user=user,
            cascade=True
        ).values('id', 'name', 'cascade')
        
        return JsonResponse({
            'success': True,
            'cascade_attributes': list(cascade_attributes)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'목록 조회 중 오류가 발생했습니다: {str(e)}'})
