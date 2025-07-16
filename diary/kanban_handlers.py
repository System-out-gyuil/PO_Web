from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Attribute, AttributeValue, User, Row, DropdownAttribute
import json

@require_GET
def get_kanban_data(request):
    """특정 dropdown 속성에 대한 칸반보드 데이터를 반환하는 API"""
    try:
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        attr_name = request.GET.get('attr_name')
        
        if not attr_name:
            return JsonResponse({
                'success': False,
                'error': 'attr_name parameter is required'
            })
        
        # 해당 속성 찾기
        kanban_attr = Attribute.objects.filter(
            user=user, 
            name=attr_name, 
            attributeType__name='dropdown'
        ).first()
        
        if not kanban_attr:
            return JsonResponse({
                'success': False,
                'error': f'Dropdown attribute "{attr_name}" not found'
            })
        
        # 칸반보드 데이터 생성
        board_data = []
        dropdown_options = DropdownAttribute.objects.filter(attribute=kanban_attr).order_by('order', 'id')
        
        for option in dropdown_options:
            # 해당 상태를 가진 행들 찾기
            rows = Row.objects.filter(
                user=user,
                values__attribute=kanban_attr,
                values__value=str(option.id)
            ).order_by('order', 'id')
            
            # 각 행의 데이터를 entry 형태로 변환
            entries = []
            for row in rows:
                # 행의 속성값들 가져오기
                row_values = {}
                for attr_value in row.values.all():
                    if attr_value.attribute:
                        row_values[attr_value.attribute.name] = attr_value.value
                
                # entry 데이터 생성
                entry_data = {
                    'id': row.id,
                    'name': row_values.get('회사명', ''),
                }
                entries.append(entry_data)
            
            # 상태 정보
            status_data = {
                'id': option.id,
                'name': option.option,
                'color': option.color
            }
            
            board_data.append({
                'status': status_data,
                'entries': entries
            })
        
        return JsonResponse({
            'success': True,
            'board': board_data,
            'selected_attr': attr_name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
def update_kanban_option_order(request):
    """칸반보드 옵션 순서 변경 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attr_name = data.get('attr_name')
            option_orders = data.get('option_orders', [])  # [{'id': 1, 'order': 0}, ...]
            
            if not attr_name or not option_orders:
                return JsonResponse({
                    'success': False,
                    'error': 'attr_name과 option_orders가 필요합니다.'
                })
            
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 해당 속성 찾기
            kanban_attr = Attribute.objects.filter(
                user=user, 
                name=attr_name, 
                attributeType__name='dropdown'
            ).first()
            
            if not kanban_attr:
                return JsonResponse({
                    'success': False,
                    'error': f'Dropdown attribute "{attr_name}" not found'
                })
            
            # 옵션 순서 업데이트
            for option_data in option_orders:
                option_id = option_data.get('id')
                new_order = option_data.get('order')
                
                if option_id is not None and new_order is not None:
                    DropdownAttribute.objects.filter(
                        id=option_id,
                        attribute=kanban_attr
                    ).update(order=new_order)
            
            return JsonResponse({
                'success': True,
                'message': '칸반보드 옵션 순서가 업데이트되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=405) 