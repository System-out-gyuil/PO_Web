from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Attribute, AttributeValue, User, Row, CalendarSettings
import json
from datetime import datetime, timedelta

@require_GET
def get_datetime_attributes(request):
    """datetime 타입의 속성 목록을 반환하는 API"""
    try:
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        datetime_attributes = Attribute.objects.filter(
            user=user, 
            attributeType__name='datetime'
        ).order_by('name')
        
        attributes_data = []
        for attr in datetime_attributes:
            attributes_data.append({
                'id': attr.id,
                'name': attr.name,
                'type': 'datetime'
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

@require_GET
def get_calendar_settings(request):
     
    user_id = request.session.get('diary_member_id')

    user = User.objects.get(id=user_id)
    calendar_settings = CalendarSettings.objects.filter(user=user).first()
    if calendar_settings:
        return JsonResponse({'success': True, 'settings': calendar_settings.settings})
    # 기본값
    return JsonResponse({'success': True, 'settings': {'date_fields': [], 'custom_events': []}})


@csrf_exempt
def save_calendar_settings(request):
    if request.method == 'POST':
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        settings = data.get('settings', {})
        calendar_settings, _ = CalendarSettings.objects.get_or_create(user=user)
        calendar_settings.settings = settings
        calendar_settings.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@require_GET
def calendar_events(request):
     
    user_id = request.session.get('diary_member_id')

    user = User.objects.get(id=user_id)
    calendar_settings = CalendarSettings.objects.filter(user=user).first()
    settings = calendar_settings.settings if calendar_settings else {}
    events = []
    # 1. 기준 날짜 필드별로 Row에서 카드 생성
    for date_field in settings.get('date_fields', []):
        attr_id = date_field['attribute']
        content_fields = date_field['content_fields']
        color = date_field.get('color', '#e5e7eb')
        
        # view_check 필드 확인 - false인 경우 이벤트 생성하지 않음
        view_check = date_field.get('view_check', True)  # 기본값은 True
        if view_check is False:
            continue
            
        attr = Attribute.objects.filter(id=attr_id, user=user).first()
        if not attr: continue
        for row in Row.objects.filter(user=user):
            date_val = AttributeValue.objects.filter(row=row, attribute=attr).first()
            if not date_val or not date_val.value: continue
            # 날짜 파싱
            try:
                v = date_val.value.strip()
                if 'T' in v:
                    dt = datetime.fromisoformat(v.replace('T', ' ').split('.')[0])
                elif ' ' in v and ':' in v:
                    dt = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                elif ' ' in v:
                    dt = datetime.strptime(v, '%Y-%m-%d %H:%M')
                else:
                    dt = datetime.strptime(v, '%Y-%m-%d')
                formatted_date = dt.strftime('%Y-%m-%d')
            except:
                continue
            # 카드 내용 (빈 값은 제외)
            row_values = {rv.attribute.name: rv.value for rv in row.values.all() if rv.attribute}
            card_content = {field: row_values.get(field, '') for field in content_fields if row_values.get(field, '')}
            event = {
                'id': f'{row.id}_{attr_id}',
                'title': row_values.get('회사명', '(회사명 없음)'),
                'start': formatted_date,
                'date_field_name': attr.name,
                'date_field_color': color,
            }
            if card_content:
                event['content'] = card_content
            events.append(event)
    # 2. 커스텀 이벤트 추가
    for ce in settings.get('custom_events', []):
        color = ce.get('color')
        if not color or color == 'undefined' or color == '':
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
            try:
                end_date = datetime.strptime(end, '%Y-%m-%d')
                end_date += timedelta(days=1)
                event['end'] = end_date.strftime('%Y-%m-%d')
            except:
                # 날짜 파싱 실패시 원본 값 사용
                event['end'] = end
        if content:
            event['content'] = {'내용': content}
        events.append(event)
    return JsonResponse(events, safe=False)