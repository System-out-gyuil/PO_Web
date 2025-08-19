from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Attribute, AttributeValue, User, DropdownAttribute, AttributeType
from django.db.models import Max
import json

@csrf_exempt  
def add_attribute(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        attr_type = request.POST.get('type', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': '속성명이 필요합니다.'})
        
        if not attr_type:
            return JsonResponse({'success': False, 'error': '속성 타입이 필요합니다.'})
        
        
        try:
            # 사용자 가져오기
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)  # 임시로 user id=1 사용
            
            # 사용자별 속성명 중복 체크
            existing_attribute = Attribute.objects.filter(user=user, name=name).first()
            if existing_attribute:
                return JsonResponse({'success': False, 'error': f'속성명 "{name}"이 이미 존재합니다.'})
            
            # AttributeType 가져오기 또는 생성
            attribute_type, _ = AttributeType.objects.get_or_create(name=attr_type)
            
            # 현재 최대 sort_order 구하기
            max_sort_order = Attribute.objects.aggregate(Max('sort_order'))['sort_order__max']
            next_sort_order = (max_sort_order or 0) + 1
            
            # 모든 status id 가져오기
            from diary.models import DropdownAttribute
            attribute_id = Attribute.objects.filter(user_id=user, name='상태').first()
            print(attribute_id)
            all_statuses = DropdownAttribute.objects.filter(attribute_id=attribute_id)
            print(all_statuses)
            # view_select 딕셔너리 생성 - 모든 status id에 대해 true 설정
            view_select_dict = {"0": True}  # 전체 탭
            for status in all_statuses:
                view_select_dict[str(status.id)] = True
            
            # 새 속성 생성
            attribute = Attribute.objects.create(
                name=name,
                user=user,
                attributeType=attribute_type,
                sort_order=next_sort_order,
                view_select=view_select_dict,
                cascade=False  # 새로 생성하는 속성은 기본적으로 동기화 비활성화
            )
            
            return JsonResponse({
                'success': True,
                'id': attribute.id,
                'name': attribute.name,
                'type': attribute.attributeType.name if attribute.attributeType else ''
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def delete_attribute(request):
    """속성과 관련된 모든 데이터 삭제"""
    if request.method == 'POST':
        attr_name = request.POST.get('name', '').strip()
        
        if not attr_name:
            return JsonResponse({'success': False, 'error': '속성명이 필요합니다.'})
        
        try:
            # 속성 찾기
            attribute = Attribute.objects.filter(name=attr_name).first()
            
            if not attribute:
                return JsonResponse({'success': False, 'error': '존재하지 않는 속성입니다.'})
            
            # essential 속성인지 확인
            if attribute.assential:
                return JsonResponse({'success': False, 'error': '필수 속성은 삭제할 수 없습니다.'})
            
            # 1. AttributeValue 먼저 삭제 (FK 제약 조건 때문에)
            AttributeValue.objects.filter(attribute=attribute).delete()
            
            # 2. DropdownAttribute 삭제 (dropdown 타입인 경우)
            if attribute.attributeType and attribute.attributeType.name == 'dropdown':
                DropdownAttribute.objects.filter(attribute=attribute).delete()
            
            # 3. 마지막으로 Attribute 삭제
            attribute.delete()
            
            return JsonResponse({'success': True, 'message': f'속성 "{attr_name}"이 성공적으로 삭제되었습니다.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def update_attribute_name(request):
    """속성명 변경 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        data = json.loads(request.body)
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        
        if not old_name or not new_name:
            return JsonResponse({'success': False, 'error': '기존 속성명과 새로운 속성명이 필요합니다.'})
        
        if old_name == new_name:
            return JsonResponse({'success': False, 'error': '기존 속성명과 새로운 속성명이 동일합니다.'})
        
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # 기존 속성 찾기
        attribute = Attribute.objects.filter(user=user, name=old_name).first()
        if not attribute:
            return JsonResponse({'success': False, 'error': f'속성 "{old_name}"을 찾을 수 없습니다.'})
        
        # 필수 속성인지 확인
        if attribute.assential:
            return JsonResponse({'success': False, 'error': '필수 속성의 이름은 변경할 수 없습니다.'})
        
        # 새 이름이 이미 존재하는지 확인
        existing_attribute = Attribute.objects.filter(user=user, name=new_name).first()
        if existing_attribute:
            return JsonResponse({'success': False, 'error': f'속성명 "{new_name}"이 이미 존재합니다.'})
        
        # 속성명 변경
        attribute.name = new_name
        attribute.save()
        
        return JsonResponse({
            'success': True,
            'message': f'속성명이 "{old_name}"에서 "{new_name}"으로 변경되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def toggle_attribute_visibility(request):
    """속성의 표시/숨김을 토글하는 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attribute_name = data.get('attribute_name')
            
            if not attribute_name:
                return JsonResponse({
                    'success': False,
                    'error': '속성명이 필요합니다.'
                })
            
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 속성 찾기
            try:
                attribute = Attribute.objects.get(user=user, name=attribute_name)
            except Attribute.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'속성 "{attribute_name}"을 찾을 수 없습니다.'
                })
            
            # 표시 상태 토글
            attribute.view_select = not attribute.view_select
            attribute.save()
            
            return JsonResponse({
                'success': True,
                'visible': attribute.view_select,
                'message': f'{attribute_name} 속성이 {"표시" if attribute.view_select else "숨김"} 상태로 변경되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def update_attribute_visibility(request):
    """속성별 상태 표시 설정을 업데이트하는 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            settings = data.get('settings', {})
            
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 각 속성의 view_select 업데이트
            for attr_id, view_select_settings in settings.items():
                try:
                    attr = Attribute.objects.get(id=attr_id, user=user)
                    attr.view_select = view_select_settings
                    attr.save()
                except Attribute.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': '속성 표시 설정이 저장되었습니다.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'}, status=405)

@require_GET
def get_hidden_attributes(request):
    """숨겨진 속성들의 목록을 반환하는 API"""
    try:
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        
        # 숨겨진 속성들 조회
        hidden_attributes = Attribute.objects.filter(
            user=user,
            view_select=False
        ).values('id', 'name', 'view_select')
        
        return JsonResponse({
            'success': True,
            'hidden_attributes': list(hidden_attributes)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def get_all_attributes(request):
    """모든 속성(필수 포함, detail=True/False 모두)을 반환하는 API"""
    try:
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        # select_related를 추가하여 N+1 쿼리 방지
        attributes = Attribute.objects.filter(user=user, detail=False).select_related('attributeType').order_by('sort_order', 'id')
        attributes_data = []
        
        for attr in attributes:
            attributes_data.append({
                'id': attr.id,
                'name': attr.name,
                'attributeType_name': attr.attributeType.name if attr.attributeType else '',
                'assential': attr.assential,
                'view_select': attr.view_select,
                'cascade': attr.cascade,  # cascade 필드 추가
                'sort_order': attr.sort_order,
                'detail': attr.detail  # detail 필드 추가
            })
        return JsonResponse({'success': True, 'attributes': attributes_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_GET
def get_dropdown_attributes(request):
    """dropdown 타입의 속성 목록을 반환하는 API (칸반보드 필터용)"""
    try:
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        
        # URL 파라미터에서 상태 ID 가져오기
        status_id = request.GET.get('status_id', 'all')
        
        # 기본 속성 쿼리 (view_select 필터링 제거, detail 필터링 제거)
        # select_related를 추가하여 N+1 쿼리 방지
        base_dropdown_attributes = Attribute.objects.filter(
            user=user, 
            attributeType__name='dropdown'
        ).select_related('attributeType').order_by('-assential', 'name')
        
        # 상태별 필터링 적용
        dropdown_attributes = filter_attributes_by_status(base_dropdown_attributes, status_id)
        
        attributes_data = []
        for attr in dropdown_attributes:
            attributes_data.append({
                'id': attr.id,
                'name': attr.name,
                'assential': attr.assential
            })
        
        return JsonResponse({
            'success': True,
            'attributes': attributes_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@csrf_exempt
def delete_attribute_value(request):
    """특정 행의 특정 속성 값을 삭제하는 API"""
    if request.method == 'POST':
        try:
            row_id = request.POST.get('id')
            field_name = request.POST.get('field')

            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            if not row_id or not field_name:
                return JsonResponse({
                    'success': False,
                    'error': '행 ID와 필드명이 필요합니다.'
                })
            
            # 해당 속성 찾기
            try:
                attribute = Attribute.objects.get(name=field_name, user=user)
            except Attribute.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'속성 \"{field_name}\"을 찾을 수 없습니다.'
                })
            
            # 해당 속성 값 삭제 (row_id, attribute_id로)
            AttributeValue.objects.filter(
                row_id=row_id,
                attribute_id=attribute.id
            ).delete()
            
            return JsonResponse({
                'success': True,
                'message': f'속성 \"{field_name}\" 값이 삭제되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)
def filter_attributes_by_status(queryset, status_id='all'):
    """상태 ID에 따라 속성들을 필터링하는 함수"""
    filtered_attrs = []
    
    for attr in queryset:
        
        if isinstance(attr.view_select, dict):
            if status_id == 'all':
                # 전체 탭에서는 "0" 키가 True인 속성들만 표시
                is_visible = attr.view_select.get('0', False)
                if is_visible:
                    filtered_attrs.append(attr)
            else:
                # 특정 상태 탭에서는 해당 상태 ID가 True인 속성들만 표시
                is_visible = attr.view_select.get(str(status_id), False)
                if is_visible:
                    filtered_attrs.append(attr)
        elif isinstance(attr.view_select, bool) and attr.view_select:
            # 기존 boolean 형태와의 호환성을 위해
            filtered_attrs.append(attr)
        else:
            pass
    
    return filtered_attrs
