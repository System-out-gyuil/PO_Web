from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Prefetch
from .models import Attribute, AttributeValue, Row, CalendarSettings
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def _parse_date_string(date_str):
    """날짜 문자열을 파싱하는 헬퍼 함수"""
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    
    # ISO 형식 (2023-12-25T10:30:00)
    if 'T' in date_str:
        try:
            return datetime.fromisoformat(date_str.split('.')[0])
        except ValueError:
            pass
    
    # 표준 형식들
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2023-12-25 10:30:00
        '%Y-%m-%d %H:%M',     # 2023-12-25 10:30
        '%Y-%m-%d'            # 2023-12-25
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def _get_user_from_session(request):
    """세션에서 사용자 ID를 가져오는 헬퍼 함수"""
    user_id = request.session.get('diary_member_id')
    if not user_id:
        raise ValueError("사용자 세션이 없습니다.")
    return user_id

@require_GET
def get_datetime_attributes(request):
    """datetime 타입의 속성 목록을 반환하는 API"""
    try:
        user_id = _get_user_from_session(request)
        
        # select_related로 user 정보를 미리 가져옴
        datetime_attributes = Attribute.objects.filter(
            user_id=user_id, 
            attributeType__name='datetime'
        ).select_related('user').order_by('name')
        
        attributes_data = [
            {
                'id': attr.id,
                'name': attr.name,
                'type': 'datetime'
            }
            for attr in datetime_attributes
        ]
        
        return JsonResponse({
            'success': True,
            'attributes': attributes_data
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=401)
    except Exception as e:
        logger.error(f"get_datetime_attributes error: {e}")
        return JsonResponse({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }, status=500)

@require_GET
def get_calendar_settings(request):
    """캘린더 설정을 가져오는 API"""
    try:
        user_id = _get_user_from_session(request)
        
        calendar_settings = CalendarSettings.objects.filter(user_id=user_id).first()
        
        if calendar_settings:
            return JsonResponse({
                'success': True, 
                'settings': calendar_settings.settings
            })
        
        # 기본값 반환
        return JsonResponse({
            'success': True, 
            'settings': {'date_fields': [], 'custom_events': []}
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=401)
    except Exception as e:
        logger.error(f"get_calendar_settings error: {e}")
        return JsonResponse({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }, status=500)

@csrf_exempt
def save_calendar_settings(request):
    """캘린더 설정을 저장하는 API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 메서드만 허용됩니다.'}, status=405)
    
    try:
        user_id = _get_user_from_session(request)
        data = json.loads(request.body)
        settings = data.get('settings', {})
        
        calendar_settings, created = CalendarSettings.objects.get_or_create(
            user_id=user_id,
            defaults={'settings': settings}
        )
        
        if not created:
            calendar_settings.settings = settings
            calendar_settings.save(update_fields=['settings'])
        
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=401)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '잘못된 JSON 형식입니다.'
        }, status=400)
    except Exception as e:
        logger.error(f"save_calendar_settings error: {e}")
        return JsonResponse({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }, status=500)

@require_GET
def calendar_events(request):
    """캘린더 이벤트를 가져오는 API"""
    try:
        user_id = _get_user_from_session(request)
        
        # 캘린더 설정 가져오기
        calendar_settings = CalendarSettings.objects.filter(user_id=user_id).first()
        settings = calendar_settings.settings if calendar_settings else {}
        
        events = []
        
        # 1. 기준 날짜 필드별로 Row에서 카드 생성
        date_fields = settings.get('date_fields', [])
        if date_fields:
            # 필요한 속성들을 한 번에 가져오기
            attr_ids = [df['attribute'] for df in date_fields if df.get('view_check', True)]
            attributes = {
                attr.id: attr for attr in Attribute.objects.filter(
                    id__in=attr_ids, 
                    user_id=user_id
                )
            }
            
            # 사용자의 모든 Row를 한 번에 가져오기
            rows = Row.objects.filter(user_id=user_id).prefetch_related(
                Prefetch(
                    'values',
                    queryset=AttributeValue.objects.select_related('attribute'),
                    to_attr='prefetched_values'
                )
            )
            
            # Row별로 속성값을 미리 계산
            row_attributes = {}
            for row in rows:
                row_attributes[row.id] = {
                    rv.attribute.name: rv.value 
                    for rv in row.prefetched_values 
                    if rv.attribute
                }
            
            for date_field in date_fields:
                # view_check가 false인 경우 스킵
                if not date_field.get('view_check', True):
                    continue
                
                attr_id = date_field['attribute']
                content_fields = date_field['content_fields']
                color = date_field.get('color', '#e5e7eb')
                
                attr = attributes.get(attr_id)
                if not attr:
                    continue
                
                # 해당 속성의 값들을 한 번에 가져오기
                attr_values = AttributeValue.objects.filter(
                    row__user_id=user_id,
                    attribute_id=attr_id
                ).select_related('row')
                
                for attr_val in attr_values:
                    if not attr_val.value:
                        continue
                    
                    # 날짜 파싱
                    dt = _parse_date_string(attr_val.value)
                    if not dt:
                        continue
                    
                    formatted_date = dt.strftime('%Y-%m-%d')
                    row_values = row_attributes.get(attr_val.row.id, {})
                    
                    # 카드 내용 (빈 값은 제외)
                    card_content = {
                        field: row_values.get(field, '') 
                        for field in content_fields 
                        if row_values.get(field, '')
                    }
                    
                    event = {
                        'id': f'{attr_val.row.id}_{attr_id}',
                        'title': row_values.get('회사명', '(회사명 없음)'),
                        'start': formatted_date,
                        'date_field_name': attr.name,
                        'date_field_color': color,
                    }
                    
                    if card_content:
                        event['content'] = card_content
                    
                    events.append(event)
        
        # 2. 커스텀 이벤트 추가
        custom_events = settings.get('custom_events', [])
        for ce in custom_events:
            color = ce.get('color')
            if not color or color in ('undefined', ''):
                color = '#e5e7eb'
            
            start = ce.get('start') or ce.get('date')
            end = ce.get('end') or ce.get('date')
            content = ce.get('content', '')
            
            event = {
                'id': f'custom_{ce.get("title")}_{start}',
                'title': ce.get('title'),
                'start': start,
                'date_field_name': '커스텀',
                'date_field_color': color,
                'is_custom': True,
            }
            
            if end:
                # FullCalendar는 end 날짜가 exclusive이므로 하루를 더해서 보내줌
                end_dt = _parse_date_string(end)
                if end_dt:
                    end_dt += timedelta(days=1)
                    event['end'] = end_dt.strftime('%Y-%m-%d')
                else:
                    event['end'] = end
            
            if content:
                event['content'] = {'내용': content}
            
            events.append(event)
        
        return JsonResponse(events, safe=False)
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=401)
    except Exception as e:
        logger.error(f"calendar_events error: {e}")
        return JsonResponse({
            'success': False,
            'error': '서버 오류가 발생했습니다.'
        }, status=500)