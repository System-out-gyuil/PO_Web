from django.shortcuts import render
from .models import DiaryEntry, Category, Region, SalesStatus, BaseAttribute, Attribute, AttributeValue, User, DropdownAttribute, Row, AttributeType
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_GET, require_http_methods
import json
import random
from types import SimpleNamespace
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from .models import DiaryEntry, Category, Region, SalesStatus, BaseAttribute, Attribute, AttributeValue, User, DropdownAttribute, Row, AttributeType
from django.db import models
# 다이어리 목록 및 작성 폼

def diary_list(request):
    user = User.objects.get(id=1)
    attributes = Attribute.objects.all().order_by('id')
    user_attributes = Attribute.objects.filter(user=user)
    attr_map = {attr.name: attr for attr in user_attributes}
    
    # 기존 단일 행 값들 제거하고, 실제 Row 데이터 가져오기
    rows = Row.objects.filter(user=user).order_by('order')
    
    # 각 행의 속성 값들을 가져오기
    rows_data = []
    for row in rows:
        row_values = {}
        for attr in user_attributes:
            attr_value = AttributeValue.objects.filter(attribute=attr, row=row).first()
            value = attr_value.value if attr_value else ''
            
            if attr.attributeType and attr.attributeType.name == 'dropdown' and value.isdigit():
                dropdown = DropdownAttribute.objects.filter(id=int(value)).first()
                if dropdown:
                    row_values[attr.name] = {'label': dropdown.option, 'color': dropdown.color}
                else:
                    row_values[attr.name] = {'label': value, 'color': ''}
            elif attr.attributeType and attr.attributeType.name == 'datetime' and value:
                # datetime 타입의 경우 날짜 포맷 적용
                try:
                    # 값이 이미 datetime 객체인지 확인
                    if isinstance(value, str):
                        # 문자열인 경우 파싱 시도
                        if 'T' in value or ' ' in value:
                            # datetime 형식
                            dt = datetime.fromisoformat(value.replace('T', ' ').split('.')[0])
                        else:
                            # date 형식
                            dt = datetime.strptime(value, '%Y-%m-%d')
                        formatted_value = dt.strftime('%Y-%m-%d')
                    else:
                        # datetime 객체인 경우
                        formatted_value = value.strftime('%Y-%m-%d')
                    row_values[attr.name] = {'label': formatted_value, 'color': ''}
                except:
                    # 파싱 실패 시 원본 값 사용
                    row_values[attr.name] = {'label': value, 'color': ''}
            else:
                row_values[attr.name] = {'label': value, 'color': ''}
        
        rows_data.append({
            'id': row.id,
            'values': row_values
        })
    
    # 칸반보드 데이터 생성
    board = []
    sales_progress_attr = Attribute.objects.filter(user=user, name='영업진행').first()
    
    if sales_progress_attr:
        # 영업진행 속성의 드롭다운 옵션들 가져오기
        dropdown_options = DropdownAttribute.objects.filter(attribute=sales_progress_attr).order_by('id')
        
        for option in dropdown_options:
            # 해당 영업진행 상태를 가진 행들 찾기
            rows = Row.objects.filter(
                user=user,
                values__attribute=sales_progress_attr,
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
                
                # entry 객체 형태로 변환 (기존 DiaryEntry와 호환)
                entry_data = {
                    'id': row.id,
                    'name': row_values.get('이름', ''),
                    'amount': row_values.get('매출', ''),
                }
                entries.append(SimpleNamespace(**entry_data))
            
            # 상태 정보를 SimpleNamespace로 변환
            status_data = {
                'id': option.id,
                'name': option.option,
                'color': option.color
            }
            
            board.append({
                'status': SimpleNamespace(**status_data),
                'entries': entries
            })

    # attributes를 list of dict로 json.dumps
    attributes_list = list(attributes.values('name', 'attributeType__name'))
    # dict -> SimpleNamespace, attributeType__name -> attributeType_name
    attributes_obj_list = [SimpleNamespace(**{k.replace('attributeType__name', 'attributeType_name'): v for k, v in d.items()}) for d in attributes_list]
    attributes_json = json.dumps(attributes_list, ensure_ascii=False)
    # dropdown 속성별 옵션 딕셔너리 생성 (Attribute 기반)
    dropdown_attrs = user_attributes.filter(attributeType__name='dropdown')
    dropdown_options = {}
    for attr in dropdown_attrs:
        options = DropdownAttribute.objects.filter(attribute=attr).values('id', 'option', 'color')
        dropdown_options[attr.name] = list(options)

    print(f"rows: {rows}")
    return render(request, 'diary/diary_list.html', {
        'attributes': attributes_obj_list,  # 템플릿 반복문용
        'attributes_json': attributes_json,  # JS용
        'dropdown_options': json.dumps(dropdown_options, ensure_ascii=False),
        'rows': rows_data,  # 실제 데이터 행들
        'board': board,  # 칸반보드 데이터
    })

@require_GET
def fu_events(request):
    events = []
    user = User.objects.get(id=1)
    
    # F/U 일정, 이름, 미팅, 영업진행 속성 가져오기
    fu_date_attr = Attribute.objects.filter(user=user, name='F/U 일정').first()
    name_attr = Attribute.objects.filter(user=user, name='이름').first()
    meeting_attr = Attribute.objects.filter(user=user, name='미팅').first()
    sales_progress_attr = Attribute.objects.filter(user=user, name='영업진행').first()
    
    print(f"F/U 일정 속성: {fu_date_attr}")
    
    if not fu_date_attr:
        print("F/U 일정 속성을 찾을 수 없습니다.")
        return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)
    
    # 모든 행을 가져와서 F/U 일정이 있는지 확인
    all_rows = Row.objects.filter(user=user)
    processed_rows = set()  # 중복 처리 방지
    
    print(f"총 행 개수: {all_rows.count()}")
    
    for row in all_rows:
        if row.id in processed_rows:
            continue
            
        # 해당 행의 F/U 일정 값 찾기
        fu_attr_value = AttributeValue.objects.filter(
            row=row,
            attribute=fu_date_attr
        ).first()
        
        if not fu_attr_value or not fu_attr_value.value:
            continue
            
        fu_date_value = fu_attr_value.value.strip() if fu_attr_value.value else ''
        
        if not fu_date_value:
            continue
            
        print(f"처리 중인 행 ID: {row.id}, F/U 일정 값: '{fu_date_value}'")
        
        # 날짜 파싱 및 유효성 검사
        try:
            if isinstance(fu_date_value, str):
                # 다양한 날짜 형식 지원
                if 'T' in fu_date_value:
                    # ISO 형식 (예: 2025-06-05T00:00:00)
                    dt = datetime.fromisoformat(fu_date_value.replace('T', ' ').split('.')[0])
                elif ' ' in fu_date_value and ':' in fu_date_value:
                    # datetime 형식 (예: 2025-06-05 14:30:00)
                    dt = datetime.strptime(fu_date_value, '%Y-%m-%d %H:%M:%S')
                elif ' ' in fu_date_value:
                    # 날짜와 시간 (예: 2025-06-05 14:30)
                    dt = datetime.strptime(fu_date_value, '%Y-%m-%d %H:%M')
                else:
                    # 날짜만 (예: 2025-06-05)
                    dt = datetime.strptime(fu_date_value, '%Y-%m-%d')
                formatted_date = dt.strftime('%Y-%m-%d')
            else:
                formatted_date = fu_date_value.strftime('%Y-%m-%d')
            print(f"  파싱된 날짜: {formatted_date}")
        except Exception as e:
            print(f"  날짜 파싱 실패 ({fu_date_value}): {e}")
            continue  # 날짜 파싱 실패 시 건너뛰기
        
        # 해당 행의 모든 속성값들 가져오기
        row_values = {}
        for rv in row.values.all():
            if rv.attribute:
                row_values[rv.attribute.name] = rv.value
        
        # 이름 가져오기
        name = row_values.get('이름', '(이름 없음)')
        
        # 미팅 날짜 가져오기
        meeting_date = row_values.get('미팅', '')
        if meeting_date:
            try:
                if isinstance(meeting_date, str):
                    if 'T' in meeting_date or ' ' in meeting_date:
                        dt = datetime.fromisoformat(meeting_date.replace('T', ' ').split('.')[0])
                    else:
                        dt = datetime.strptime(meeting_date, '%Y-%m-%d')
                    meeting_date = dt.strftime('%Y/%m/%d')
                else:
                    meeting_date = meeting_date.strftime('%Y/%m/%d')
            except:
                meeting_date = str(meeting_date)
        
        # 영업진행 상태 가져오기
        sales_progress_value = row_values.get('영업진행', '')
        status_name = ''
        status_color = '#bbb'
        
        if sales_progress_value and str(sales_progress_value).isdigit():
            dropdown = DropdownAttribute.objects.filter(
                id=int(sales_progress_value),
                attribute=sales_progress_attr
            ).first()
            if dropdown:
                status_name = dropdown.option
                status_color = dropdown.color or '#bbb'
        
        event_data = {
            'id': row.id,
            'title': name,
            'start': formatted_date,
            'meeting_date': meeting_date,
            'status_name': status_name,
            'status_color': status_color,
        }
        events.append(event_data)
        processed_rows.add(row.id)
        print(f"  이벤트 추가됨: {event_data}")
    
    print(f"최종 이벤트 개수: {len(events)}")
    return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def fu_memo(request, entry_id):
    try:
        entry = DiaryEntry.objects.get(id=entry_id)
    except DiaryEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'success': True, 'memo': entry.memo or ''})
    elif request.method == 'POST':
        memo = request.POST.get('memo', '')
        entry.memo = memo
        entry.save()
        return JsonResponse({'success': True})

def random_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])

@csrf_exempt
def category_list(request):
    if request.method == 'GET':
        return JsonResponse({'categories': list(Category.objects.values('id', 'name', 'color'))})
    elif request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '').strip()
        if name:
            if not color:
                color = random_color()
            cat, created = Category.objects.get_or_create(name=name, defaults={'color': color})
            if not created and not cat.color:
                cat.color = color
                cat.save()
            return JsonResponse({'id': cat.id, 'name': cat.name, 'color': cat.color, 'created': created})
        return JsonResponse({'error': 'No name'}, status=400)
    elif request.method == 'DELETE':
        id = request.GET.get('id')
        Category.objects.filter(id=id).delete()
        return JsonResponse({'success': True})
    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        color = request.GET.get('color', '').strip()
        cat = Category.objects.filter(id=id).first()
        updated = False
        if cat:
            if name:
                cat.name = name
                updated = True
            if color:
                cat.color = color
                updated = True
            if updated:
                cat.save()
                return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def region_list(request):
    if request.method == 'GET':
        return JsonResponse({'regions': list(Region.objects.values('id', 'name'))})
    elif request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            reg, created = Region.objects.get_or_create(name=name)
            return JsonResponse({'id': reg.id, 'name': reg.name, 'created': created})
        return JsonResponse({'error': 'No name'}, status=400)
    elif request.method == 'DELETE':
        id = request.GET.get('id')
        Region.objects.filter(id=id).delete()
        return JsonResponse({'success': True})
    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        reg = Region.objects.filter(id=id).first()
        if reg and name:
            reg.name = name
            reg.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def create_entry(request):
    if request.method == 'POST':
        data = {field: request.POST.get(field, '') for field in [
            'name', 'subregion', 'address', 'manager', 'phone', 'email',
            'status', 'possibility', 'amount']}
        for date_field in ['ta_date', 'meeting_date', 'fu_date']:
            value = request.POST.get(date_field)
            data[date_field] = value if value else None
        cat_val = request.POST.get('category')
        reg_val = request.POST.get('region')
        status_val = request.POST.get('status')
        # category 처리
        if cat_val:
            if cat_val.isdigit():
                data['category'] = Category.objects.filter(id=cat_val).first()
            else:
                data['category'], _ = Category.objects.get_or_create(name=cat_val)
        else:
            data['category'] = None
        # region 처리
        if reg_val:
            if reg_val.isdigit():
                data['region'] = Region.objects.filter(id=reg_val).first()
            else:
                data['region'], _ = Region.objects.get_or_create(name=reg_val)
        else:
            data['region'] = None
        # status 처리 (추가)
        if status_val:
            if status_val.isdigit():
                data['status'] = SalesStatus.objects.filter(id=status_val).first()
            else:
                data['status'], _ = SalesStatus.objects.get_or_create(name=status_val)
        else:
            data['status'] = None
        # order 값 지정: 가장 큰 order+1
        max_order = DiaryEntry.objects.aggregate(max_order=models.Max('order'))['max_order']
        data['order'] = (max_order + 1) if max_order is not None else 0
        entry = DiaryEntry.objects.create(**data)
        return JsonResponse({'success': True, 'id': entry.id})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def reorder_entries(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('order', [])
            for idx, row_id in enumerate(ids):
                Row.objects.filter(id=row_id).update(order=idx)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def status_list(request):
    if request.method == 'GET':
        return JsonResponse({'statuses': list(SalesStatus.objects.values('id', 'name', 'color'))})
    elif request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            color = request.POST.get('color', '').strip()
            if not color:
                color = random_color()
            status, created = SalesStatus.objects.get_or_create(name=name, defaults={'color': color})
            if not created and not status.color:
                status.color = color
                status.save()
            return JsonResponse({'id': status.id, 'name': status.name, 'color': status.color, 'created': created})
        return JsonResponse({'error': 'No name'}, status=400)
    elif request.method == 'DELETE':
        id = request.GET.get('id')
        SalesStatus.objects.filter(id=id).delete()
        return JsonResponse({'success': True})
    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        color = request.GET.get('color', '').strip()
        status = SalesStatus.objects.filter(id=id).first()
        if status:
            updated = False
            if name:
                status.name = name
                updated = True
            if color:
                status.color = color
                updated = True
            if updated:
                status.save()
                return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def board_view(request):
    user = User.objects.get(id=1)  # 현재 사용자
    
    # "영업진행" 속성 가져오기
    sales_progress_attr = Attribute.objects.filter(user=user, name='영업진행').first()
    
    if not sales_progress_attr:
        # 영업진행 속성이 없으면 빈 보드 반환
        return render(request, 'diary/diary_list.html', {'board': [], 'statuses': []})
    
    # 영업진행 속성의 드롭다운 옵션들 가져오기
    dropdown_options = DropdownAttribute.objects.filter(attribute=sales_progress_attr).order_by('id')
    
    board = []
    for option in dropdown_options:
        # 해당 영업진행 상태를 가진 행들 찾기
        rows = Row.objects.filter(
            user=user,
            values__attribute=sales_progress_attr,
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
            
            # entry 객체 형태로 변환 (기존 DiaryEntry와 호환)
            entry_data = {
                'id': row.id,
                'name': row_values.get('이름', ''),
                'amount': row_values.get('매출', ''),
            }
            entries.append(SimpleNamespace(**entry_data))
        
        # 상태 정보를 SimpleNamespace로 변환
        status_data = {
            'id': option.id,
            'name': option.option,
            'color': option.color
        }
        
        board.append({
            'status': SimpleNamespace(**status_data),
            'entries': entries
        })
    
    return render(request, 'diary/diary_list.html', {'board': board, 'statuses': dropdown_options})

@csrf_exempt
def update_entry(request):
    if request.method == 'POST':
        row_id = request.POST.get('id')
        field = request.POST.get('field')
        value = request.POST.get('value')
        print(field, value)
        if not row_id or not field or row_id == 'null':
            return JsonResponse({'success': False, 'error': 'Missing id or field'})
            
        try:
            from .models import Row
            row = Row.objects.get(id=row_id)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid row ID'})
            
        user = User.objects.get(id=1)
        try:
            attr = Attribute.objects.get(name=field)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid attribute'})
        
        attr_type = attr.attributeType.name if attr.attributeType else ''
        attribute, _ = Attribute.objects.get_or_create(
            name=attr.name,
            user=user,
            defaults={'attributeType': attr.attributeType}
        )
        # Dropdown 처리
        if attr_type == 'dropdown':
            try:
                dropdown = DropdownAttribute.objects.get(id=int(value), attribute=attr)
                value_to_save = str(dropdown.id)
            except (DropdownAttribute.DoesNotExist, ValueError):
                return JsonResponse({'success': False, 'error': 'Invalid dropdown value'})
        else:
            value_to_save = value
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=attribute,
            defaults={'value': value_to_save}
        )
        if not created:
            attr_value.value = value_to_save
            attr_value.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def create_new_row(request):
    """새 행 생성을 위한 엔드포인트"""
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value', '')
        
        if not field:
            return JsonResponse({'success': False, 'error': 'Missing field'})
            
        user = User.objects.get(id=1)
        
        # 새 Row 생성 (임시로 빈 Row)
        from .models import Row
        max_order = Row.objects.aggregate(max_order=models.Max('order'))['max_order']
        new_order = (max_order + 1) if max_order is not None else 0
        
        new_row = Row.objects.create(order=new_order, user=user)
        
        # 첫 번째 필드 값 설정
        try:
            attr = Attribute.objects.get(name=field)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid attribute'})
            
        attr_type = attr.attributeType.name if attr.attributeType else ''
        attribute, _ = Attribute.objects.get_or_create(
            name=attr.name,
            user=user,
            defaults={'attributeType': attr.attributeType}
        )
        
        # Dropdown 처리
        if attr_type == 'dropdown':
            try:
                dropdown = DropdownAttribute.objects.get(id=int(value), attribute=attr)
                value_to_save = str(dropdown.id)
            except (DropdownAttribute.DoesNotExist, ValueError):
                return JsonResponse({'success': False, 'error': 'Invalid dropdown value'})
        else:
            value_to_save = value
            
        # 새 Row에 AttributeValue 생성
        AttributeValue.objects.create(
            row=new_row,
            attribute=attribute,
            value=value_to_save
        )
        
        return JsonResponse({'success': True, 'id': new_row.id})
        
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def update_row_field(request):
    """기존 행의 필드 업데이트"""
    if request.method == 'POST':
        row_id = request.POST.get('id')
        field = request.POST.get('field')
        value = request.POST.get('value', '')
        
        if not row_id or not field:
            return JsonResponse({'success': False, 'error': 'Missing id or field'})
            
        try:
            row = Row.objects.get(id=row_id)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found'})
            
        user = User.objects.get(id=1)
        
        try:
            attr = Attribute.objects.get(name=field)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid attribute'})
            
        attr_type = attr.attributeType.name if attr.attributeType else ''
        attribute, _ = Attribute.objects.get_or_create(
            name=attr.name,
            user=user,
            defaults={'attributeType': attr.attributeType}
        )
        
        # Dropdown 처리
        if attr_type == 'dropdown':
            try:
                dropdown = DropdownAttribute.objects.get(id=int(value), attribute=attr)
                value_to_save = str(dropdown.id)
            except (DropdownAttribute.DoesNotExist, ValueError):
                return JsonResponse({'success': False, 'error': 'Invalid dropdown value'})
        else:
            value_to_save = value
            
        # 해당 Row의 AttributeValue 업데이트 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=attribute,
            defaults={'value': value_to_save}
        )
        if not created:
            attr_value.value = value_to_save
            attr_value.save()
            
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def dropdown_options(request):
    field = request.GET.get('field')
    print(field)
    if not field:
        return JsonResponse({'error': 'No field'}, status=400)
    try:
        attr = Attribute.objects.get(name=field)
    except Attribute.DoesNotExist:
        return JsonResponse({'error': 'Invalid field'}, status=400)

    if request.method == 'GET':
        options = list(DropdownAttribute.objects.filter(attribute=attr).values('id', 'option', 'color'))
        return JsonResponse({'options': options})

    elif request.method == 'POST':
        option = request.POST.get('name', '').strip()
        color = request.POST.get('color', '').strip() or None
        if option:
            if color:
                dropdown, created = DropdownAttribute.objects.get_or_create(attribute=attr, option=option, defaults={'color': color})
            else:
                dropdown, created = DropdownAttribute.objects.get_or_create(attribute=attr, option=option)
            return JsonResponse({'id': dropdown.id, 'option': dropdown.option, 'color': dropdown.color, 'created': created})
        return JsonResponse({'error': 'No option'}, status=400)

    elif request.method == 'PUT':
        id = request.GET.get('id')
        name = request.GET.get('name', '').strip()
        color = request.GET.get('color', '').strip()
        dropdown = DropdownAttribute.objects.filter(id=id, attribute=attr).first()
        if dropdown:
            if name:
                dropdown.option = name
            if color:
                dropdown.color = color
            dropdown.save()
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid'}, status=400)

    elif request.method == 'DELETE':
        id = request.GET.get('id')
        DropdownAttribute.objects.filter(id=id, attribute=attr).delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt  
def add_attribute(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        attr_type = request.POST.get('type', '').strip()
        
        if not name:
            return JsonResponse({'success': False, 'error': '속성명이 필요합니다.'})
        
        if not attr_type:
            return JsonResponse({'success': False, 'error': '속성 타입이 필요합니다.'})
        
        # 속성명 중복 확인
        if Attribute.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': '이미 존재하는 속성명입니다.'})
        
        try:
            # 사용자 가져오기
            user = User.objects.get(id=1)  # 임시로 user id=1 사용
            
            # AttributeType 가져오기 또는 생성
            attribute_type, _ = AttributeType.objects.get_or_create(name=attr_type)
            
            # 새 속성 생성
            attribute = Attribute.objects.create(
                name=name,
                user=user,
                attributeType=attribute_type
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

@require_GET
def get_row_details(request, row_id):
    try:
        user = User.objects.get(id=1)
        row = Row.objects.get(id=row_id, user=user)
        
        # 행의 모든 속성값들 가져오기
        row_data = {}
        for attr_value in row.values.all():
            if attr_value.attribute:
                attr_name = attr_value.attribute.name
                value = attr_value.value
                
                # 드롭다운 타입인 경우 텍스트 값으로 변환
                if attr_value.attribute.attributeType and attr_value.attribute.attributeType.name == 'dropdown':
                    if value and value.isdigit():
                        dropdown = DropdownAttribute.objects.filter(
                            id=int(value),
                            attribute=attr_value.attribute
                        ).first()
                        if dropdown:
                            value = dropdown.option
                
                row_data[attr_name] = value
        
        return JsonResponse({
            'success': True,
            'row_data': row_data,
            'row_id': row.id
        })
        
    except Row.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 데이터를 찾을 수 없습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
def debug_fu_data(request):
    """F/U 일정 데이터 디버깅용 뷰"""
    user = User.objects.get(id=1)
    fu_date_attr = Attribute.objects.filter(user=user, name='F/U 일정').first()
    
    if not fu_date_attr:
        return JsonResponse({'error': 'F/U 일정 속성을 찾을 수 없습니다.'})
    
    # 모든 F/U 일정 AttributeValue 가져오기
    fu_values = AttributeValue.objects.filter(attribute=fu_date_attr)
    
    debug_data = []
    for attr_value in fu_values:
        debug_data.append({
            'row_id': attr_value.row.id,
            'value': attr_value.value,
            'is_null': attr_value.value is None,
            'is_empty': attr_value.value == '',
            'value_length': len(attr_value.value) if attr_value.value else 0,
            'value_repr': repr(attr_value.value)
        })
    
    return JsonResponse({
        'fu_date_attr_id': fu_date_attr.id,
        'total_fu_values': len(debug_data),
        'fu_values': debug_data
    }, indent=2)

@require_GET
def get_user_attributes(request):
    """사용자의 속성 목록을 반환하는 뷰"""
    try:
        user = User.objects.get(id=1)
        attributes = Attribute.objects.filter(user=user).order_by('id')
        
        attributes_data = []
        for attr in attributes:
            attributes_data.append({
                'name': attr.name,
                'attributeType': attr.attributeType.name if attr.attributeType else 'text'
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