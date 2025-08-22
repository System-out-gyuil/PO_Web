from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Prefetch, Q
from .models import Attribute, AttributeValue, User, Row, DropdownAttribute, KanbanSettings
import json

@require_GET
def get_kanban_data(request):
    """특정 dropdown 속성에 대한 칸반보드 데이터를 반환하는 API"""
    try:
        user_id = request.session.get('diary_member_id')
        
        # 사용자 ID가 없으면 로그인되지 않은 상태
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': '로그인이 필요합니다.'
            })
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # 사용자가 존재하지 않으면 로그인되지 않은 상태
            return JsonResponse({
                'success': False,
                'error': '사용자를 찾을 수 없습니다.'
            })
        
        attr_name = request.GET.get('attr_name')
        
        if not attr_name:
            return JsonResponse({
                'success': False,
                'error': 'attr_name parameter is required'
            })
        
        # 해당 속성과 진행사항 속성을 한 번에 가져오기
        attributes = Attribute.objects.filter(
            user=user,
            name__in=[attr_name, '진행사항'],
            attributeType__name='dropdown'
        ).select_related('attributeType')
        
        kanban_attr = None
        progress_attr = None
        
        for attr in attributes:
            if attr.name == attr_name:
                kanban_attr = attr
            elif attr.name == '진행사항':
                progress_attr = attr
        
        if not kanban_attr:
            return JsonResponse({
                'success': False,
                'error': f'Dropdown attribute "{attr_name}" not found'
            })
        
        # 칸반보드 설정 가져오기
        kanban_settings = KanbanSettings.objects.filter(user=user).first()
        settings = kanban_settings.settings if kanban_settings else {}
        
        # 드롭다운 옵션들을 한 번에 가져오기
        dropdown_options = DropdownAttribute.objects.filter(attribute=kanban_attr).order_by('order', 'id')
        
        # 진행사항 옵션들을 미리 가져오기
        progress_options = []
        if progress_attr:
            progress_options = list(DropdownAttribute.objects.filter(attribute=progress_attr).values('id', 'option'))
        
        # 모든 행과 속성값을 최적화된 쿼리로 가져오기
        # 필요한 속성들만 미리 정의
        needed_attrs = [attr_name, '회사명', '진행사항']
        if settings.get('filters'):
            for filter_rule in settings['filters']:
                if filter_rule.get('attribute') and filter_rule.get('attribute') not in needed_attrs:
                    needed_attrs.append(filter_rule.get('attribute'))
        
        if settings.get('custom_rules'):
            for rule in settings['custom_rules']:
                for condition in rule.get('conditions', []):
                    if condition.get('attribute') and condition.get('attribute') not in needed_attrs:
                        needed_attrs.append(condition.get('attribute'))
        
        # 필요한 속성들만 필터링하여 가져오기
        needed_attributes = Attribute.objects.filter(
            user=user,
            name__in=needed_attrs
        )
        
        # 행과 속성값을 최적화된 쿼리로 가져오기
        rows = Row.objects.filter(user=user).prefetch_related(
            Prefetch(
                'values',
                queryset=AttributeValue.objects.filter(
                    attribute__in=needed_attributes
                ).select_related('attribute')
            )
        ).order_by('order', 'id')
        
        # 칸반보드 데이터 생성
        board_data = []
        
        # 행별 속성값을 미리 구성하여 N+1 쿼리 방지
        row_values_cache = {}
        for row in rows:
            row_values = {}
            for attr_value in row.values.all():
                if attr_value.attribute:
                    row_values[attr_value.attribute.name] = attr_value.value
            row_values_cache[row.id] = row_values
        
        # 각 상태별로 행들을 그룹화
        status_rows = {}
        for row in rows:
            row_values = row_values_cache.get(row.id, {})
            status_value = row_values.get(attr_name)
            if status_value:
                if status_value not in status_rows:
                    status_rows[status_value] = []
                status_rows[status_value].append(row)
        
        for option in dropdown_options:
            # 해당 상태를 가진 행들
            matching_rows = status_rows.get(str(option.id), [])
            
            # 각 행의 데이터를 entry 형태로 변환
            entries = []
            for row in matching_rows:
                row_values = row_values_cache.get(row.id, {})
                
                # 필터 적용
                if not apply_kanban_filters(row_values, settings):
                    continue
                
                # 커스텀 규칙 적용
                if not apply_custom_rules(row_values, settings):
                    continue
                
                # entry 데이터 생성
                entry_data = {
                    'id': row.id,
                    'name': row_values.get('회사명', ''),
                    'now': row_values.get('진행사항', ''),
                    'progress': row_values.get('진행사항', '')  # 진행사항 값
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
            'progress_options': progress_options
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'칸반보드 데이터 처리 중 오류가 발생했습니다: {str(e)}'
        })

def apply_kanban_filters(row_values, settings):
    """칸반보드 필터 적용 - 최적화된 버전"""
    filters = settings.get('filters', [])
    if not filters:
        return True
        
    for filter_rule in filters:
        attr_name = filter_rule.get('attribute')
        operator = filter_rule.get('operator', 'equals')
        expected_value = str(filter_rule.get('value'))
        
        if not attr_name or not expected_value:
            continue
            
        actual_value = str(row_values.get(attr_name, ''))
        
        # 연산자별 비교 최적화
        if operator == 'equals':
            if actual_value != expected_value:
                return False
        elif operator == 'not_equals':
            if actual_value == expected_value:
                return False
        elif operator == 'contains':
            if expected_value not in actual_value:
                return False
        elif operator == 'not_contains':
            if expected_value in actual_value:
                return False
    
    return True

def apply_custom_rules(row_values, settings):
    """커스텀 규칙 적용 - 최적화된 버전"""
    custom_rules = settings.get('custom_rules', [])
    if not custom_rules:
        return True
        
    for rule in custom_rules:
        conditions = rule.get('conditions', [])
        logic = rule.get('logic', 'AND')
        
        if not conditions:
            continue
            
        # 조건 결과를 미리 계산
        condition_results = []
        for condition in conditions:
            attr_name = condition.get('attribute')
            operator = condition.get('operator', 'equals')
            expected_value = str(condition.get('value'))
            
            if not attr_name or not expected_value:
                continue
                
            actual_value = str(row_values.get(attr_name, ''))
            result = False
            
            # 연산자별 비교 최적화
            if operator == 'equals':
                result = (actual_value == expected_value)
            elif operator == 'not_equals':
                result = (actual_value != expected_value)
            elif operator == 'contains':
                result = (expected_value in actual_value)
            elif operator == 'not_contains':
                result = (expected_value not in actual_value)
                
            condition_results.append(result)
        
        # 로직에 따른 결과 계산
        if logic == 'AND':
            if not all(condition_results):
                return False
        elif logic == 'OR':
            if not any(condition_results):
                return False
    
    return True

@csrf_exempt
def update_kanban_option_order(request):
    """칸반보드 옵션 순서 변경 API - 최적화된 버전"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attr_name = data.get('attr_name')
            option_orders = data.get('option_orders', [])
            
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
            
            # 벌크 업데이트로 최적화
            update_queries = []
            for option_data in option_orders:
                option_id = option_data.get('id')
                new_order = option_data.get('order')
                
                if option_id is not None and new_order is not None:
                    update_queries.append(
                        DropdownAttribute.objects.filter(
                            id=option_id,
                            attribute=kanban_attr
                        ).update(order=new_order)
                    )
            
            return JsonResponse({
                'success': True,
                'message': '칸반보드 옵션 순서가 업데이트되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@require_GET
def get_kanban_settings(request):
    """칸반보드 설정을 가져오는 API - 최적화된 버전"""
    try:
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        
        kanban_settings = KanbanSettings.objects.filter(user=user).first()
        if kanban_settings:
            return JsonResponse({'success': True, 'settings': kanban_settings.settings})
        
        # 기본값
        return JsonResponse({
            'success': True, 
            'settings': {
                'main_attr': '',
                'filters': [],
                'custom_rules': []
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
def save_kanban_settings(request):
    """칸반보드 설정을 저장하는 API - 최적화된 버전"""
    if request.method == 'POST':
        try:
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            data = json.loads(request.body)
            settings = data.get('settings', {})
            
            kanban_settings, _ = KanbanSettings.objects.get_or_create(user=user)
            kanban_settings.settings = settings
            kanban_settings.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@require_GET
def get_dropdown_attributes_for_kanban(request):
    """칸반보드 설정용 드롭다운 속성들을 가져오는 API - 최적화된 버전"""
    try:
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        
        # 드롭다운 타입의 속성들과 옵션들을 한 번에 가져오기
        dropdown_attrs = Attribute.objects.filter(
            user=user,
            attributeType__name='dropdown'
        ).prefetch_related(
            Prefetch(
                'dropdown_attributes',
                queryset=DropdownAttribute.objects.order_by('order', 'id')
            )
        ).order_by('sort_order', 'id')
        
        attributes_data = []
        for attr in dropdown_attrs:
            options_data = [
                {'id': opt.id, 'name': opt.option, 'color': opt.color} 
                for opt in attr.dropdown_attributes.all()
            ]
            
            attributes_data.append({
                'id': attr.id,
                'name': attr.name,
                'options': options_data
            })
        
        return JsonResponse({
            'success': True,
            'attributes': attributes_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 