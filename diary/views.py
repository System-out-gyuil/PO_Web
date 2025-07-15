from django.shortcuts import render
from .models import DiaryEntry, Category, Region, SalesStatus, BaseAttribute, Attribute, AttributeValue, User, DropdownAttribute, Row, AttributeType, CalendarSettings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_GET, require_http_methods
import json
import random
from types import SimpleNamespace
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from .models import DiaryEntry, Category, Region, SalesStatus, BaseAttribute, Attribute, AttributeValue, User, DropdownAttribute, Row, AttributeType
from django.db import models
import boto3
from django.conf import settings
import uuid
import os
from botocore.exceptions import ClientError
from google.cloud import speech
from langchain_openai import ChatOpenAI
import io
from django.http import JsonResponse
from config import GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_APPLICATION_CREDENTIALS2, NAVER_CLOVA_SPEECH_SECRET_KEY, NAVER_CLOVA_SPEECH_INVOKE_URL, OPEN_AI_API_KEY
import requests
import logging
from django.contrib.auth.decorators import login_required
from .funding_calculator import FundingCalculator
from board.models import BizInfo
from django.db.models import Q, Max
import re
from datetime import date
import time
import json
import re
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
import os
import boto3
from botocore.exceptions import ClientError
import uuid
import requests
import base64
import hashlib
import hmac
import time
from urllib.parse import quote
import mimetypes
from django.conf import settings
from django.db import transaction
import pandas as pd
from openpyxl import load_workbook
from django.http import Http404

logger = logging.getLogger(__name__)

# 다이어리 목록 및 작성 폼

def diary_list(request):
    host = request.get_host()

    user = User.objects.get(id=1)
    
    # detail 필터링 추가: 기본적으로 detail=False인 속성만 표시
    show_detail = request.GET.get('detail', '0') == '1'  # detail=1이면 상세 속성도 표시
    
    # 속성 필터링: detail 값과 view_select 값에 따라 필터링
    if show_detail:
        attributes = Attribute.objects.filter(view_select=True).order_by('sort_order', 'id')  # view_select=True인 속성만 표시
        user_attributes = Attribute.objects.filter(user=user, view_select=True).order_by('sort_order', 'id')  # view_select=True인 속성만 표시
    else:
        attributes = Attribute.objects.filter(detail=False, view_select=True).order_by('sort_order', 'id')  # detail=False이고 view_select=True인 속성만 표시
        user_attributes = Attribute.objects.filter(user=user, detail=False, view_select=True).order_by('sort_order', 'id')  # detail=False이고 view_select=True인 속성만 표시
    
    # 행 데이터는 모든 행을 가져옴 (필터링은 속성 레벨에서 처리)
    # 쿼리 최적화: select_related와 prefetch_related 적용
    rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
        'values__attribute__attributeType',
        'values__attribute__dropdown_attributes'
    ).order_by('order')
    
    # 각 행의 속성 값들을 가져오기 (필터링된 속성만)
    rows_data = []
    for row in rows:
        row_values = {}
        for attr in user_attributes:  # 이미 필터링된 속성들만 사용
            # prefetch된 데이터에서 찾기
            attr_value = None
            for value in row.values.all():
                if value.attribute_id == attr.id:
                    attr_value = value
                    break
            
            value = attr_value.value if attr_value else ''
            
            if attr.name == '매출' or '매출' in attr.name:
                numeric_value = parse_korean_currency(value)
                row_values[attr.name] = {
                    'label': value,  # 화면 표시용(한글 단위 등)
                    'value': numeric_value,  # 실제 숫자값
                    'color': ''
                }
            elif attr.attributeType and attr.attributeType.name == 'dropdown' and value.isdigit():
                # prefetch된 dropdown 데이터에서 찾기
                dropdown = None
                for dropdown_attr in attr.dropdown_attributes.all():
                    if dropdown_attr.id == int(value):
                        dropdown = dropdown_attr
                        break
                
                if dropdown:
                    row_values[attr.name] = {
                        'label': dropdown.option, 
                        'color': dropdown.color,
                        'raw_value': value,
                        'selected_options': [{'id': dropdown.id, 'label': dropdown.option, 'color': dropdown.color}]
                    }
                else:
                    row_values[attr.name] = {
                        'label': value, 
                        'color': '',
                        'raw_value': value,
                        'selected_options': []
                    }
            elif attr.attributeType and attr.attributeType.name == 'dropdown' and value.startswith('[') and value.endswith(']'):
                # 다중선택(dropdown) 필드인 경우
                try:
                    selected_ids = json.loads(value)
                    selected_options = []
                    for dropdown_attr in attr.dropdown_attributes.all():
                        if dropdown_attr.id in selected_ids:
                            selected_options.append({
                                'id': dropdown_attr.id,
                                'label': dropdown_attr.option,
                                'color': dropdown_attr.color
                            })
                    
                    
                    if selected_options:
                        # 첫 번째 옵션의 색상을 기본 색상으로 사용
                        default_color = selected_options[0]['color']
                        row_values[attr.name] = {
                            'label': ', '.join([opt['label'] for opt in selected_options]),
                            'color': default_color,
                            'raw_value': value,
                            'selected_options': selected_options,
                            'multi_select': True
                        }
                    else:
                        row_values[attr.name] = {
                            'label': '선택 없음',
                            'color': '',
                            'raw_value': value,
                            'selected_options': [],
                            'multi_select': True
                        }
                except json.JSONDecodeError as e:
                    print(f"  JSON 파싱 실패: {e}")
                    row_values[attr.name] = {
                        'label': value,
                        'color': '',
                        'raw_value': value,
                        'selected_options': [],
                        'multi_select': True
                    }
            elif attr.attributeType and attr.attributeType.name == 'file' and value:
                # 파일 타입인 경우
                file_info = json.loads(value)
                original_filename = file_info.get('original_filename', '파일')
                
                row_values[attr.name] = {
                    'type': 'file',
                    'label': original_filename,
                    'download_url': file_info.get('download_url', ''),
                    'file_size': file_info.get('file_size', 0),
                    'content_type': file_info.get('content_type', ''),
                    'original_filename': original_filename
                }
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
    
    # 칸반보드용 dropdown 속성들 가져오기 (필터링된 속성 중에서)
    dropdown_attributes = user_attributes.filter(attributeType__name='dropdown').order_by('-assential', 'name')
    
    # 칸반보드 데이터 생성 - 기본적으로 '영업진행' 속성 사용, 없으면 첫 번째 dropdown 속성 사용
    board = []
    selected_kanban_attr = request.GET.get('kanban_attr', '영업진행')
    kanban_attr = user_attributes.filter(name=selected_kanban_attr, attributeType__name='dropdown').first()
    
    if not kanban_attr and dropdown_attributes.exists():
        kanban_attr = dropdown_attributes.first()
        selected_kanban_attr = kanban_attr.name
    
    if kanban_attr:
        # 선택된 속성의 드롭다운 옵션들 가져오기 (prefetch된 데이터 활용)
        dropdown_options = kanban_attr.dropdown_attributes.all().order_by('order', 'id')
        
        for option in dropdown_options:
            # 해당 상태를 가진 행들 찾기 (쿼리 최적화)
            rows_with_status = Row.objects.filter(
                user=user,
                values__attribute=kanban_attr,
                values__value=str(option.id)
            ).prefetch_related(
                'values__attribute',
                'values__attribute__dropdown_attributes'
            ).order_by('order', 'id')
            
            # 각 행의 데이터를 entry 형태로 변환
            entries = []
            for row in rows_with_status:
                # 행의 속성값들 가져오기 (prefetch된 데이터 활용)
                row_values = {}
                for attr_value in row.values.all():
                    if attr_value.attribute:
                        row_values[attr_value.attribute.name] = attr_value.value
                
                # entry 객체 형태로 변환 (기존 DiaryEntry와 호환)
                entry_data = {
                    'id': row.id,
                    'name': row_values.get('회사명', ''),
                }
                entries.append(entry_data)
            
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
    attributes_list = list(attributes.values('id', 'name', 'attributeType__name', 'assential'))
    # dict -> SimpleNamespace, attributeType__name -> attributeType_name
    attributes_obj_list = [SimpleNamespace(**{k.replace('attributeType__name', 'attributeType_name'): v for k, v in d.items()}) for d in attributes_list]
    attributes_json = json.dumps(attributes_list, ensure_ascii=False)
    
    # dropdown 속성별 옵션 딕셔너리 생성 (필터링된 Attribute 기반)
    dropdown_attrs = user_attributes.filter(attributeType__name='dropdown')
    dropdown_options_dict = {}
    for attr in dropdown_attrs:
        # prefetch된 데이터 활용
        options = list(attr.dropdown_attributes.values('id', 'option', 'color'))
        dropdown_options_dict[attr.name] = options

    # dropdown 속성들을 JSON으로 전달 (필터링된 것만)
    dropdown_attributes_json = json.dumps([
        {'name': attr.name, 'id': attr.id} 
        for attr in dropdown_attributes
    ], ensure_ascii=False)

    print(f"rows: {rows}")
    return render(request, 'diary/diary_list.html', {
        'attributes': attributes_obj_list,  # 템플릿 반복문용
        'attributes_json': attributes_json,  # JS용
        'dropdown_options': json.dumps(dropdown_options_dict, ensure_ascii=False),
        'dropdown_attributes': dropdown_attributes,  # 칸반 필터용
        'dropdown_attributes_json': dropdown_attributes_json,  # JS용
        'selected_kanban_attr': selected_kanban_attr,  # 현재 선택된 칸반 속성
        'rows': rows_data,  # 실제 데이터 행들
        'board': board,  # 칸반보드 데이터
    })

@require_GET
def fu_events(request):
    events = []
    user = User.objects.get(id=1)
    
    # F/U 일정, 회사명, 미팅, 영업진행 속성 가져오기 (쿼리 최적화)
    fu_date_attr = Attribute.objects.filter(user=user, name='F/U 일정').select_related('attributeType').first()
    name_attr = Attribute.objects.filter(user=user, name='회사명').select_related('attributeType').first()
    meeting_attr = Attribute.objects.filter(user=user, name='미팅').select_related('attributeType').first()
    sales_progress_attr = Attribute.objects.filter(user=user, name='영업진행').select_related('attributeType').first()
    
    print(f"F/U 일정 속성: {fu_date_attr}")
    
    if not fu_date_attr:
        print("F/U 일정 속성을 찾을 수 없습니다.")
        return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)
    
    # 모든 행을 가져와서 F/U 일정이 있는지 확인 (쿼리 최적화)
    all_rows = Row.objects.filter(user=user).prefetch_related(
        'values__attribute',
        'values__attribute__attributeType',
        'values__attribute__dropdown_attributes'
    )
    processed_rows = set()  # 중복 처리 방지
    
    print(f"총 행 개수: {all_rows.count()}")
    
    for row in all_rows:
        if row.id in processed_rows:
            continue
            
        # 해당 행의 F/U 일정 값 찾기 (prefetch된 데이터 활용)
        fu_attr_value = None
        for attr_value in row.values.all():
            if attr_value.attribute_id == fu_date_attr.id:
                fu_attr_value = attr_value
                break
        
        if not fu_attr_value or not fu_attr_value.value:
            continue
            
        fu_date_value = fu_attr_value.value.strip() if fu_attr_value.value else ''
        
        if not fu_date_value:
            continue
            
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
        except Exception as e:
            print(f"  날짜 파싱 실패 ({fu_date_value}): {e}")
            continue  # 날짜 파싱 실패 시 건너뛰기
        
        # 해당 행의 모든 속성값들 가져오기 (prefetch된 데이터 활용)
        row_values = {}
        for rv in row.values.all():
            if rv.attribute:
                row_values[rv.attribute.name] = rv.value
        
        # 회사명 가져오기
        name = row_values.get('회사명', '(회사명 없음)')
        
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
        
        # 영업진행 상태 가져오기 (prefetch된 데이터 활용)
        sales_progress_value = row_values.get('영업진행', '')
        status_name = ''
        status_color = '#bbb'
        
        if sales_progress_value and str(sales_progress_value).isdigit():
            # prefetch된 dropdown 데이터에서 찾기
            dropdown = None
            if sales_progress_attr:
                for dropdown_attr in sales_progress_attr.dropdown_attributes.all():
                    if dropdown_attr.id == int(sales_progress_value):
                        dropdown = dropdown_attr
                        break
            
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
    
    # "영업진행" 속성 가져오기 (쿼리 최적화)
    sales_progress_attr = Attribute.objects.filter(user=user, name='영업진행').select_related('attributeType').first()
    
    if not sales_progress_attr:
        # 영업진행 속성이 없으면 빈 보드 반환
        return render(request, 'diary/diary_list.html', {'board': [], 'statuses': []})
    
    # 영업진행 속성의 드롭다운 옵션들 가져오기 (prefetch된 데이터 활용)
    dropdown_options = sales_progress_attr.dropdown_attributes.all().order_by('id')
    
    board = []
    for option in dropdown_options:
        # 해당 영업진행 상태를 가진 행들 찾기 (쿼리 최적화)
        rows = Row.objects.filter(
            user=user,
            values__attribute=sales_progress_attr,
            values__value=str(option.id)
        ).prefetch_related(
            'values__attribute',
            'values__attribute__dropdown_attributes'
        ).order_by('order', 'id')
        
        # 각 행의 데이터를 entry 형태로 변환
        entries = []
        for row in rows:
            # 행의 속성값들 가져오기 (prefetch된 데이터 활용)
            row_values = {}
            for attr_value in row.values.all():
                if attr_value.attribute:
                    row_values[attr_value.attribute.name] = attr_value.value
            
            # entry 객체 형태로 변환 (기존 DiaryEntry와 호환)
            entry_data = {
                'id': row.id,
                'name': row_values.get('회사명', ''),
            }
            entries.append(entry_data)
        
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
            # 사용자 ID를 1로 고정
            user = User.objects.get(id=1)
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid row ID'})
            
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
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_entry) ===")
            print(f"속성 '{field}'의 cascade 값: {attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {value_to_save}")
            
            synced_count = sync_cascade_attributes(row_id, field, value_to_save)
            if synced_count > 0:
                print(f"Cascade 동기화 완료: {field} 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_entry) ===")
        else:
            print(f"속성 '{field}'의 cascade 값: {attr.cascade} - 동기화하지 않음")
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def create_new_row(request):
    """새 행 생성을 위한 엔드포인트"""
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value', '')
        status_field = request.POST.get('status_field')
        status_value = request.POST.get('status_value')
        
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
        
        # 상태 필드가 있으면 추가로 생성
        if status_field and status_value:
            try:
                status_attr = Attribute.objects.get(name=status_field, user=user)
                status_attr_type = status_attr.attributeType.name if status_attr.attributeType else ''
                if status_attr_type == 'dropdown':
                    # status_value가 id인지 option명인지 구분
                    if status_value.isdigit():
                        status_value_to_save = status_value
                    else:
                        dropdown_option = DropdownAttribute.objects.get(attribute=status_attr, option=status_value)
                        status_value_to_save = str(dropdown_option.id)
                else:
                    status_value_to_save = status_value
                AttributeValue.objects.create(
                    row=new_row,
                    attribute=status_attr,
                    value=status_value_to_save
                )
            except Exception as e:
                print(f"상태 필드 생성 오류: {e}")
        
        return JsonResponse({'success': True, 'id': new_row.id})
        
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def update_row_field(request):
    if request.method == 'POST':
        print("===========update_row_field")
        try:
            # JSON 형 field식과 form-urlencoded 형식 모두 지원
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                row_id = data.get('row_id')
                field_name = data.get('field_name')
                value = data.get('value')
            else:
                # form-urlencoded 형식 처리
                row_id = request.POST.get('id')  # 기존 코드와 호환성 유지
                field_name = request.POST.get('field')
                value = request.POST.get('value')
            
            if not row_id or not field_name:
                return JsonResponse({'success': False, 'error': 'row_id와 field_name이 필요합니다'})
            
            # 사용자와 행 조회
            user = User.objects.get(id=1)
            row = Row.objects.get(id=row_id, user=user)
            
            # 매출 필드 특별 처리
            if field_name == '매출' or '매출' in field_name:
                # 억/천만 단위로 전송된 경우 처리
                if isinstance(value, dict) and 'eok' in value and 'cheonman' in value:
                    value = parse_sales_amount(value['eok'], value['cheonman'])
                else:
                    # 기존 방식 (숫자 문자열)
                    value = parse_korean_currency(value)
            
            # 개업년월 필드 특별 처리
            elif field_name == '개업년월':
                # JSON 형태로 저장된 데이터는 그대로 유지
                if isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                # 문자열이 JSON 형태인지 확인
                elif isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    # 이미 JSON 형태면 그대로 사용
                    pass
                else:
                    # 일반 문자열인 경우 JSON으로 변환
                    value = json.dumps({'opening_date': value}, ensure_ascii=False)
            
            # 속성 조회
            try:
                attr = Attribute.objects.get(name=field_name, user=user)
            except Attribute.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'속성 {field_name}을 찾을 수 없습니다'})
            
            # 드롭다운 타입인 경우 특별 처리
            if attr.attributeType and attr.attributeType.name == 'dropdown':
                print(f"Dropdown 필드 처리 - {attr.name}: value='{value}', isdigit: {value.isdigit() if value else False}")
                
                if value.isdigit():
                    # 단일 선택
                    print(f"  단일 선택 처리")
                    value_to_save = value
                elif value.startswith('[') and value.endswith(']'):
                    # 다중선택(dropdown) 필드인 경우
                    print(f"다중선택 처리 - {attr.name}: value='{value}'")
                    try:
                        selected_ids = json.loads(value)
                        print(f"  JSON 파싱 성공: {selected_ids}")
                        value_to_save = value  # JSON 배열 형태로 저장
                    except json.JSONDecodeError as e:
                        print(f"  JSON 파싱 실패: {e}")
                        value_to_save = value
                else:
                    # 빈 값이거나 다른 형태
                    print(f"  빈 값 또는 다른 형태: '{value}'")
                    value_to_save = value
            else:
                value_to_save = str(value)
            
            # AttributeValue 조회 또는 생성
            attr_value, created = AttributeValue.objects.get_or_create(
                row=row, 
                attribute=attr,
                defaults={'value': value_to_save}
            )
            
            if not created:
                attr_value.value = value_to_save
                attr_value.save()
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if attr.cascade:
                print(f"=== Cascade 동기화 시작 ===")
                print(f"속성 '{field_name}'의 cascade 값: {attr.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {value_to_save}")
                
                synced_count = sync_cascade_attributes(row_id, field_name, value_to_save)
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: {field_name} 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 ===")
            else:
                print(f"속성 '{field_name}'의 cascade 값: {attr.cascade} - 동기화하지 않음")
            
            return JsonResponse({'success': True})
            
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다'})
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '속성을 찾을 수 없습니다'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})

@csrf_exempt
def dropdown_options(request):
    # GET과 POST 모두에서 field 파라미터 확인
    field = request.GET.get('field') or request.POST.get('field')
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
        # POST body에서 먼저 확인, 없으면 URL 파라미터에서 확인
        option = request.POST.get('name', '').strip() or request.GET.get('name', '').strip()
        color = request.POST.get('color', '').strip() or request.GET.get('color', '').strip() or None
        if option:
            if color:
                dropdown, created = DropdownAttribute.objects.get_or_create(attribute=attr, option=option, defaults={'color': color})
            else:
                dropdown, created = DropdownAttribute.objects.get_or_create(attribute=attr, option=option)
            return JsonResponse({'success': True, 'id': dropdown.id, 'option': dropdown.option, 'color': dropdown.color, 'created': created})
        return JsonResponse({'error': 'No option'}, status=400)

    elif request.method == 'PUT':
        # PUT 요청의 body 파싱
        import urllib.parse
        body_data = urllib.parse.parse_qs(request.body.decode('utf-8'))
        
        id = request.GET.get('id') or body_data.get('id', [None])[0]
        name = request.GET.get('name', '').strip() or body_data.get('name', [''])[0].strip()
        color = request.GET.get('color', '').strip() or body_data.get('color', [''])[0].strip()
        
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
        # DELETE 요청의 body 파싱
        import urllib.parse
        body_data = urllib.parse.parse_qs(request.body.decode('utf-8'))
        
        id = request.GET.get('id') or body_data.get('id', [None])[0]
        
        # 삭제할 옵션 찾기
        dropdown = DropdownAttribute.objects.filter(id=id, attribute=attr).first()
        if not dropdown:
            return JsonResponse({'error': 'Option not found'}, status=404)
        
        # 해당 옵션을 사용하는 모든 AttributeValue 찾기
        affected_values = AttributeValue.objects.filter(attribute=attr)
        
        # 각 AttributeValue에서 삭제된 옵션 ID 제거
        for attr_value in affected_values:
            if attr_value.value:
                try:
                    # JSON 형태로 저장된 다중선택 값인지 확인
                    parsed = json.loads(attr_value.value)
                    if isinstance(parsed, list):
                        # 다중선택 값에서 삭제된 옵션 ID 제거
                        if int(id) in parsed:
                            parsed.remove(int(id))
                            attr_value.value = json.dumps(parsed) if parsed else ''
                            attr_value.save()
                    elif str(parsed) == str(id):
                        # 단일 선택 값이 삭제된 옵션과 일치하는 경우
                        attr_value.value = ''
                        attr_value.save()
                except (json.JSONDecodeError, ValueError):
                    # JSON이 아닌 경우 단일 값으로 처리
                    if str(attr_value.value) == str(id):
                        attr_value.value = ''
                        attr_value.save()
        
        # DropdownAttribute 삭제
        dropdown.delete()
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
            
            # 현재 최대 sort_order 구하기
            max_sort_order = Attribute.objects.aggregate(Max('sort_order'))['sort_order__max']
            next_sort_order = (max_sort_order or 0) + 1
            
            # 새 속성 생성
            attribute = Attribute.objects.create(
                name=name,
                user=user,
                attributeType=attribute_type,
                sort_order=next_sort_order,
                view_select=True
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
        # 쿼리 최적화: select_related와 prefetch_related 적용
        row = Row.objects.filter(id=row_id, user=user).select_related('user').prefetch_related(
            'values__attribute__attributeType',
            'values__attribute__dropdown_attributes'
        ).first()
        
        if not row:
            return JsonResponse({
                'success': False,
                'error': '해당 데이터를 찾을 수 없습니다.'
            })
        
        # 행의 모든 속성값들 가져오기 (prefetch된 데이터 활용)
        row_data = {}
        for attr_value in row.values.all():
            if attr_value.attribute:
                attr_name = attr_value.attribute.name
                value = attr_value.value
                
                # 특별한 필드들 처리
                if attr_name == '개업년월':
                    # 개업년월 데이터 파싱
                    business_data = parse_business_data(value)
                    if business_data:
                        # 개업년수 계산
                        business_years = calculate_business_years(
                            business_data.get('opening_date'),
                            business_data.get('years_ago')
                        )
                        if business_years is not None:
                            business_data['business_years'] = business_years
                        row_data[attr_name] = business_data
                    else:
                        row_data[attr_name] = {}
                elif attr_name == '매출' or '매출' in attr_name:
                    # 매출 데이터는 숫자로 변환
                    try:
                        numeric_value = int(value) if value else 0
                        row_data[attr_name] = numeric_value
                    except (ValueError, TypeError):
                        row_data[attr_name] = 0
                else:
                    # 드롭다운 타입인 경우 텍스트 값으로 변환 (prefetch된 데이터 활용)
                    if attr_value.attribute.attributeType and attr_value.attribute.attributeType.name == 'dropdown':
                        if value and value.isdigit():
                            # prefetch된 dropdown 데이터에서 찾기
                            dropdown = None
                            for dropdown_attr in attr_value.attribute.dropdown_attributes.all():
                                if dropdown_attr.id == int(value):
                                    dropdown = dropdown_attr
                                    break
                            if dropdown:
                                value = dropdown.option
                            else:
                                # dropdown 옵션을 찾지 못한 경우 원본 값 유지
                                value = value
                        elif value and value.startswith('[') and value.endswith(']'):
                            # 리스트 형태의 값인 경우 (예: [27]) 첫 번째 값만 추출
                            try:
                                import ast
                                list_value = ast.literal_eval(value)
                                if isinstance(list_value, list) and len(list_value) > 0:
                                    dropdown_id = list_value[0]
                                    # prefetch된 dropdown 데이터에서 찾기
                                    dropdown = None
                                    for dropdown_attr in attr_value.attribute.dropdown_attributes.all():
                                        if dropdown_attr.id == dropdown_id:
                                            dropdown = dropdown_attr
                                            break
                                    if dropdown:
                                        value = dropdown.option
                                    else:
                                        value = str(dropdown_id)  # 옵션을 찾지 못한 경우 ID 반환
                                else:
                                    value = value  # 빈 리스트인 경우 원본 값 유지
                            except (ValueError, SyntaxError):
                                value = value  # 파싱 실패 시 원본 값 유지
                    # 파일 타입인 경우 JSON 파싱하여 객체로 반환
                    elif attr_value.attribute.attributeType and attr_value.attribute.attributeType.name == 'file':
                        if value:
                            try:
                                value = json.loads(value)  # JSON 문자열을 객체로 변환
                            except (json.JSONDecodeError, TypeError):
                                value = None  # 파싱 실패 시 None
                    
                    row_data[attr_name] = value
        
        return JsonResponse({
            'success': True,
            'row_data': row_data,
            'row_id': row.id
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
    """사용자의 속성 목록을 반환하는 API"""
    try:
        user = User.objects.get(id=1)
        attributes = Attribute.objects.filter(user=user).order_by('-assential', 'id')  # 필수 속성 먼저, 그 다음 id 순
        
        attributes_data = []
        for attr in attributes:
            attr_data = {
                'id': attr.id,
                'name': attr.name,
                'type': attr.attributeType.name if attr.attributeType else 'text',
                'essential': attr.assential  # essential 정보 추가
            }
            attributes_data.append(attr_data)
        
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
def get_kanban_data(request):
    """특정 dropdown 속성에 대한 칸반보드 데이터를 반환하는 API"""
    try:
        user = User.objects.get(id=1)
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
        dropdown_options = DropdownAttribute.objects.filter(attribute=kanban_attr).order_by('id')
        
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
def upload_file(request):
    """파일 업로드 및 S3 저장 (여러 파일 지원)"""
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        field_name = request.POST.get('field_name')
        uploaded_file = request.FILES.get('file')
        
        print(f"=== 파일 업로드 시작 ===")
        print(f"Row ID: {row_id}")
        print(f"Field Name: {field_name}")
        
        if not row_id or not field_name:
            return JsonResponse({
                'success': False,
                'error': 'Row ID와 Field Name이 필요합니다.'
            })
        
        if uploaded_file:
            print(f"파일명: {uploaded_file.name}")
            print(f"파일 크기: {uploaded_file.size} bytes")
            print(f"파일 타입: {uploaded_file.content_type}")
            
            try:
                # Row와 Attribute 가져오기
                user = User.objects.get(id=1)
                row = Row.objects.get(id=row_id, user=user)
                attribute = Attribute.objects.get(name=field_name, user=user)
                
                # 속성이 file 타입인지 확인
                if not attribute.attributeType or attribute.attributeType.name != 'file':
                    return JsonResponse({
                        'success': False,
                        'error': '파일 타입 속성이 아닙니다.'
                    })
                
                # S3 클라이언트 생성
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # 파일명 생성 (중복 방지를 위해 UUID 사용)
                file_extension = os.path.splitext(uploaded_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                s3_key = f"{settings.AWS_LOCATION}/{unique_filename}"
                
                print(f"S3 업로드 시작...")
                print(f"버킷: {settings.AWS_STORAGE_BUCKET_NAME}")
                print(f"키: {s3_key}")
                
                # S3에 파일 업로드
                s3_client.upload_fileobj(
                    uploaded_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': uploaded_file.content_type,
                        'ContentDisposition': f'attachment; filename="{uploaded_file.name}"'
                    }
                )
                
                # 다운로드 URL 생성
                download_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                
                # 서명된 다운로드 URL 생성 (24시간 유효)
                try:
                    signed_download_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': s3_key
                        },
                        ExpiresIn=300  # 5분
                    )
                    print(f"서명된 다운로드 URL 생성 성공 (5분 유효)")
                except Exception as e:
                    print(f"서명된 URL 생성 실패: {e}")
                    signed_download_url = download_url
                
                # 서명된 미리보기 URL 생성 (24시간 유효, inline으로 설정)
                try:
                    signed_preview_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': s3_key,
                            'ResponseContentDisposition': 'inline'
                        },
                        ExpiresIn=300  # 5분
                    )
                    print(f"서명된 미리보기 URL 생성 성공 (5분 유효)")
                except Exception as e:
                    print(f"서명된 미리보기 URL 생성 실패: {e}")
                    signed_preview_url = download_url
                
                print(f"S3 업로드 성공:")
                print(f"  원본 파일명: {uploaded_file.name}")
                print(f"  S3 파일명: {unique_filename}")
                print(f"  다운로드 URL: {download_url}")
                print(f"  서명된 다운로드 URL: {signed_download_url}")
                print(f"  서명된 미리보기 URL: {signed_preview_url}")
                
                # 파일 타입 결정 (확장자와 content_type 기반)
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                content_type = uploaded_file.content_type or ''
                
                # 파일 타입 분류
                file_type = 'file'  # 기본값
                if content_type.startswith('image/'):
                    file_type = 'img'
                elif content_type == 'application/pdf':
                    file_type = 'pdf'
                elif content_type.startswith('audio/'):
                    file_type = 'audio'
                elif content_type.startswith('video/'):
                    file_type = 'video'
                elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    file_type = 'img'
                elif file_extension == '.pdf':
                    file_type = 'pdf'
                elif file_extension in ['.mp3', '.wav', '.ogg', '.m4a']:
                    file_type = 'audio'
                elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
                    file_type = 'video'
                
                # 새 파일 정보
                new_file_data = {
                    'original_filename': uploaded_file.name,
                    'stored_filename': unique_filename,
                    's3_key': s3_key,
                    'download_url': signed_download_url,
                    'preview_url': signed_preview_url,
                    'public_url': download_url,
                    'file_size': uploaded_file.size,
                    'content_type': uploaded_file.content_type,
                    'type': file_type,  # 파일 타입 추가
                    'upload_time': datetime.now().isoformat()  # 업로드 시간 추가
                }
                
                # AttributeValue에서 기존 파일 정보 가져오기
                attr_value, created = AttributeValue.objects.get_or_create(
                    row=row,
                    attribute=attribute,
                    defaults={'value': '[]'}  # 빈 배열로 초기화
                )
                
                # 기존 파일 목록 파싱
                try:
                    if attr_value.value and attr_value.value.strip():
                        existing_files = json.loads(attr_value.value)
                        if not isinstance(existing_files, list):
                            # 기존이 단일 파일인 경우 배열로 변환
                            existing_files = [existing_files] if existing_files else []
                    else:
                        existing_files = []
                except (json.JSONDecodeError, TypeError):
                    existing_files = []
                
                # 새 파일을 배열에 추가
                existing_files.append(new_file_data)
                
                # 업데이트된 파일 목록을 데이터베이스에 저장
                attr_value.value = json.dumps(existing_files, ensure_ascii=False)
                attr_value.save()
                
                print(f"데이터베이스에 파일 정보 저장 완료 (총 {len(existing_files)}개 파일)")
                
                return JsonResponse({
                    'success': True,
                    'message': f'파일 "{uploaded_file.name}"이 성공적으로 업로드되었습니다.',
                    'file_info': new_file_data,
                    'total_files': len(existing_files)
                })
                
            except Row.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '해당 행을 찾을 수 없습니다.'
                })
            except Attribute.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '해당 속성을 찾을 수 없습니다.'
                })
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                print(f"=== S3 업로드 실패 ===")
                print(f"에러 코드: {error_code}")
                print(f"에러 메시지: {error_message}")
                
                return JsonResponse({
                    'success': False,
                    'error': f'S3 업로드 실패: {error_message}'
                })
                
            except Exception as e:
                print(f"=== 예상치 못한 오류 ===")
                print(f"오류: {str(e)}")
                
                return JsonResponse({
                    'success': False,
                    'error': f'파일 업로드 중 오류 발생: {str(e)}'
                })
        else:
            print("업로드된 파일이 없습니다.")
            return JsonResponse({
                'success': False,
                'error': '업로드된 파일이 없습니다.'
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'POST 요청만 허용됩니다.'
        })

@csrf_exempt
def delete_file(request):
    """파일 삭제 (여러 파일 지원)"""
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        field_name = request.POST.get('field_name')
        file_index = request.POST.get('file_index')  # 삭제할 파일의 인덱스
        
        print(f"Received Row ID: {row_id}")
        print(f"Received Field Name: {field_name}")
        print(f"Received File Index: {file_index}")
        print(f"File Index Type: {type(file_index)}")
        print(f"All POST data: {dict(request.POST)}")
        
        # 필수 파라미터 검증
        if not row_id or not field_name:
            return JsonResponse({
                'success': False,
                'error': 'row_id와 field_name이 필요합니다.'
            })
        
        try:
            # 사용자 ID를 1로 고정
            user = User.objects.get(id=1)
            
            # Row와 Attribute 조회
            row = Row.objects.get(id=row_id, user=user)
            attribute = Attribute.objects.get(name=field_name, user=user)
            
            # 파일 타입 속성인지 확인
            if attribute.attributeType.name != 'file':
                return JsonResponse({
                    'success': False,
                    'error': '파일 타입이 아닙니다.'
                })
            
            # AttributeValue 조회
            try:
                attribute_value = AttributeValue.objects.get(row=row, attribute=attribute)
                
                # 파일 정보 파싱
                if attribute_value.value:
                    try:
                        files_data = json.loads(attribute_value.value)
                        print(f"Original files_data: {files_data}")
                        
                        # 단일 파일인 경우 배열로 변환
                        if not isinstance(files_data, list):
                            files_data = [files_data] if files_data else []
                        
                        print(f"Processed files_data: {files_data}")
                        print(f"Number of files: {len(files_data)}")
                        
                        if not files_data:
                            return JsonResponse({
                                'success': False,
                                'error': '삭제할 파일이 없습니다.'
                            })
                        
                        # file_index가 제공된 경우 특정 파일 삭제
                        if file_index is not None:
                            try:
                                file_index = int(file_index)
                                print(f"Converted file_index: {file_index}")
                                
                                if file_index < 0 or file_index >= len(files_data):
                                    return JsonResponse({
                                        'success': False,
                                        'error': f'유효하지 않은 파일 인덱스입니다. (인덱스: {file_index}, 파일 수: {len(files_data)})'
                                    })
                                
                                # 삭제할 파일 정보
                                file_to_delete = files_data[file_index]
                                print(f"File to delete: {file_to_delete}")
                                s3_key = file_to_delete.get('s3_key')
                                original_filename = file_to_delete.get('original_filename', 'unknown')
                                
                                # S3에서 파일 삭제
                                if s3_key:
                                    try:
                                        s3_client = boto3.client(
                                            's3',
                                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                            region_name=settings.AWS_S3_REGION_NAME
                                        )
                                        
                                        s3_client.delete_object(
                                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                            Key=s3_key
                                        )
                                        print(f"S3에서 파일 삭제 성공: {s3_key}")
                                        
                                    except ClientError as e:
                                        print(f"S3 파일 삭제 실패: {e}")
                                        # S3 삭제 실패해도 계속 진행
                                
                                # 배열에서 해당 파일 제거
                                files_data.pop(file_index)
                                print(f"Files after deletion: {files_data}")
                                
                                # 남은 파일이 있으면 업데이트, 없으면 삭제
                                if files_data:
                                    attribute_value.value = json.dumps(files_data, ensure_ascii=False)
                                    attribute_value.save()
                                    print(f"Updated attribute_value: {attribute_value.value}")
                                else:
                                    attribute_value.delete()
                                    print("AttributeValue deleted")
                                
                                print(f"파일 삭제 성공: {original_filename}")
                                
                                return JsonResponse({
                                    'success': True,
                                    'message': f'파일 "{original_filename}"이(가) 성공적으로 삭제되었습니다.',
                                    'remaining_files': len(files_data)
                                })
                                
                            except ValueError as e:
                                print(f"ValueError converting file_index: {e}")
                                return JsonResponse({
                                    'success': False,
                                    'error': '유효하지 않은 파일 인덱스입니다.'
                                })
                        else:
                            print("No file_index provided, deleting all files")
                            # file_index가 없으면 모든 파일 삭제 (기존 동작)
                            for file_data in files_data:
                                s3_key = file_data.get('s3_key')
                                if s3_key:
                                    try:
                                        s3_client = boto3.client(
                                            's3',
                                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                            region_name=settings.AWS_S3_REGION_NAME
                                        )
                                        
                                        s3_client.delete_object(
                                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                            Key=s3_key
                                        )
                                        print(f"S3에서 파일 삭제 성공: {s3_key}")
                                        
                                    except ClientError as e:
                                        print(f"S3 파일 삭제 실패: {e}")
                            
                            # AttributeValue 삭제
                            attribute_value.delete()
                            print(f"모든 파일 삭제 성공")
                            
                            return JsonResponse({
                                'success': True,
                                'message': '모든 파일이 성공적으로 삭제되었습니다.'
                            })
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        return JsonResponse({
                            'success': False,
                            'error': '파일 정보를 파싱할 수 없습니다.'
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': '파일 정보가 없습니다.'
                    })
                    
            except AttributeValue.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '삭제할 파일이 없습니다.'
                })
                
        except Row.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 행을 찾을 수 없습니다.'
            })
        except Attribute.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 속성을 찾을 수 없습니다.'
            })
        except Exception as e:
            print(f"파일 삭제 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'POST 요청만 허용됩니다.'
    })

@require_GET
def download_file(request, row_id, field_name):
    """S3에 저장된 파일을 다운로드하는 뷰"""
    try:
        # 사용자 ID를 1로 고정 (이미 import된 User 모델 사용)
        user = User.objects.get(id=1)
        
        # Row와 Attribute 조회
        row = Row.objects.get(id=row_id, user=user)
        attribute = Attribute.objects.get(name=field_name, user=user)
        
        # AttributeValue 조회
        try:
            attribute_value = AttributeValue.objects.get(row=row, attribute=attribute)
            
            if attribute_value.value:
                try:
                    file_info = json.loads(attribute_value.value)
                    s3_key = file_info.get('s3_key')
                    original_filename = file_info.get('original_filename', 'download')
                    existing_download_url = file_info.get('download_url')
                    
                    if s3_key:
                        # 항상 새로운 서명된 다운로드 URL 생성 (1시간 유효)
                        s3_client = boto3.client(
                            's3',
                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME
                        )
                        
                        try:
                            signed_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={
                                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                    'Key': s3_key
                                },
                                ExpiresIn=300  # 5분
                            )
                            
                            print(f"새로운 서명된 다운로드 URL 생성: {signed_url}")
                            
                            # 리다이렉트로 다운로드
                            from django.http import HttpResponseRedirect
                            return HttpResponseRedirect(signed_url)
                            
                        except Exception as e:
                            print(f"서명된 URL 생성 실패: {e}")
                            # 서명된 URL 생성 실패 시 기존 URL 사용
                            if existing_download_url:
                                from django.http import HttpResponseRedirect
                                return HttpResponseRedirect(existing_download_url)
                            else:
                                return JsonResponse({
                                    'success': False,
                                    'error': '다운로드 URL 생성에 실패했습니다.'
                                })
                        
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'S3 키가 없습니다.'
                        })
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': '파일 정보를 파싱할 수 없습니다.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '파일 정보가 없습니다.'
                })
                
        except AttributeValue.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '파일이 존재하지 않습니다.'
            })
                
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '사용자를 찾을 수 없습니다.'
        })
    except Row.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 행을 찾을 수 없습니다.'
        })
    except Attribute.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 속성을 찾을 수 없습니다.'
        })
    except Exception as e:
        print(f"파일 다운로드 중 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
        })

class ClovaSpeechClient:
    # Clova Speech invoke URL
    invoke_url = NAVER_CLOVA_SPEECH_INVOKE_URL
    # Clova Speech secret key
    secret = NAVER_CLOVA_SPEECH_SECRET_KEY

    def req_url(self, url, completion, callback=None, userdata=None, \
    	forbiddens=None, boostings=None, wordAlignment=True, \
        	fullText=True, diarization=None, sed=None):
        request_body = {
            'url': url,
            'language': 'ko-KR',
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'forbiddens': forbiddens,
            'boostings': boostings,
            'diarization': diarization,
            'sed': sed,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'Content-Type': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        return requests.post(headers=headers,
                             url=self.invoke_url + '/recognizer/url',
                             data=json.dumps(request_body).encode('UTF-8'))

    def req_object_storage(self, data_key, completion, callback=None,
    	userdata=None, forbiddens=None, boostings=None,wordAlignment=True,
        	fullText=True, diarization=None, sed=None):
        request_body = {
            'dataKey': data_key,
            'language': 'ko-KR',
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'forbiddens': forbiddens,
            'boostings': boostings,
            'diarization': diarization,
            'sed': sed,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'Content-Type': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        return requests.post(headers=headers,
                             url=self.invoke_url + '/recognizer/object-storage',
                             data=json.dumps(request_body).encode('UTF-8'))

    def req_upload(self, file, completion, callback=None, userdata=None,
    	forbiddens=None, boostings=None, wordAlignment=True,
        	fullText=True, diarization=None, sed=None):
        request_body = {
            'language': 'ko-KR',
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'forbiddens': forbiddens,
            'boostings': boostings,
            'diarization': diarization,
            'sed': sed,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        print(json.dumps(request_body, ensure_ascii=False).encode('UTF-8'))
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, \
            			ensure_ascii=False).encode('UTF-8'), \
                        		'application/json')
        }
        response = requests.post(headers=headers, url=self.invoke_url \
        			+ '/recognizer/upload', files=files)
        return response


@csrf_exempt
@require_http_methods(["POST"])
def upload_audio_file(request):
    """음성파일을 업로드하고 변환된 텍스트를 저장하는 뷰"""
    
    if request.method == 'POST':
        audio_file = request.FILES.get('audio_file')
        row_id = request.POST.get('row_id')
        field_name = request.POST.get('field_name', '음성파일')

        print(f"Received audio file: {audio_file}")
        print(f"Received row ID: {row_id}")
        print(f"Received field name: {field_name}")
        
        # 필수 파라미터 검증
        if not audio_file:
            return JsonResponse({
                'success': False,
                'error': '음성파일이 필요합니다.'
            })
        
        if not row_id:
            return JsonResponse({
                'success': False,
                'error': 'row_id가 필요합니다.'
            })
        
        # 파일 크기 제한 (100MB)
        max_file_size = 1024 * 1024 * 1024  # 100MB
        if audio_file.size > max_file_size:
            return JsonResponse({
                'success': False,
                'error': '파일 크기가 1GB를 초과합니다.'
            })
        
        # 오디오 파일 검증
        if not audio_file.content_type.startswith('audio/'):
            return JsonResponse({
                'success': False,
                'error': '오디오 파일만 업로드 가능합니다.'
            })
        
        try:
            # 사용자 ID를 1로 고정 (이미 import된 User 모델 사용)
            user = User.objects.get(id=1)
            
            # Row 존재 여부 확인
            row = Row.objects.get(id=row_id, user=user)
            
            # 음성파일 속성 조회 (변환된 텍스트 속성은 더 이상 사용하지 않음)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            
            # 오늘 날짜 생성
            from datetime import date
            today = date.today().strftime('%y.%m.%d')
            
            # Clova Speech-to-Text API 호출
            converted_text = ""
            gpt_summary = ""
            try:
                # 임시 파일로 저장 (Clova Speech는 파일 업로드 방식)
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as temp_file:
                    for chunk in audio_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                # Clova Speech API 호출
                clova_client = ClovaSpeechClient()
                response = clova_client.req_upload(file=temp_file_path, completion='sync')
                result = response.json()
                
                # 화자별 인식 결과 segment 추출
                segments = result.get('segments', [])
                speaker_segments = []
                converted_text = ''

                for segment in segments:
                    speaker_label = segment['speaker']['label']
                    text = segment['text']
                    speaker_segments.append({'start': segment['start'], 'end': segment['end'], 'speaker': speaker_label, 'text': text})

                for speaker_segment in speaker_segments:
                    start_mil = speaker_segment['start']
                    end_mil = speaker_segment['end']
                    
                    # Convert milliseconds to minutes and seconds
                    def ms_to_min_sec(milliseconds):
                        if milliseconds == 0:
                            return 0, 0
                        
                        total_seconds = milliseconds / 1000
                        minutes = int(total_seconds // 60)
                        seconds = int(total_seconds % 60)
                        return minutes, seconds
                    
                    def format_time(minutes, seconds):
                        if minutes == 0:
                            return f"{seconds}초"
                        else:
                            return f"{minutes}분 {seconds}초"
                    
                    start_min, start_sec = ms_to_min_sec(start_mil)
                    end_min, end_sec = ms_to_min_sec(end_mil)
                    
                    start_time_str = format_time(start_min, start_sec)
                    end_time_str = format_time(end_min, end_sec)
                
                    speaker_label = speaker_segment['speaker']
                    text = speaker_segment['text']

                    converted_text += f'Speaker {speaker_label}({start_time_str}~): {text} \n'
                
                # GPT 요약 생성
                llm = ChatOpenAI(
                    temperature=0,
                    model_name='gpt-4o-mini',
                    openai_api_key=OPEN_AI_API_KEY
                )

                user_input = "담당자와 고객사가 대한 통화한 내용이야. 각자 언급한 내용을 정리하고, 전체적인 소통내용을 정리해줘. 그리고 고객사의 심리상태를 간단하게 설명해줘. "

                texts = converted_text + user_input

                response = llm.invoke(texts)
                # 다양한 종류의 공백 문자를 제거하는 강력한 정리
                import re
                gpt_summary = response.content.replace("**", "").replace("#", "")
                # 모든 종류의 공백 문자 제거 (공백, 탭, 개행 등)
                gpt_summary = re.sub(r'^\s+', '', gpt_summary)  # 앞쪽 공백 제거
                gpt_summary = re.sub(r'\s+$', '', gpt_summary)  # 뒤쪽 공백 제거
                gpt_summary = re.sub(r'\n\s*\n', '\n\n', gpt_summary)  # 연속된 빈 줄 정리
                print("[GPT 응답 원본]:", gpt_summary)
                
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                    
            except Exception as stt_error:
                print(f"Clova STT API 오류: {stt_error}")
                # 임시 파일이 있다면 삭제
                try:
                    if 'temp_file_path' in locals():
                        os.unlink(temp_file_path)
                except:
                    pass

            # S3에 파일 업로드
            try:
                # 파일 포인터를 다시 처음으로 이동 (S3 업로드용)
                audio_file.seek(0)
                
                # 고유한 파일명 생성
                file_extension = os.path.splitext(audio_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                s3_key = f"audio_files/{unique_filename}"
                
                # S3 클라이언트 생성
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # S3에 파일 업로드
                s3_client.upload_fileobj(
                    audio_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': audio_file.content_type,
                        'ContentDisposition': f'attachment; filename="{audio_file.name}"'
                    }
                )
                
                # 다운로드 URL 생성
                download_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                
                # 서명된 다운로드 URL 생성 (24시간 유효)
                try:
                    signed_download_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': s3_key
                        },
                        ExpiresIn=300  # 5분
                    )
                    print(f"서명된 다운로드 URL 생성 성공 (5분 유효)")
                except Exception as e:
                    print(f"서명된 URL 생성 실패: {e}")
                    signed_download_url = download_url
                
                # 서명된 미리보기 URL 생성 (24시간 유효, inline으로 설정)
                try:
                    signed_preview_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': s3_key,
                            'ResponseContentDisposition': 'inline'
                        },
                        ExpiresIn=300  # 5분
                    )
                    print(f"서명된 미리보기 URL 생성 성공 (5분 유효)")
                except Exception as e:
                    print(f"서명된 미리보기 URL 생성 실패: {e}")
                    signed_preview_url = download_url
                
                print(f"S3 업로드 성공:")
                print(f"  원본 파일명: {audio_file.name}")
                print(f"  S3 파일명: {unique_filename}")
                print(f"  다운로드 URL: {download_url}")
                print(f"  서명된 다운로드 URL: {signed_download_url}")
                print(f"  서명된 미리보기 URL: {signed_preview_url}")
                
            except Exception as e:
                print(f"S3 업로드 실패: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'파일 업로드 실패: {str(e)}'
                })
            
            # 기존 음성파일 데이터 가져오기 또는 빈 dict 생성
            existing_attr_value = AttributeValue.objects.filter(
                row=row,
                attribute=audio_attribute
            ).first()
            
            if existing_attr_value and existing_attr_value.value:
                try:
                    existing_data = json.loads(existing_attr_value.value)
                except (json.JSONDecodeError, TypeError):
                    existing_data = {}
            else:
                existing_data = {}
            
            # 기존 파일들의 order 값을 1씩 증가시키기 (새 파일이 맨 위에 오도록)
            for date_key in existing_data:
                date_data = existing_data[date_key]
                
                # date_data가 딕셔너리인 경우 (기존 구조)
                if isinstance(date_data, dict):
                    for file_id_key in date_data:
                        file_info = date_data[file_id_key]
                        if isinstance(file_info, dict):
                            current_order = file_info.get('order', 0)
                            file_info['order'] = current_order + 1
                
                # date_data가 리스트인 경우 (새로운 구조)
                elif isinstance(date_data, list):
                    for file_info in date_data:
                        if isinstance(file_info, dict):
                            current_order = file_info.get('order', 0)
                            file_info['order'] = current_order + 1
            
            # 고유한 파일 ID 생성 (시간 포함)
            from datetime import datetime
            file_id = datetime.now().strftime('%H%M%S')  # HHMMSS 형식
            
            # 새로운 파일 데이터 생성 (order를 0으로 설정하여 맨 위에 표시)
            new_file_data = {
                'original_filename': audio_file.name,
                'stored_filename': unique_filename,
                's3_key': s3_key,
                'download_url': signed_download_url,
                'preview_url': signed_preview_url,
                'public_url': download_url,
                'file_size': audio_file.size,
                'content_type': audio_file.content_type,
                'converted_text': converted_text,
                'gpt_summary': gpt_summary,
                'upload_time': datetime.now().strftime('%H:%M:%S'),
                'order': 0,  # 새로 업로드된 파일은 항상 맨 위에
                'type': 'audio'  # 타입 구분을 위한 필드 추가
            }
            
            # 날짜별로 데이터 구조화
            if 'data' not in existing_data:
                existing_data['data'] = {}
            new_file_data['upload_date'] = today
            existing_data['data'][file_id] = new_file_data
            
            # 음성파일 속성에 전체 데이터 저장
            if existing_attr_value:
                existing_attr_value.value = json.dumps(existing_data, ensure_ascii=False)
                existing_attr_value.save()
            else:
                AttributeValue.objects.create(
                    row=row,
                    attribute=audio_attribute,
                    value=json.dumps(existing_data, ensure_ascii=False)
                )
            
            print(f"Row ID {row_id}의 음성파일 데이터 저장 완료 (날짜: {today})")
            
            return JsonResponse({
                'success': True,
                'date': today,
                'file_id': file_id,
                'converted_text': converted_text,
                'gpt_summary': gpt_summary,
                'file_info': {
                    'original_filename': audio_file.name,
                    'download_url': signed_download_url,
                    'preview_url': signed_preview_url,
                    'file_size': audio_file.size,
                    'content_type': audio_file.content_type,
                    'upload_time': new_file_data['upload_time']
                },
                'message': '음성파일 업로드 및 변환이 완료되었습니다.'
            })
                
        except Row.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 행을 찾을 수 없습니다.'
            })
        except Exception as e:
            print(f"음성파일 처리 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'처리 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'POST 요청만 허용됩니다.'
    })

@require_GET
def get_audio_files_by_date(request):
    """특정 행의 날짜별 음성파일 데이터를 조회하는 API"""
    try:
        row_id = request.GET.get('row_id')
        
        if not row_id:
            return JsonResponse({
                'success': False,
                'error': 'row_id가 필요합니다.'
            })
        
        # 사용자 ID를 1로 고정
        user = User.objects.get(id=1)
        
        # Row와 음성파일 속성 조회
        row = Row.objects.get(id=row_id, user=user)
        audio_attribute = Attribute.objects.get(name='음성파일', user=user)
        
        # 음성파일 데이터 조회
        attr_value = AttributeValue.objects.filter(
            row=row,
            attribute=audio_attribute
        ).first()
        
        if attr_value and attr_value.value:
            try:
                audio_data = json.loads(attr_value.value)
                
                # 날짜별로 정리된 데이터 반환
                formatted_data = {}
                for date_key, files in audio_data.items():
                    formatted_data[date_key] = []
                    for file_id, file_info in files.items():
                        formatted_data[date_key].append({
                            'file_id': file_id,
                            'original_filename': file_info.get('original_filename', ''),
                            'converted_text': file_info.get('converted_text', ''),
                            'gpt_summary': file_info.get('gpt_summary', ''),
                            'download_url': file_info.get('download_url', ''),
                            'preview_url': file_info.get('preview_url', ''),
                            'file_size': file_info.get('file_size', 0),
                            'upload_time': file_info.get('upload_time', ''),
                            'content_type': file_info.get('content_type', '')
                        })
                
                return JsonResponse({
                    'success': True,
                    'audio_data': formatted_data
                })
                
            except (json.JSONDecodeError, TypeError):
                return JsonResponse({
                    'success': True,
                    'audio_data': {}
                })
        else:
            return JsonResponse({
                'success': True,
                'audio_data': {}
            })
            
    except Row.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 행을 찾을 수 없습니다.'
        })
    except Attribute.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '음성파일 속성을 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"오디오 파일 조회 오류: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'오디오 파일 조회 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def delete_audio_file(request):
    """특정 날짜의 특정 음성파일 삭제"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 메서드만 허용됩니다.'})
    
    try:
        row_id = request.POST.get('row_id')
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        
        if not all([row_id, date, file_id]):
            return JsonResponse({
                'success': False,
                'error': 'row_id, date, file_id가 모두 필요합니다.'
            })
        
        # 사용자 및 Row 조회
        user = User.objects.get(id=1)
        row = Row.objects.get(id=row_id, user=user)
        
        # 음성파일 속성 조회
        audio_attribute = Attribute.objects.get(name='음성파일', user=user)
        
        # 기존 AttributeValue 조회
        try:
            attr_value = AttributeValue.objects.get(row=row, attribute=audio_attribute)
            current_data = json.loads(attr_value.value) if attr_value.value else {}
        except AttributeValue.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 데이터를 찾을 수 없습니다.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '음성파일 데이터 형식이 올바르지 않습니다.'})
        
        # 해당 날짜와 파일 ID 확인
        if date not in current_data:
            return JsonResponse({'success': False, 'error': f'{date} 날짜 데이터를 찾을 수 없습니다.'})
        
        if file_id not in current_data[date]:
            return JsonResponse({'success': False, 'error': f'파일 ID {file_id}를 찾을 수 없습니다.'})
        
        # S3에서 파일 삭제 시도
        file_info = current_data[date][file_id]
        try:
            if 'stored_filename' in file_info:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                delete_response = s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f"audio_files/{file_info['stored_filename']}"
                )
                logger.info(f"S3 파일 삭제 완료: {file_info['stored_filename']}")
        except Exception as e:
            logger.warning(f"S3 파일 삭제 실패 (계속 진행): {str(e)}")
        
        # 데이터에서 해당 파일 제거
        del current_data[date][file_id]
        
        # 해당 날짜에 다른 파일이 없으면 날짜 자체도 제거
        if not current_data[date]:
            del current_data[date]
        
        # 업데이트된 데이터 저장
        if current_data:
            attr_value.value = json.dumps(current_data, ensure_ascii=False)
            attr_value.save()
        else:
            # 모든 음성파일이 삭제된 경우
            attr_value.value = ''
            attr_value.save()
        
        logger.info(f"음성파일 삭제 완료 - Row: {row_id}, Date: {date}, File: {file_id}")
        
        return JsonResponse({
            'success': True,
            'message': '음성파일이 성공적으로 삭제되었습니다.',
            'remaining_files': len(current_data)
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
    except Row.DoesNotExist:
        return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
    except Attribute.DoesNotExist:
        return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
    except Exception as e:
        logger.error(f"음성파일 삭제 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'음성파일 삭제 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def update_audio_text(request):
    """
    음성파일의 변환된 텍스트를 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # 파라미터 검증
        row_id = request.POST.get('row_id')
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        converted_text = request.POST.get('converted_text', '')
        
        if not all([row_id, date, file_id]):
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attribute = Attribute.objects.get(user=user, name='음성파일')
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=audio_attribute,
            defaults={'value': '{}'}
        )
        
        # 기존 데이터 파싱
        try:
            audio_data = json.loads(attr_value.value) if attr_value.value else {}
        except json.JSONDecodeError:
            audio_data = {}
        
        # 해당 날짜의 파일 데이터 찾기 및 업데이트
        if file_id in audio_data.get('data', {}):
            audio_data['data'][file_id]['converted_text'] = converted_text
            
            # 데이터베이스에 저장
            attr_value.value = json.dumps(audio_data, ensure_ascii=False)
            attr_value.save()
            
            logger.info(f"음성파일 텍스트 업데이트 성공 - Row ID: {row_id}, Date: {date}, File ID: {file_id}")
            
            return JsonResponse({
                'success': True,
                'message': '변환된 텍스트가 성공적으로 업데이트되었습니다.'
            })
        else:
            return JsonResponse({'success': False, 'error': '해당 음성파일을 찾을 수 없습니다.'})
            
    except Exception as e:
        logger.error(f"음성파일 텍스트 업데이트 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': f'서버 오류: {str(e)}'})

@csrf_exempt
def update_audio_memo(request):
    """음성파일 메모 업데이트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '허용되지 않은 메소드입니다.'})
    
    try:
        # 파라미터 가져오기
        row_id = request.POST.get('row_id')
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        memo = request.POST.get('memo', '')
        
        if not all([row_id, date, file_id]):
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 정보 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attr = Attribute.objects.get(name='음성파일')
            audio_attr_value, created = AttributeValue.objects.get_or_create(
                row=row,
                attribute=audio_attr,
                defaults={'value': '{}'}
            )
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        
        # 기존 음성파일 데이터 파싱
        try:
            audio_data = json.loads(audio_attr_value.value) if audio_attr_value.value else {}
        except (json.JSONDecodeError, TypeError):
            audio_data = {}
        
        # 해당 날짜와 파일 ID의 메모 업데이트
        if file_id in audio_data.get('data', {}):
            audio_data['data'][file_id]['memo'] = memo
            
            # 업데이트된 데이터 저장
            audio_attr_value.value = json.dumps(audio_data, ensure_ascii=False)
            audio_attr_value.save()
            
            logger.info(f"음성파일 메모 업데이트 성공: Row {row_id}, Date {date}, File {file_id}")
            return JsonResponse({'success': True, 'message': '메모가 성공적으로 저장되었습니다.'})
        else:
            return JsonResponse({'success': False, 'error': '해당 음성파일을 찾을 수 없습니다.'})
            
    except Exception as e:
        logger.error(f"음성파일 메모 업데이트 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': f'메모 저장 중 오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def update_audio_file_order(request):
    """
    음성파일들의 순서를 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # 파라미터 검증
        row_id = request.POST.get('row_id')
        ordered_files = request.POST.get('ordered_files')
        
        if not all([row_id, ordered_files]):
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 순서 데이터 파싱
        try:
            ordered_files_data = json.loads(ordered_files)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '순서 데이터 형식이 올바르지 않습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        
        # 기존 AttributeValue 가져오기
        try:
            attr_value = AttributeValue.objects.get(row=row, attribute=audio_attribute)
            current_data = json.loads(attr_value.value) if attr_value.value else {}
        except AttributeValue.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 데이터를 찾을 수 없습니다.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '음성파일 데이터 형식이 올바르지 않습니다.'})
        
        # 각 파일에 순서 번호 추가
        for index, file_data in enumerate(ordered_files_data):
            date = file_data.get('date')
            file_id = file_data.get('file_id')
            
            if date and file_id and date in current_data and file_id in current_data[date]:
                current_data[date][file_id]['order'] = index
        
        # 업데이트된 데이터 저장
        attr_value.value = json.dumps(current_data, ensure_ascii=False)
        attr_value.save()
        
        logger.info(f"음성파일 순서 업데이트 완료 - Row: {row_id}")
        
        return JsonResponse({
            'success': True,
            'message': '파일 순서가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"음성파일 순서 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'순서 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def update_expected_loans(request):
    """
    기대출 속성의 다중 선택 값을 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # 파라미터 검증
        row_id = request.POST.get('row_id')
        attribute = request.POST.get('attribute')
        value = request.POST.get('value', '')
        
        if not row_id or not attribute:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 기대출 속성인지 확인
        if attribute != '기대출':
            return JsonResponse({'success': False, 'error': '기대출 속성만 처리 가능합니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기 또는 생성
        try:
            expected_loans_attr = Attribute.objects.get(name='기대출', user=user)
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type, _ = AttributeType.objects.get_or_create(name='text')
            expected_loans_attr = Attribute.objects.create(
                name='기대출',
                user=user,
                attributeType=text_type
            )
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=expected_loans_attr,
            defaults={'value': value}
        )
        
        if not created:
            attr_value.value = value
            attr_value.save()
        
        return JsonResponse({
            'success': True,
            'message': '기대출 정보가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def update_loan_amount(request):
    """
    기대출 금액을 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})
    
    try:
        # 임시로 user id 1 사용 (나중에 request.user로 변경 가능)
        user = User.objects.get(id=1)
        
        # JSON 데이터 파싱
        data = json.loads(request.body)
        row_id = data.get('row_id')
        loan_data_str = data.get('loan_data')
        
        if not row_id or not loan_data_str:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # Row 찾기
        row = Row.objects.get(id=row_id, user=user)
        
        # 기대출 속성 가져오기 또는 생성
        try:
            expected_loans_attr = Attribute.objects.get(name='기대출', user=user)
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type = AttributeType.objects.get_or_create(name='text')[0]
            expected_loans_attr = Attribute.objects.create(
                user=user,
                name='기대출',
                attributeType=text_type,
                assential=False
            )
        
        # 기대출 데이터를 JSON 문자열로 저장
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=expected_loans_attr,
            defaults={'value': loan_data_str}
        )
        
        if not created:
            attr_value.value = loan_data_str
            attr_value.save()
        
        return JsonResponse({
            'success': True,
            'message': '기대출 금액이 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 금액 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 금액 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def update_debt_field(request):
    """
    기대출 필드를 업데이트하는 함수 (diary_detail.js에서 사용)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        row_id = data.get('row_id')
        debt_data = data.get('debt_data')
        
        if not row_id or not debt_data:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기 또는 생성
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type, _ = AttributeType.objects.get_or_create(name='text')
            debt_attribute = Attribute.objects.create(
                name='기대출',
                user=user,
                attributeType=text_type,
                assential=False
            )
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=debt_attribute,
            defaults={'value': json.dumps(debt_data)}
        )
        
        if not created:
            attr_value.value = json.dumps(debt_data)
            attr_value.save()
        
        return JsonResponse({
            'success': True,
            'message': '기대출 정보가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def get_debt_details(request, row_id):
    """
    기대출 상세 정보를 가져오는 함수
    """
    try:
        # 사용자 정보 가져오기 (고정 ID: 1)
        user = User.objects.get(id=1)
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
            attr_value = AttributeValue.objects.get(row=row, attribute=debt_attribute)
            
            # JSON 데이터 파싱
            try:
                debt_data = json.loads(attr_value.value) if attr_value.value else {}
            except json.JSONDecodeError:
                debt_data = {}
                
        except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
            debt_data = {}
        
        return JsonResponse({
            'success': True,
            'debt_data': debt_data
        })
        
    except Exception as e:
        logger.error(f"기대출 정보 조회 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 정보 조회 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def save_debt_details(request):
    """
    기대출 상세 정보를 저장하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        row_id = data.get('row_id')
        debt_data = data.get('debt_data')
        
        if not row_id or not debt_data:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기 또는 생성
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type, _ = AttributeType.objects.get_or_create(name='text')
            debt_attribute = Attribute.objects.create(
                name='기대출',
                user=user,
                attributeType=text_type,
                assential=False
            )
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=debt_attribute,
            defaults={'value': json.dumps(debt_data)}
        )
        
        if not created:
            attr_value.value = json.dumps(debt_data)
            attr_value.save()
        
        return JsonResponse({
            'success': True,
            'message': '기대출 정보가 성공적으로 저장되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 저장 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 저장 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def get_funding_recommendation(request):
    """
    정책자금 추천 엔진 V2.0을 사용한 자금 추천 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        data = json.loads(request.body)
        row_id = data.get('row_id')
        
        if not row_id:
            return JsonResponse({'success': False, 'error': 'row_id가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
            user = User.objects.get(id=1)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        print("=== 정책자금 추천 엔진 V2.0 시작 ===")
        print(f"Row ID: {row_id}")
        
        # 회사 데이터 수집
        company_data = {}
        
        # 필수 필드들 (기본값 없음)
        # 업종 정보
        industry_value = _get_attribute_value(user, row, '업종')
        company_data['industry'] = industry_value if industry_value else '기타'
        
        # 연매출액 (문자열에서 숫자 추출)
        revenue_value = _get_attribute_value(user, row, '매출')  # '연매출액' -> '매출'로 수정
        company_data['annual_revenue'] = _parse_number(revenue_value, 0)
        
        # 신용점수
        credit_value = _get_attribute_value(user, row, '신용점수')
        company_data['credit_score'] = _parse_number(credit_value, 0)
        
        # 기본값이 설정되는 필드들
        # 직원수 (기본값: 1명)
        employee_value = _get_attribute_value(user, row, '직원수')
        company_data['employees'] = _parse_number(employee_value, 1)
        
        # 개업년월로부터 업력 계산 (기본값: 3년 = 36개월)
        opening_date_value = _get_attribute_value(user, row, '개업년월')
        calculated_months = _calculate_business_months(opening_date_value)
        company_data['business_months'] = calculated_months if calculated_months > 0 else 36
        
        # 기대출 정보에서 기존 부채 및 자금 사용 현황 계산 (기본값: 0)
        debt_data = _get_debt_data(user, row)
        print(f"원본 기대출 데이터: {debt_data}")
        
        # 총 기존 부채 계산 (만원 -> 원)
        total_existing_debt = sum(float(v) for v in debt_data.values() if v) * 10000
        company_data['existing_debt'] = total_existing_debt
        
        # V2.0 엔진을 위한 정확한 existing_funds 구조 생성 (만원 -> 원 변환)
        # 실제 기대출 데이터 키에 맞춰 정확한 매핑
        print(f'업종 : {company_data["industry"]} ')
        print(f'매출 : {company_data["annual_revenue"]} ')
        print(f'신용점수 : {company_data["credit_score"]} ')
        print(f'직원수 : {company_data["employees"]} ')
        print(f'업력 : {company_data["business_months"]} ')

        biz_region = _get_attribute_value(user, row, '지역')
        biz_industry = company_data['industry']

        # 매출액 카테고리 분류
        original_revenue = company_data['annual_revenue']
        if original_revenue == 0:
            biz_revenue = "매출 없음"
        elif original_revenue <= 100000000:  # 1억 이하
            biz_revenue = "1억 이하"
        elif original_revenue <= 500000000:  # 1~5억
            biz_revenue = "1~5억"
        elif original_revenue <= 1000000000:  # 5~10억
            biz_revenue = "5~10억"
        elif original_revenue <= 3000000000:  # 10~30억
            biz_revenue = "10~30억"
        else:  # 30억 이상
            biz_revenue = "30억 이상"
        
        # 직원수 카테고리 분류
        original_employees = company_data['employees']
        if original_employees == 0:
            biz_employees = "직원 없음"
        elif original_employees <= 4:  # 1~4인
            biz_employees = "1~4인"
        else:  # 5인 이상
            biz_employees = "5인 이상"

        if biz_employees in ["1~4인", "5~9인"] and biz_industry in ["광업", "제조업", "건설업", "운수업"] :
            biz_employees = "소상공인"
        elif biz_employees == "1~4인":
            biz_employees = "소상공인"
        elif biz_employees in ["10인 이상", "5~9인"]:
            biz_employees = "중소기업"
        
        # 업력 카테고리 분류 (개월을 년으로 환산)
        original_business_months = company_data['business_months']
        business_years = original_business_months / 12
        if business_years < 3:  # 3년 미만
            biz_business_months = "3년 미만"
        else:  # 3년 이상
            biz_business_months = "3년 이상"

        print(f'지역 : {biz_region} ')
        print(f'업종 : {biz_industry} ')
        print(f'매출 : {biz_revenue} ')
        print(f'규모 : {biz_employees} ')
        print(f'업력 : {biz_business_months} ')

        # region이 None이 아닐 경우에만 지역 조건 포함
        if biz_region:
            biz_data = BizInfo.objects.filter(
                                            (Q(region__contains=biz_region) | Q(region__contains="전국"))\
                                           & Q(possible_industry__contains=biz_industry) \
                                           & Q(revenue__contains=biz_revenue)\
                                           & Q(business_period__contains=biz_business_months) \
                                           & Q(target__contains=biz_employees)
                                           )[:5]
        else:
            # region이 None인 경우 지역 조건 제외
            biz_data = BizInfo.objects.filter(
                                            Q(possible_industry__contains=biz_industry) \
                                           & Q(revenue__contains=biz_revenue)\
                                           & Q(business_period__contains=biz_business_months) \
                                           & Q(target__contains=biz_employees)
                                           )[:5]
        
        # 공고 추천 데이터 준비
        recommended_notices = []
        pblanc_ids = []
        
        for biz in biz_data:
            print(f'biz_data : {biz.pblanc_id}')
            pblanc_ids.append(biz.pblanc_id)
            recommended_notices.append({
                'pblanc_id': biz.pblanc_id,
                'title': biz.title,
                'institution': biz.institution_name,
                'apply_period': f"{biz.reception_start} ~ {biz.reception_end}" if biz.reception_start and biz.reception_end else "상시접수",
                'support_amount': biz.support_field if biz.support_field else "지원규모 미정"
            })

        existing_funds = {
            'kibo_general': 0,  # 일반보증은 별도 없음
            'kibo_ip': float(debt_data.get('tech_guarantee', 0)) * 10000,  # 기술보증기금 = 기보 IP보증
            'sinbo': float(debt_data.get('credit_guarantee', 0)) * 10000,  # 신용보증기금 = 신보
            'jungjin': float(debt_data.get('smba', 0)) * 10000,  # 중진공
            'sojin_innovation': float(debt_data.get('semas_innovation', 0)) * 10000,  # 소진공 혁신성장
            'sojin_lowcredit': float(debt_data.get('semas_lowcredit', 0)) * 10000,  # 소진공 저신용
            'credit_foundation': float(debt_data.get('credit_foundation', 0)) * 10000  # 신용 = 신용보증재단
        }
        company_data['existing_funds'] = existing_funds
        
        print("=== 매핑된 existing_funds ===")
        for key, value in existing_funds.items():
            if value > 0:
                print(f"{key}: {value:,}원")
        print("==============================")
        
        # 신보 기존 사용액 별도 계산 (하위 호환성)
        company_data['existing_sinbo_debt'] = existing_funds['sinbo']
        
        # 추가 필드들 (기본값 설정)
        # 나이 속성에서 CEO 나이 계산 (기본값: 35세)
        age_attribute_value = _get_attribute_value(user, row, '나이')
        calculated_age = _calculate_age_from_data(age_attribute_value)
        company_data['ceo_age'] = calculated_age if calculated_age > 0 else 35
        
        company_data['is_startup'] = company_data['business_months'] <= 36
        
        # 경력은 별도 속성에서 가져오기 (기본값: 5년)
        experience_value = _get_attribute_value(user, row, '경력')
        company_data['experience_years'] = _parse_number(experience_value, 5)  # 기본값 5년
        
        print("=== 수집된 회사 데이터 ===")
        for key, value in company_data.items():
            if key == 'existing_funds':
                print(f"{key}:")
                for fund_key, fund_value in value.items():
                    print(f"  {fund_key}: {fund_value:,}원")
            else:
                print(f"{key}: {value}")
        print("========================")
        
        # 새로운 정책자금 추천 엔진 V2.0 사용
        from .funding_calculator import PolicyFundRecommendationEngineV2
        engine = PolicyFundRecommendationEngineV2()
        recommendation_result = engine.recommend_funds(company_data)
        
        print("=== 추천 엔진 결과 ===")
        print(f"결과 구조: {list(recommendation_result.keys())}")
        print("====================")
        
        # 에러 처리
        if 'error' in recommendation_result:
            return JsonResponse({
                'success': False,
                'error': recommendation_result['error'],
                'details': recommendation_result.get('exclusion_notes', [])
            })
        
        # 추천 자금들을 이전 형식과 호환되도록 변환
        individual_funds = []
        for fund in recommendation_result['recommended_funds']:
            fund_info = {
                'fund_name': fund['fund_name'],
                'limit': fund['limit'],
                'priority': fund.get('priority', 5),
                'institution': fund.get('institution', '미지정'),
                'calculation_note': fund.get('calculation_note', ''),
                'processing_time': fund.get('processing_time', '2-4주'),
                'interest_rate': fund.get('interest_rate', '3.0~6.0%'),
                'required_documents': fund.get('required_documents', ['사업자등록증', '재무제표']),
                'total_limit_after': fund.get('total_limit_after', fund['limit'])  # V2.0 추가 정보
            }
            individual_funds.append(fund_info)
        
        # 상세 자금 내역을 dict 형태로 구성
        detailed_funds_dict = {}
        for fund in individual_funds:
            detailed_funds_dict[fund['fund_name']] = fund['limit']
        
        # 총 추천 금액
        total_amount = recommendation_result['total_additional_amount']
        
        # V2.0 추가 정보 포함한 추천자금 필드 저장 데이터 구성
        recommendation_data = {
            '자금들': detailed_funds_dict,
            '총자금': total_amount,
            '상세정보': individual_funds,
            'pblanc_ids': pblanc_ids,  # 공고 ID 목록 추가
            'v2_info': {
                'version': recommendation_result['system_info']['version'],
                'calculation_time': recommendation_result['calculation_time'],
                'exclusion_notes': recommendation_result['exclusion_notes'],
                'existing_funds_summary': recommendation_result['existing_funds_summary']
            }
        }
        
        # 추천자금 필드에 상세 데이터 저장
        try:
            recommend_attribute = Attribute.objects.get(user=user, name='추천자금')
            recommend_attr_value, created = AttributeValue.objects.get_or_create(
                row=row, 
                attribute=recommend_attribute,
                defaults={'value': json.dumps(recommendation_data, ensure_ascii=False)}
            )
            if not created:
                recommend_attr_value.value = json.dumps(recommendation_data, ensure_ascii=False)
                recommend_attr_value.save()
                
            print(f"추천자금 필드 저장 완료: {'새로 생성' if created else '업데이트'}")
        except Attribute.DoesNotExist:
            print("추천자금 속성이 존재하지 않아 저장을 건너뜀")
        
        # 클라이언트에 반환할 응답 구성
        response_data = {
            'success': True,
            'total_recommended_amount': f"{total_amount:,}원",
            'individual_funds': individual_funds,
            'recommended_notices': recommended_notices,  # 공고 추천 데이터 추가
            'analysis_summary': {
                'total_products': len(individual_funds),
                'confidence': '95%',
                'version': recommendation_result['system_info']['version'],
                'logic_name': recommendation_result['system_info']['logic_name'],
                'calculation_time': recommendation_result['calculation_time'],
                'exclusion_notes': recommendation_result['exclusion_notes'],
                'existing_funds_summary': recommendation_result['existing_funds_summary']
            },
            'engine_info': {
                'version': '7월1일 로직 v2.0',
                'features': ['증액 가능성 정확 계산', '중복 표시 완전 제거', '기존 자금 현황 고려']
            }
        }
        
        print("=== 추천 완료 ===")
        print(f"총 추천 금액: {total_amount:,}원")
        print(f"추천 자금 수: {len(individual_funds)}개")
        print(f"계산 시간: {recommendation_result['calculation_time']}")
        print("================")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        error_msg = f'정책자금 추천 중 오류가 발생했습니다: {str(e)}'
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        })


def _get_attribute_value(user, row, attribute_name):
    """속성 값을 가져오는 헬퍼 함수"""
    try:
        attribute = Attribute.objects.get(user=user, name=attribute_name)
        attr_value = AttributeValue.objects.get(row=row, attribute=attribute)
        return attr_value.value
    except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
        return None


def _get_debt_data(user, row):
    """기대출 데이터를 가져오는 헬퍼 함수"""
    try:
        attribute = Attribute.objects.get(user=user, name='기대출')
        attr_value = AttributeValue.objects.get(row=row, attribute=attribute)
        
        if attr_value.value:
            if isinstance(attr_value.value, dict):
                return attr_value.value
            elif isinstance(attr_value.value, str) and attr_value.value.startswith('{'):
                return json.loads(attr_value.value)
        
        return {}
    except (Attribute.DoesNotExist, AttributeValue.DoesNotExist, json.JSONDecodeError):
        return {}


def _parse_number(value, default=0):
    """문자열이나 숫자를 정수로 변환하는 헬퍼 함수"""
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return int(value)
    
    if isinstance(value, str):
        # 숫자가 아닌 문자 제거 후 변환
        import re
        numbers_only = re.sub(r'[^\d.]', '', value)
        try:
            return int(float(numbers_only)) if numbers_only else default
        except ValueError:
            return default
    
    return default


def _calculate_business_months(opening_date_str):
    """개업년월로부터 업력(개월수) 계산하는 헬퍼 함수"""
    if not opening_date_str:
        return 12  # 기본값
    
    try:
        # 다양한 날짜 형식 처리
        if isinstance(opening_date_str, str):
            # YYYY-MM-DD 형식
            if '-' in opening_date_str and len(opening_date_str) >= 7:
                opening_date = datetime.strptime(opening_date_str[:7], '%Y-%m')
            # YYYY년 MM월 형식
            elif '년' in opening_date_str and '월' in opening_date_str:
                # 예: "2023년 5월"
                import re
                match = re.search(r'(\d{4})년\s*(\d{1,2})월', opening_date_str)
                if match:
                    year, month = int(match.group(1)), int(match.group(2))
                    opening_date = datetime(year, month, 1)
                else:
                    return 12
            else:
                return 12
        
        # 현재 날짜와의 차이 계산
        now = datetime.now()
        months_diff = (now.year - opening_date.year) * 12 + (now.month - opening_date.month)
        return max(1, months_diff)  # 최소 1개월
        
    except (ValueError, AttributeError):
        return 12  # 파싱 실패 시 기본값


def _calculate_age_from_data(age_data_str):
    """나이 데이터에서 실제 나이를 계산하는 헬퍼 함수"""
    import json
    from datetime import datetime, timedelta
    
    if not age_data_str:
        return 35  # 기본값
    
    try:
        # JSON 문자열인 경우 파싱
        if isinstance(age_data_str, str) and age_data_str.startswith('{'):
            age_data = json.loads(age_data_str)
        elif isinstance(age_data_str, dict):
            age_data = age_data_str
        else:
            return 35  # 기본값
        
        # 생년월일이 있는 경우 실제 나이 계산
        if age_data.get('birth_date'):
            birth_date_str = age_data['birth_date']
            try:
                # YY.MM.DD 형식 파싱
                if '.' in birth_date_str and len(birth_date_str) == 8:
                    year_part, month_part, day_part = birth_date_str.split('.')
                    year = int(year_part)
                    month = int(month_part)
                    day = int(day_part)
                    
                    # 2자리 연도를 4자리로 변환 (50 이상이면 19xx, 미만이면 20xx)
                    if year >= 50:
                        year += 1900
                    else:
                        year += 2000
                    
                    birth_date = datetime(year, month, day)
                    current_date = datetime.now()
                    
                    # 나이 계산
                    age = current_date.year - birth_date.year
                    if current_date.month < birth_date.month or (current_date.month == birth_date.month and current_date.day < birth_date.day):
                        age -= 1
                    
                    return max(age, 1)  # 최소 1세
                    
            except (ValueError, IndexError) as e:
                print(f"생년월일 파싱 오류: {e}")
                
        # 연령대 선택이 있는 경우
        elif age_data.get('age_range'):
            age_range = age_data['age_range']
            if age_range == 'under40':
                return 35
            elif age_range == 'over40':
                return 40
        
        return 35  # 기본값
        
    except Exception as e:
        print(f"나이 계산 오류: {e}")
        return 35  # 기본값

@csrf_exempt
def save_column_order(request):
    """컬럼 순서 저장"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    try:
        data = json.loads(request.body)
        column_order = data.get('column_order', [])
        if not column_order:
            return JsonResponse({'success': False, 'error': 'column_order is required'})
        user = User.objects.get(id=1)
        with transaction.atomic():
            for index, column_name in enumerate(column_order):
                try:
                    attribute = Attribute.objects.get(name=column_name, user=user)
                    attribute.sort_order = index
                    attribute.save()
                except Attribute.DoesNotExist:
                    continue
        return JsonResponse({'success': True, 'message': '컬럼 순서가 저장되었습니다.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def delete_row(request):
    """행 삭제 - 해당 행의 모든 데이터 제거"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        row_id = data.get('row_id')
        
        if not row_id:
            return JsonResponse({'success': False, 'error': 'row_id is required'})
        
        # 현재 사용자 (임시로 id=1 사용)
        user = User.objects.get(id=1)
        
        # 해당 행 찾기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 해당 행의 모든 속성 값들 삭제
        AttributeValue.objects.filter(row=row).delete()
        
        # 행 자체 삭제
        row.delete()
        
        return JsonResponse({'success': True, 'message': '행이 성공적으로 삭제되었습니다.'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
@csrf_exempt
def get_recommended_notices(request):
    """저장된 pblanc_ids를 이용해 공고 정보를 반환하는 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})
    
    try:
        data = json.loads(request.body)
        pblanc_ids = data.get('pblanc_ids', [])
        
        if not pblanc_ids:
            return JsonResponse({'success': True, 'recommended_notices': []})
        
        # pblanc_ids를 이용해 BizInfo에서 공고 정보 조회
        biz_data = BizInfo.objects.filter(pblanc_id__in=pblanc_ids)
        
        recommended_notices = []
        for biz in biz_data:
            # 접수 기간 처리
            if biz.reception_start and biz.reception_end:
                start_str = str(biz.reception_start)
                end_str = str(biz.reception_end)
                
                if start_str == "1900-01-01" and end_str == "9999-12-31":
                    apply_period = "상시접수"
                elif start_str == "1900-01-01":
                    apply_period = f"~ {end_str}"
                elif end_str == "9999-12-31":
                    apply_period = "상시접수 (지원금 소모 시 까지)"
                else:
                    apply_period = f"{start_str} ~ {end_str}"
            else:
                apply_period = "상시접수"
            
            recommended_notices.append({
                'pblanc_id': biz.pblanc_id,
                'title': biz.title,
                'institution': biz.institution_name,
                'apply_period': apply_period,
                'support_amount': biz.support_field if biz.support_field else "지원규모 미정"
            })
        
        return JsonResponse({
            'success': True,
            'recommended_notices': recommended_notices
        })
        
    except Exception as e:
        print(f"공고 정보 조회 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': '공고 정보를 조회할 수 없습니다.'
        })

@csrf_exempt
def update_audio_text_notes(request):
    """
    음성파일 노트(텍스트) 추가/수정/순서변경
    POST: row_id, date, notes(JSON string: [{id, text, order}, ...])
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST만 허용'})
    try:
        row_id = request.POST.get('row_id')
        notes_json = request.POST.get('notes')
        target_date = request.POST.get('date')
        if not row_id or not notes_json or not target_date:
            return JsonResponse({'success': False, 'error': '필수 파라미터 누락'})
        notes = json.loads(notes_json)
        user = User.objects.get(id=1)
        row = Row.objects.get(id=row_id, user=user)
        audio_attr = Attribute.objects.get(name='음성파일', user=user)
        attr_value, _ = AttributeValue.objects.get_or_create(row=row, attribute=audio_attr, defaults={'value': '{}'})
        # 기존 데이터 파싱
        try:
            data = json.loads(attr_value.value) if attr_value.value else {}
        except:
            data = {}
        # 지정한 날짜가 없으면 생성
        if 'data' not in data:
            data['data'] = {}
        # 기존 텍스트 노트들 제거 (같은 날짜의 텍스트 타입만)
        keys_to_remove = []
        for key, value in data['data'].items():
            if isinstance(value, dict) and value.get('type') == 'text':
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del data['data'][key]
        # 새로운 텍스트 노트들 추가
        for note in notes:
            note_id = note.get('id')
            if note_id:
                # 텍스트 값이 undefined나 null인 경우 빈 문자열로 처리
                text_value = note.get('text', '')
                if text_value is None:
                    text_value = ''
                    
                data['data'][note_id] = {
                    'text': text_value,
                    'order': note.get('order', 0),
                    'type': 'text'
                }
        attr_value.value = json.dumps(data, ensure_ascii=False)
        attr_value.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@csrf_exempt
def update_audio_file_order_and_notes(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})

    row_id = request.POST.get('row_id')
    notes_json = request.POST.get('notes')

    print(f"=== update_audio_file_order_and_notes 시작 ===")
    print(f"row_id: {row_id}")
    print(f"notes_json: {notes_json}")

    if not row_id:
        return JsonResponse({'success': False, 'error': 'row_id 누락'})

    try:
        notes = json.loads(notes_json or "[]")
        print(f"파싱된 notes: {notes}")

        user = User.objects.get(id=1)
        row = Row.objects.get(id=row_id, user=user)
        attr = Attribute.objects.get(name="음성파일", user=user)
        attr_value = AttributeValue.objects.filter(row=row, attribute=attr).first()

        if not attr_value:
            # 최초 생성: 빈 dict으로 생성
            attr_value = AttributeValue.objects.create(row=row, attribute=attr, value='{}')

        value = json.loads(attr_value.value or "{}")
        print(f"기존 value: {value}")

        # 'data' 키가 없으면 생성
        if 'data' not in value:
            value['data'] = {}

        # 새로운 순서로 재구성된 데이터
        new_data = {}

        # 모든 아이템을 순서대로 저장
        for item in notes:
            item_id = item.get('id')
            if not item_id:
                continue
                
            print(f"처리 중인 아이템: {item}")
            
            if item.get('type') == 'text':
                # 텍스트 노트
                text_value = item.get('text', '')
                if text_value is None:
                    text_value = ''
                
                new_data[item_id] = {
                    'text': text_value,
                    'order': item.get('order', 0),
                    'type': 'text',
                    'upload_date': item.get('upload_date', '')
                }
                print(f"텍스트 노트 저장: {new_data[item_id]}")
            else:
                # 파일 (오디오, 이미지, 문서)
                # notes에서 받은 모든 파일 정보를 그대로 사용 (JS에서 이미 완전한 정보를 보냄)
                file_data = {
                    'order': item.get('order', 0),
                    'type': item.get('type', 'file'),
                    'original_filename': item.get('original_filename', ''),
                    'filename': item.get('filename', ''),
                    'stored_filename': item.get('stored_filename', ''),
                    's3_key': item.get('s3_key', ''),
                    'download_url': item.get('download_url', ''),
                    'preview_url': item.get('preview_url', ''),
                    'file_size': item.get('file_size', 0),
                    'content_type': item.get('content_type', ''),
                    'upload_time': item.get('upload_time', ''),
                    'upload_date': item.get('upload_date', ''),
                    'converted_text': item.get('converted_text', ''),
                    'memo': item.get('memo', ''),
                    'gpt_summary': item.get('gpt_summary', '')
                }
                
                # None 값들을 빈 문자열로 변환
                for key, val in file_data.items():
                    if val is None:
                        file_data[key] = ''
                
                new_data[item_id] = file_data
                print(f"파일 저장: {new_data[item_id]}")

        # 새로운 데이터로 교체
        value['data'] = new_data
        print(f"최종 저장할 value: {value}")

        attr_value.value = json.dumps(value, ensure_ascii=False)
        attr_value.save()

        print("=== update_audio_file_order_and_notes 완료 ===")
        return JsonResponse({'success': True})

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def entry_table_partial(request):
    user = User.objects.get(id=1)
    # 항상 detail=False, view_select=True만 표시 (쿼리 최적화)
    attributes = Attribute.objects.filter(user=user, detail=False, view_select=True).select_related('attributeType').order_by('sort_order', 'id')
    user_attributes = attributes
    
    # 쿼리 최적화: select_related와 prefetch_related 적용
    rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
        'values__attribute__attributeType',
        'values__attribute__dropdown_attributes'
    ).order_by('order')
    
    rows_data = []
    for row in rows:
        row_values = {}
        for attr in user_attributes:
            # prefetch된 데이터에서 찾기
            attr_value = None
            for value in row.values.all():
                if value.attribute_id == attr.id:
                    attr_value = value
                    break
            
            value = attr_value.value if attr_value else ''
            
            if attr.name == '매출' or '매출' in attr.name:
                numeric_value = parse_korean_currency(value)
                row_values[attr.name] = {
                    'label': value,  # 화면 표시용(한글 단위 등)
                    'value': numeric_value,  # 실제 숫자값
                    'color': ''
                }
            elif attr.attributeType and attr.attributeType.name == 'dropdown' and value.isdigit():
                # prefetch된 dropdown 데이터에서 찾기
                dropdown = None
                for dropdown_attr in attr.dropdown_attributes.all():
                    if dropdown_attr.id == int(value):
                        dropdown = dropdown_attr
                        break
                
                if dropdown:
                    row_values[attr.name] = {
                        'label': dropdown.option, 
                        'color': dropdown.color,
                        'raw_value': value,
                        'selected_options': [{'id': dropdown.id, 'label': dropdown.option, 'color': dropdown.color}]
                    }
                else:
                    row_values[attr.name] = {
                        'label': value, 
                        'color': '',
                        'raw_value': value,
                        'selected_options': []
                    }
            elif attr.attributeType and attr.attributeType.name == 'dropdown' and value.startswith('[') and value.endswith(']'):
                # 다중선택(dropdown) 필드인 경우
                try:
                    selected_ids = json.loads(value)
                    print(f"  JSON 파싱 성공: {selected_ids}")
                    selected_options = []
                    for dropdown_attr in attr.dropdown_attributes.all():
                        if dropdown_attr.id in selected_ids:
                            selected_options.append({
                                'id': dropdown_attr.id,
                                'label': dropdown_attr.option,
                                'color': dropdown_attr.color
                            })
                    
                    
                    if selected_options:
                        # 첫 번째 옵션의 색상을 기본 색상으로 사용
                        default_color = selected_options[0]['color']
                        row_values[attr.name] = {
                            'label': ', '.join([opt['label'] for opt in selected_options]),
                            'color': default_color,
                            'raw_value': value,
                            'selected_options': selected_options,
                            'multi_select': True
                        }
                        print(f"  최종 결과: {row_values[attr.name]}")
                    else:
                        row_values[attr.name] = {
                            'label': '선택 없음',
                            'color': '',
                            'raw_value': value,
                            'selected_options': [],
                            'multi_select': True
                        }
                        print(f"  선택된 옵션 없음: {row_values[attr.name]}")
                except json.JSONDecodeError as e:
                    print(f"  JSON 파싱 실패: {e}")
                    row_values[attr.name] = {
                        'label': value,
                        'color': '',
                        'raw_value': value,
                        'selected_options': [],
                        'multi_select': True
                    }
            elif attr.attributeType and attr.attributeType.name == 'file' and value:
                # 파일 타입인 경우
                file_info = json.loads(value)
                original_filename = file_info.get('original_filename', '파일')
                
                row_values[attr.name] = {
                    'type': 'file',
                    'label': original_filename,
                    'download_url': file_info.get('download_url', ''),
                    'file_size': file_info.get('file_size', 0),
                    'content_type': file_info.get('content_type', ''),
                    'original_filename': original_filename
                }
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
    
    attributes_list = list(attributes.values('name', 'attributeType__name', 'assential'))
    attributes_obj_list = [SimpleNamespace(**{k.replace('attributeType__name', 'attributeType_name'): v for k, v in d.items()}) for d in attributes_list]
    return render(request, 'diary/entry_table_partial.html', {
        'attributes': attributes_obj_list,
        'rows': rows_data,
    })

@csrf_exempt
def toggle_attribute_visibility(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attribute_name = data.get('attribute_name')
            
            if not attribute_name:
                return JsonResponse({'success': False, 'error': '속성명이 필요합니다.'})
            
            # 속성 찾기
            user = User.objects.get(id=1)
            attribute = Attribute.objects.filter(user=user, name=attribute_name).first()
            
            if not attribute:
                return JsonResponse({'success': False, 'error': '속성을 찾을 수 없습니다.'})
            
            # view_select 값 토글
            attribute.view_select = not attribute.view_select
            attribute.save()
            
            return JsonResponse({
                'success': True, 
                'view_select': attribute.view_select,
                'message': f'"{attribute_name}" 속성이 {"표시" if attribute.view_select else "숨김"} 상태로 변경되었습니다.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'}, status=405)

@require_GET
def get_hidden_attributes(request):
    """숨겨진 속성들(detail=False, view_select=False)을 가져오는 API"""
    try:
        user = User.objects.get(id=1)
        hidden_attributes = Attribute.objects.filter(
            user=user, 
            detail=False, 
            view_select=False
        ).order_by('sort_order', 'id')
        
        attributes_data = []
        for attr in hidden_attributes:
            attributes_data.append({
                'id': attr.id,
                'name': attr.name,
                'attributeType_name': attr.attributeType.name if attr.attributeType else '',
                'assential': attr.assential,
                'detail': attr.detail,
                'view_select': attr.view_select,
                'sort_order': attr.sort_order
            })
        
        return JsonResponse({
            'success': True,
            'attributes': attributes_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_GET
def get_all_attributes(request):
    """detail=False인 모든 속성(필수 포함)을 반환하는 API"""
    try:
        user = User.objects.get(id=1)
        attributes = Attribute.objects.filter(user=user, detail=False).order_by('sort_order', 'id')
        attributes_data = []
        for attr in attributes:
            attributes_data.append({
                'id': attr.id,
                'name': attr.name,
                'attributeType_name': attr.attributeType.name if attr.attributeType else '',
                'assential': attr.assential,
                'view_select': attr.view_select,
                'cascade': attr.cascade,  # cascade 필드 추가
                'sort_order': attr.sort_order
            })
        return JsonResponse({'success': True, 'attributes': attributes_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_GET
def get_dropdown_attributes(request):
    """dropdown 타입의 속성 목록을 반환하는 API (칸반보드 필터용)"""
    try:
        user = User.objects.get(id=1)
        dropdown_attributes = Attribute.objects.filter(
            user=user, 
            attributeType__name='dropdown',
            detail=False,
            view_select=True
        ).order_by('-assential', 'name')
        
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

def parse_korean_currency(value):
    """한국어 통화를 숫자로 변환"""
    if not value or value == '0':
        return 0
    
    # 숫자만 추출
    if isinstance(value, str):
        # 콤마 제거
        value = value.replace(',', '')
        # 숫자가 아닌 문자 제거
        value = ''.join(c for c in value if c.isdigit())
    
    try:
        return int(value) if value else 0
    except (ValueError, TypeError):
        return 0

def parse_sales_amount(eok, cheonman):
    """억과 천만 단위를 숫자로 변환"""
    try:
        eok_amount = int(eok) if eok else 0
        cheonman_amount = int(cheonman) if cheonman else 0
        
        # 총 금액 계산 (억 * 100000000 + 천만 * 10000000)
        total_amount = eok_amount * 100000000 + cheonman_amount * 10000000
        return total_amount
    except (ValueError, TypeError):
        return 0

@csrf_exempt
def upload_note_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        row_id = request.POST.get('row_id')
        if not file or not row_id:
            return JsonResponse({'success': False, 'error': '파일 또는 row_id 누락'})
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        file_extension = os.path.splitext(file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        s3_key = f"note_files/{unique_filename}"
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type,
                'ContentDisposition': f'attachment; filename=\"{file.name}\"'
            }
        )
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=300
        )
        preview_url = download_url
        file_info = {
            'original_filename': file.name,
            'stored_filename': unique_filename,
            's3_key': s3_key,
            'download_url': download_url,
            'preview_url': preview_url,
            'file_size': file.size,
            'content_type': file.content_type,
            'type': None,  # type 필드 추가
        }
        # 파일 타입 판별
        if file.content_type.startswith('image/'):
            file_info['type'] = 'image'
        elif file.content_type.startswith('audio/'):
            file_info['type'] = 'audio'
        else:
            file_info['type'] = 'file'

        # === DB 저장 로직 추가 ===
        from .models import User, Row, Attribute, AttributeValue
        import json

        user = User.objects.get(id=1)
        row = Row.objects.get(id=row_id, user=user)
        attr = Attribute.objects.get(name='음성파일', user=user)
        attr_value, _ = AttributeValue.objects.get_or_create(row=row, attribute=attr)
        # 기존 값이 있으면 파싱, 없으면 빈 dict
        try:
            value_dict = json.loads(attr_value.value) if attr_value.value else {"data": {}}
        except Exception:
            value_dict = {"data": {}}
        
        # 고유 id 생성
        import time
        file_id = f'f{int(time.time()*1000)}'
        
        # order 필드 추가 (기존 아이템 개수 + 1)
        existing_count = len(value_dict.get("data", {}))
        file_info['order'] = existing_count
        
        value_dict["data"][file_id] = file_info
        attr_value.value = json.dumps(value_dict, ensure_ascii=False)
        attr_value.save()
        # === DB 저장 끝 ===

        return JsonResponse({'success': True, 'file_info': file_info, 'file_id': file_id})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def delete_note_file(request):
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        file_id = request.POST.get('file_id')
        s3_key = request.POST.get('s3_key')
        
        if not row_id or not file_id or not s3_key:
            return JsonResponse({'success': False, 'error': 'row_id, file_id, s3_key 모두 필요합니다'})
        
        try:
            # 사용자와 행 조회
            user = User.objects.get(id=1)
            row = Row.objects.get(id=row_id, user=user)
            audio_attr = Attribute.objects.get(name='음성파일', user=user)
            attr_value = AttributeValue.objects.get(row=row, attribute=audio_attr)
            
            # 기존 데이터 파싱
            try:
                current_data = json.loads(attr_value.value) if attr_value.value else {}
            except json.JSONDecodeError:
                current_data = {}
            
            # 'data' 키가 없으면 생성
            if 'data' not in current_data:
                current_data['data'] = {}
            
            # 해당 file_id가 존재하는지 확인
            if file_id not in current_data['data']:
                return JsonResponse({'success': False, 'error': '해당 파일을 찾을 수 없습니다'})
            
            # S3에서 파일 삭제
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            try:
                s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
                print(f"S3 파일 삭제 완료: {s3_key}")
            except Exception as e:
                print(f"S3 파일 삭제 실패 (계속 진행): {str(e)}")
                # S3 삭제 실패해도 DB에서 삭제는 진행
            
            # DB에서 해당 파일 데이터 삭제
            del current_data['data'][file_id]
            
            # 업데이트된 데이터 저장
            attr_value.value = json.dumps(current_data, ensure_ascii=False)
            attr_value.save()
            
            print(f"노트 파일 삭제 완료 - Row: {row_id}, File: {file_id}")
            
            return JsonResponse({
                'success': True,
                'message': '파일이 성공적으로 삭제되었습니다.',
                'remaining_files': len(current_data['data'])
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        except AttributeValue.DoesNotExist:
            return JsonResponse({'success': False, 'error': '속성 값을 찾을 수 없습니다.'})
        except Exception as e:
            print(f"노트 파일 삭제 중 오류: {e}")
            return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})

@csrf_exempt
def update_note_order_and_notes(request):
    """노트 순서와 텍스트 노트를 업데이트하는 API"""
    if request.method == 'POST':
        try:
            row_id = request.POST.get('row_id')
            notes_data = request.POST.get('notes')
            
            if not row_id or not notes_data:
                return JsonResponse({
                    'success': False,
                    'error': 'row_id와 notes가 필요합니다.'
                })
            
            # 사용자 ID를 1로 고정
            user = User.objects.get(id=1)
            
            # Row와 음성파일 속성 조회
            row = Row.objects.get(id=row_id, user=user)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            
            # JSON 데이터 파싱
            try:
                notes = json.loads(notes_data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': '잘못된 JSON 형식입니다.'
                })
            
            # 기존 데이터 구조 생성
            existing_data = {'data': {}}
            
            # 노트 데이터 처리
            for note in notes:
                note_id = note.get('id')
                note_type = note.get('type', 'file')
                order = note.get('order', 0)
                
                if note_type == 'text':
                    # 텍스트 노트
                    existing_data['data'][note_id] = {
                        'id': note_id,
                        'type': 'text',
                        'text': note.get('text', ''),
                        'order': order,
                        'upload_date': note.get('upload_date', '')
                    }
                else:
                    # 파일 노트 (기존 파일 정보 유지)
                    existing_data['data'][note_id] = {
                        'id': note_id,
                        'type': note.get('type', 'file'),
                        'original_filename': note.get('original_filename', ''),
                        'stored_filename': note.get('stored_filename', ''),
                        's3_key': note.get('s3_key', ''),
                        'download_url': note.get('download_url', ''),
                        'preview_url': note.get('preview_url', ''),
                        'file_size': note.get('file_size', 0),
                        'content_type': note.get('content_type', ''),
                        'order': order,
                        'upload_date': note.get('upload_date', '')
                    }
            
            # 음성파일 속성에 저장
            attr_value, created = AttributeValue.objects.get_or_create(
                row=row,
                attribute=audio_attribute,
                defaults={'value': json.dumps(existing_data, ensure_ascii=False)}
            )
            
            if not created:
                attr_value.value = json.dumps(existing_data, ensure_ascii=False)
                attr_value.save()
            
            return JsonResponse({
                'success': True,
                'message': '노트 순서와 텍스트 노트가 업데이트되었습니다.'
            })
            
        except Row.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 행을 찾을 수 없습니다.'
            })
        except Exception as e:
            print(f"노트 업데이트 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'처리 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'POST 요청만 허용됩니다.'
    })

@csrf_exempt
def get_file_preview_url_note(request, file_id):
    """파일 미리보기를 위한 새로운 S3 서명된 URL을 생성하는 API"""
    if request.method == 'GET':
        print(f"get_file_preview_url_note 호출됨: {file_id}")
        try:
            row_id = request.GET.get('row_id')
            if not row_id:
                return JsonResponse({'success': False, 'error': 'row_id가 필요합니다.'})
            user = User.objects.get(id=1)
            row = Row.objects.get(id=row_id, user=user)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            attr_value = AttributeValue.objects.filter(row=row, attribute=audio_attribute).first()
            if not attr_value or not attr_value.value:
                return JsonResponse({'success': False, 'error': '파일 데이터를 찾을 수 없습니다.'})
            try:
                audio_data = json.loads(attr_value.value)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
            file_info = None
            if 'data' in audio_data:
                for k, v in audio_data['data'].items():
                    if not isinstance(v, dict):
                        continue
                    # 정확히 key 또는 stored_filename으로만 매칭
                    if k == file_id or v.get('stored_filename') == file_id:
                        file_info = v
                        break
            if not file_info:
                return JsonResponse({'success': False, 'error': f'파일 ID {file_id}를 찾을 수 없습니다.'})
            s3_key = file_info.get('s3_key')
            if not s3_key:
                return JsonResponse({'success': False, 'error': 'S3 키가 없습니다.'})
            try:
                import boto3
                from django.conf import settings
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                content_type = file_info.get('content_type', '')
                if (content_type == 'application/pdf' or 
                    content_type.startswith('image/') or
                    content_type == 'text/plain' or
                    content_type == 'text/html' or
                    content_type == 'text/css' or
                    content_type == 'text/javascript' or
                    content_type == 'application/json' or
                    content_type == 'application/xml'):
                    content_disposition = 'inline'
                else:
                    content_disposition = 'attachment'
                signed_preview_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': s3_key,
                        'ResponseContentDisposition': content_disposition
                    },
                    ExpiresIn=3600
                )
                return JsonResponse({'success': True, 'preview_url': signed_preview_url})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'S3 URL 생성 실패: {str(e)}'})
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'})

@require_GET
def get_file_preview_url(request, row_id, field_name):
    """단일 파일 필드(영업노트 방식) presigned URL 반환"""
    try:
        user = User.objects.get(id=1)
        row = Row.objects.get(id=row_id, user=user)
        attr = Attribute.objects.get(name=field_name, user=user)
        attr_value = AttributeValue.objects.get(row=row, attribute=attr)
        file_info = json.loads(attr_value.value)
        s3_key = file_info.get('s3_key')
        if not s3_key:
            return JsonResponse({'success': False, 'error': 'S3 키가 없습니다.'})
        import boto3
        from django.conf import settings
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        content_type = file_info.get('content_type', '')
        if (content_type == 'application/pdf' or 
            content_type.startswith('image/') or
            content_type == 'text/plain' or
            content_type == 'text/html' or
            content_type == 'text/css' or
            content_type == 'text/javascript' or
            content_type == 'application/json' or
            content_type == 'application/xml'):
            content_disposition = 'inline'
        else:
            content_disposition = 'attachment'
        signed_preview_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': content_disposition
            },
            ExpiresIn=3600
        )
        return JsonResponse({'success': True, 'preview_url': signed_preview_url})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_GET
def get_datetime_attributes(request):
    """datetime 타입의 속성 목록을 반환하는 API"""
    try:
        user = User.objects.get(id=1)
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
    user = User.objects.get(id=1)
    calendar_settings = CalendarSettings.objects.filter(user=user).first()
    if calendar_settings:
        return JsonResponse({'success': True, 'settings': calendar_settings.settings})
    # 기본값
    return JsonResponse({'success': True, 'settings': {'date_fields': [], 'custom_events': []}})

@csrf_exempt
def save_calendar_settings(request):
    if request.method == 'POST':
        user = User.objects.get(id=1)
        data = json.loads(request.body)
        settings = data.get('settings', {})
        calendar_settings, _ = CalendarSettings.objects.get_or_create(user=user)
        calendar_settings.settings = settings
        calendar_settings.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@require_GET
def calendar_events(request):
    user = User.objects.get(id=1)
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

def parse_business_data(value):
    """개업년월 데이터 파싱"""
    if not value:
        return {}
    
    # 이미 JSON 형태인 경우
    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    
    # 일반 문자열인 경우 (날짜 형식)
    if isinstance(value, str):
        return {'opening_date': value}
    
    # 딕셔너리인 경우
    if isinstance(value, dict):
        return value
    
    return {}

def calculate_business_years(opening_date_str, years_ago=None):
    """개업년수 계산"""
    if years_ago:
        try:
            return int(years_ago)
        except (ValueError, TypeError):
            pass
    
    if not opening_date_str:
        return None
    
    try:
        opening_date = datetime.strptime(opening_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        years = current_date.year - opening_date.year
        if current_date.month < opening_date.month or (current_date.month == opening_date.month and current_date.day < opening_date.day):
            years -= 1
        return max(0, years)
    except (ValueError, TypeError):
        return None

@csrf_exempt
def update_sales_field(request):
    """매출 필드 업데이트 - 억/천만 단위 지원"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            row_id = data.get('row_id')
            field_name = data.get('field_name')
            eok = data.get('eok', 0)
            cheonman = data.get('cheonman', 0)
            
            if not row_id or not field_name:
                return JsonResponse({'success': False, 'error': 'row_id와 field_name이 필요합니다'})
            
            # 사용자와 행 조회
            user = User.objects.get(id=1)
            row = Row.objects.get(id=row_id, user=user)
            
            # 총 금액 계산
            total_amount = parse_sales_amount(eok, cheonman)
            
            # 속성 조회
            try:
                attr = Attribute.objects.get(name=field_name, user=user)
            except Attribute.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'속성 {field_name}을 찾을 수 없습니다'})
            
            # AttributeValue 조회 또는 생성
            attr_value, created = AttributeValue.objects.get_or_create(
                row=row, 
                attribute=attr,
                defaults={'value': str(total_amount)}
            )
            
            if not created:
                attr_value.value = str(total_amount)
                attr_value.save()
            
            return JsonResponse({
                'success': True, 
                'total_amount': total_amount,
                'formatted_amount': formatToKoreanCurrency(total_amount) if total_amount > 0 else '0원'
            })
            
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다'})
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '속성을 찾을 수 없습니다'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})

def formatToKoreanCurrency(amount):
    """숫자를 한국어 통화 단위로 변환"""
    if not amount or amount == 0:
        return '0원'
    
    amount = int(amount)
    if amount == 0:
        return '0원'
    
    result = ''
    
    # 억 단위 처리
    if amount >= 100000000:
        eok = amount // 100000000
        result += f'{eok}억'
        amount = amount % 100000000
    
    # 천만 단위 처리
    if amount >= 10000000:
        cheonman = amount // 10000000
        if result:
            result += f' {cheonman}천'
        else:
            result = f'{cheonman}천'
        amount = amount % 10000000
    
    # 백만 단위 처리
    if amount >= 1000000:
        baekman = amount // 1000000
        if result:
            result += f' {baekman}백'
        else:
            result = f'{baekman}백'
        amount = amount % 1000000
    
    # 만 단위 처리
    if amount >= 10000:
        man = amount // 10000
        if result:
            result += f'{man}만'
        else:
            result = f'{man}만'
    
    return result + '원'

@csrf_exempt
def duplicate_row(request):
    """행을 복제하는 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        data = json.loads(request.body)
        source_row_id = data.get('source_row_id')
        
        if not source_row_id:
            return JsonResponse({'success': False, 'error': '복제할 행 ID가 필요합니다.'})
        
        # 사용자 가져오기 (diary_list와 동일한 방식)
        user = User.objects.get(id=1)
        
        # 소스 행 조회
        source_row = Row.objects.filter(id=source_row_id).first()
        if not source_row:
            return JsonResponse({'success': False, 'error': '복제할 행을 찾을 수 없습니다.'})
        
        print(f"복제 시작: 소스 행 ID {source_row_id}")
        print(f"소스 행의 original_row_ids: {source_row.original_row_ids}")
        print(f"소스 행의 copied_row_ids: {source_row.copied_row_ids}")
        
        # 현재 사용자의 모든 행 조회하여 order 조정
        user_rows = Row.objects.filter(user=user).order_by('order')
        
        # 소스 행의 order 찾기
        source_order = source_row.order
        
        # 소스 행 이후의 모든 행들의 order를 1씩 증가
        rows_to_update = user_rows.filter(order__gt=source_order)
        for row in rows_to_update:
            row.order += 1
            row.save()
        
        # 새 행 생성 (소스 행의 모든 데이터 복사)
        new_row = Row.objects.create(
            user=user,
            order=source_order + 1,
            created_at=timezone.now()
        )
        
        print(f"새 행 생성됨: ID {new_row.id}")
        
        # === 개선된 양방향 관계 설정 ===
        # 1. 새 행의 원본 행 ID들을 설정 (소스 행의 원본 행 ID들 + 소스 행 ID)
        new_original_ids = source_row.original_row_ids.copy()
        new_original_ids.append(source_row.id)
        new_row.original_row_ids = new_original_ids
        new_row.save()
        
        print(f"새 행의 original_row_ids 설정: {new_row.original_row_ids}")
        
        # 2. 소스 행의 복제된 행 목록에 새 행 추가
        source_row.add_copied_row(new_row.id)
        print(f"소스 행의 copied_row_ids 업데이트: {source_row.copied_row_ids}")
        
        # 3. 소스 행의 모든 원본 행들에도 새 행을 복제된 행으로 추가
        for original_id in source_row.original_row_ids:
            try:
                original_row = Row.objects.get(id=original_id)
                original_row.add_copied_row(new_row.id)
                print(f"원본 행 {original_id}의 copied_row_ids 업데이트: {original_row.copied_row_ids}")
            except Row.DoesNotExist:
                print(f"원본 행 {original_id}를 찾을 수 없습니다.")
                continue
        
        # 4. 소스 행의 모든 복제된 행들에도 새 행을 복제된 행으로 추가
        for copied_id in source_row.copied_row_ids:
            try:
                copied_row = Row.objects.get(id=copied_id)
                copied_row.add_copied_row(new_row.id)
                print(f"복제된 행 {copied_id}의 copied_row_ids 업데이트: {copied_row.copied_row_ids}")
            except Row.DoesNotExist:
                print(f"복제된 행 {copied_id}를 찾을 수 없습니다.")
                continue
        
        # 5. 새 행의 복제된 행 목록에 소스 행의 모든 복제된 행들 추가
        new_copied_ids = source_row.copied_row_ids.copy()
        new_row.copied_row_ids = new_copied_ids
        new_row.save()
        print(f"새 행의 copied_row_ids 설정: {new_row.copied_row_ids}")
        
        # 6. 새 행의 복제된 행 목록에 소스 행도 추가 (양방향 관계 완성)
        if source_row.id not in new_row.copied_row_ids:
            new_row.copied_row_ids.append(source_row.id)
            new_row.save()
            print(f"새 행의 copied_row_ids에 소스 행 추가: {new_row.copied_row_ids}")
        
        # 7. 소스 행의 원본 행 목록에 새 행 추가 (양방향 관계 완성)
        if new_row.id not in source_row.original_row_ids:
            source_row.original_row_ids.append(new_row.id)
            source_row.save()
            print(f"소스 행의 original_row_ids에 새 행 추가: {source_row.original_row_ids}")
        
        # 8. 소스 행을 다시 조회하여 최신 상태 확인 및 강제 업데이트
        source_row.refresh_from_db()
        if new_row.id not in source_row.copied_row_ids:
            source_row.copied_row_ids.append(new_row.id)
            source_row.save()
            print(f"소스 행 강제 업데이트 후 copied_row_ids: {source_row.copied_row_ids}")
        
        # 9. 새 행도 다시 조회하여 최신 상태 확인 및 강제 업데이트
        new_row.refresh_from_db()
        if source_row.id not in new_row.copied_row_ids:
            new_row.copied_row_ids.append(source_row.id)
            new_row.save()
            print(f"새 행 강제 업데이트 후 copied_row_ids: {new_row.copied_row_ids}")
        
        # === AttributeValue 복사 ===
        source_values = AttributeValue.objects.filter(row=source_row)
        print(f"복사할 AttributeValue 개수: {source_values.count()}")
        
        for source_value in source_values:
            try:
                print(f"=== AttributeValue 복사 시작 ===")
                print(f"속성명: {source_value.attribute.name if source_value.attribute else 'None'}")
                print(f"속성 타입: {source_value.attribute.attributeType.name if source_value.attribute and source_value.attribute.attributeType else 'None'}")
                print(f"값: {source_value.value[:100] if source_value.value else 'None'}...")
                
                # 파일 타입인 경우 S3에서 파일 복사
                if (source_value.attribute and 
                    source_value.attribute.attributeType and 
                    source_value.attribute.attributeType.name == 'file' and 
                    source_value.value):
                    
                    print(f"파일 타입 속성 발견: {source_value.attribute.name}")
                    
                    try:
                        # 기존 파일 정보 파싱
                        file_data = json.loads(source_value.value)
                        print(f"파일 데이터 파싱 성공: {file_data}")
                        
                        original_filename = file_data.get('original_filename', '')
                        stored_filename = file_data.get('stored_filename', '')
                        s3_key = file_data.get('s3_key', '')
                        
                        print(f"파일 정보 - 원본명: {original_filename}, 저장명: {stored_filename}, S3키: {s3_key}")
                        
                        if s3_key and stored_filename:
                            # 새로운 파일명 생성 (UUID 사용)
                            file_extension = os.path.splitext(original_filename)[1] if original_filename else ''
                            new_filename = f"{uuid.uuid4()}{file_extension}"
                            print(f"새 파일명 생성: {new_filename}")
                            
                            # S3에서 파일 복사
                            print(f"S3 파일 복사 시작: {s3_key} -> {new_filename}")
                            copy_result = copy_s3_file(s3_key, new_filename)
                            print(f"S3 복사 결과: {copy_result}")
                            
                            if copy_result and isinstance(copy_result, dict) and copy_result.get('success'):
                                # 새로운 파일 정보 생성 (upload_time 추가)
                                new_file_data = {
                                    'original_filename': original_filename,
                                    'stored_filename': new_filename,
                                    's3_key': copy_result.get('new_s3_key', ''),
                                    'download_url': copy_result.get('new_download_url', ''),
                                    'preview_url': copy_result.get('new_preview_url', ''),
                                    'public_url': copy_result.get('new_public_url', ''),
                                    'file_size': file_data.get('file_size', 0),
                                    'content_type': file_data.get('content_type', ''),
                                    'type': file_data.get('type', 'file'),
                                    'upload_time': copy_result.get('upload_time', timezone.now().isoformat())  # copy_s3_file에서 반환된 시간 사용
                                }
                                
                                print(f"새 파일 데이터 생성: {new_file_data}")
                                
                                # 새로운 파일 정보로 AttributeValue 생성
                                new_attr_value = AttributeValue.objects.create(
                                    row=new_row,
                                    attribute=source_value.attribute,
                                    value=json.dumps(new_file_data, ensure_ascii=False),
                                    copy_from=source_row.id  # 원본 행 ID 저장
                                )
                                print(f"새 AttributeValue 생성 완료: ID {new_attr_value.id}")
                            else:
                                # S3 복사 실패 시 새로운 파일명으로 원본 파일 정보 복사
                                error_msg = '알 수 없는 오류'
                                if isinstance(copy_result, dict):
                                    error_msg = copy_result.get('error', '알 수 없는 오류')
                                print(f"파일 복사 실패, 새로운 파일명으로 원본 정보 복사: {error_msg}")
                                
                                # 새로운 파일명으로 원본 파일 정보 복사
                                new_file_data = {
                                    'original_filename': original_filename,
                                    'stored_filename': new_filename,  # 새로운 파일명 사용
                                    's3_key': s3_key,  # 원본 S3 키 유지
                                    'download_url': file_data.get('download_url', ''),
                                    'preview_url': file_data.get('preview_url', ''),
                                    'public_url': file_data.get('public_url', ''),
                                    'file_size': file_data.get('file_size', 0),
                                    'content_type': file_data.get('content_type', ''),
                                    'type': file_data.get('type', 'file')
                                }
                                
                                AttributeValue.objects.create(
                                    row=new_row,
                                    attribute=source_value.attribute,
                                    value=json.dumps(new_file_data, ensure_ascii=False),
                                    copy_from=source_row.id  # 원본 행 ID 저장
                                )
                                print(f"원본 파일 정보로 새 AttributeValue 생성 완료")
                        else:
                            # 파일 정보가 없거나 불완전한 경우 원본 그대로 복사
                            print(f"파일 정보 불완전, 원본 그대로 복사")
                            AttributeValue.objects.create(
                                row=new_row,
                                attribute=source_value.attribute,
                                value=source_value.value,
                                copy_from=source_row.id  # 원본 행 ID 저장
                            )
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        # JSON 파싱 실패 시 원본 그대로 복사
                        print(f"파일 정보 파싱 실패, 원본 그대로 복사: {e}")
                        AttributeValue.objects.create(
                            row=new_row,
                            attribute=source_value.attribute,
                            value=source_value.value,
                            copy_from=source_row.id  # 원본 행 ID 저장
                        )
                else:
                    # 파일이 아닌 경우 원본 그대로 복사
                    print(f"일반 속성 복사: {source_value.attribute.name if source_value.attribute else 'None'}")
                    AttributeValue.objects.create(
                        row=new_row,
                        attribute=source_value.attribute,
                        value=source_value.value,
                        copy_from=source_row.id  # 원본 행 ID 저장
                    )
                print(f"=== AttributeValue 복사 완료 ===")
            except Exception as e:
                # 개별 AttributeValue 복사 중 오류가 발생해도 계속 진행
                print(f"AttributeValue 복사 중 오류 발생: {e}")
                continue
        
        print(f"복제 완료: 새 행 ID {new_row.id}")
        
        return JsonResponse({
            'success': True, 
            'message': '행이 성공적으로 복제되었습니다.',
            'new_row_id': new_row.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'복제 중 오류가 발생했습니다: {str(e)}'})

def copy_s3_file(source_s3_key, new_filename):
    """S3에서 파일을 복사하는 함수"""
    print(f"=== S3 파일 복사 시작 ===")
    print(f"소스 S3 키: {source_s3_key}")
    print(f"새 파일명: {new_filename}")
    
    try:
        # S3 클라이언트 생성
        print("S3 클라이언트 생성 중...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        print("S3 클라이언트 생성 완료")
        
        # 새로운 S3 키 생성
        new_s3_key = f"{settings.AWS_LOCATION}/{new_filename}"
        print(f"새 S3 키: {new_s3_key}")
        
        # S3에서 파일 복사
        print("S3 파일 복사 실행 중...")
        s3_client.copy_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CopySource={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': source_s3_key},
            Key=new_s3_key
        )
        print("S3 파일 복사 완료")
        
        # 새로운 다운로드 URL 생성
        new_download_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{new_s3_key}"
        print(f"새 다운로드 URL: {new_download_url}")
        
        # 새로운 서명된 다운로드 URL 생성
        try:
            print("서명된 다운로드 URL 생성 중...")
            new_signed_download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': new_s3_key
                },
                ExpiresIn=300  # 5분
            )
            print("서명된 다운로드 URL 생성 완료")
        except Exception as e:
            print(f"새로운 서명된 다운로드 URL 생성 실패: {e}")
            new_signed_download_url = new_download_url
        
        # 새로운 서명된 미리보기 URL 생성
        try:
            print("서명된 미리보기 URL 생성 중...")
            new_signed_preview_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': new_s3_key,
                    'ResponseContentDisposition': 'inline'
                },
                ExpiresIn=300  # 5분
            )
            print("서명된 미리보기 URL 생성 완료")
        except Exception as e:
            print(f"새로운 서명된 미리보기 URL 생성 실패: {e}")
            new_signed_preview_url = new_download_url
        
        # 현재 시간을 ISO 형식으로 생성
        current_time = timezone.now().isoformat()
        
        result = {
            'success': True,
            'new_s3_key': new_s3_key,
            'new_download_url': new_signed_download_url,
            'new_preview_url': new_signed_preview_url,
            'new_public_url': new_download_url,
            'upload_time': current_time  # upload_time 필드 추가
        }
        print(f"S3 파일 복사 성공: {result}")
        return result
        
    except Exception as e:
        print(f"S3 파일 복사 실패: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@require_GET
def get_status_tabs(request):
    """상태 속성의 드롭다운 옵션들을 반환하는 API (탭 생성용)"""
    try:
        user = User.objects.get(id=1)
        
        # "상태" 속성 찾기 (없으면 "영업진행" 사용)
        status_attr = Attribute.objects.filter(
            user=user, 
            name='상태', 
            attributeType__name='dropdown'
        ).first()
        
        if not status_attr:
            # "상태" 속성이 없으면 "영업진행" 속성 사용
            status_attr = Attribute.objects.filter(
                user=user, 
                name='영업진행', 
                attributeType__name='dropdown'
            ).first()
        
        if not status_attr:
            return JsonResponse({
                'success': False,
                'error': '상태 또는 영업진행 속성을 찾을 수 없습니다.'
            })
        
        # 드롭다운 옵션들 가져오기
        dropdown_options = DropdownAttribute.objects.filter(attribute=status_attr).order_by('id')
        
        options_data = []
        for option in dropdown_options:
            options_data.append({
                'id': option.id,
                'name': option.option,
                'color': option.color
            })
        
        return JsonResponse({
            'success': True,
            'attribute_name': status_attr.name,
            'options': options_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

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
        
        user = User.objects.get(id=1)
        
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

def sync_cascade_attributes(row_id, attribute_name, new_value):
    """cascade가 true인 속성이 수정될 때 원본 행과 복제된 행들을 동기화"""
    try:
        # 사용자 가져오기
        user = User.objects.get(id=1)
        
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
        user = User.objects.get(id=1)
        
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
        user = User.objects.get(id=1)
        
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

@require_GET
def fix_existing_row_relationships(request):
    """기존 행들의 복제 관계를 수정하는 함수 (디버깅용)"""
    try:
        user = User.objects.get(id=1)
        
        # 모든 행을 가져와서 복제 관계 확인
        rows = Row.objects.filter(user=user).order_by('id')
        
        fixed_count = 0
        for row in rows:
            print(f"행 {row.id} 처리 중...")
            print(f"  - original_row_ids: {row.original_row_ids}")
            print(f"  - copied_row_ids: {row.copied_row_ids}")
            
            # copy_from이 있는 AttributeValue들을 찾아서 복제 관계 설정
            attr_values = AttributeValue.objects.filter(row=row, copy_from__gt=0)
            
            for attr_value in attr_values:
                original_row_id = attr_value.copy_from
                print(f"  - copy_from: {original_row_id}")
                
                try:
                    original_row = Row.objects.get(id=original_row_id)
                    
                    # 원본 행의 copied_row_ids에 현재 행 추가
                    if row.id not in original_row.copied_row_ids:
                        original_row.add_copied_row(row.id)
                        print(f"    → 원본 행 {original_row_id}에 복제된 행 {row.id} 추가")
                    
                    # 현재 행의 original_row_ids에 원본 행 추가
                    if original_row_id not in row.original_row_ids:
                        row.add_original_row(original_row_id)
                        print(f"    → 복제된 행 {row.id}에 원본 행 {original_row_id} 추가")
                    
                    fixed_count += 1
                    
                except Row.DoesNotExist:
                    print(f"    → 원본 행 {original_row_id}를 찾을 수 없습니다.")
                    continue
        
        print(f"총 {fixed_count}개의 복제 관계가 수정되었습니다.")
        
        return JsonResponse({
            'success': True,
            'message': f'{fixed_count}개의 복제 관계가 수정되었습니다.'
        })
        
    except Exception as e:
        print(f"복제 관계 수정 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'복제 관계 수정 중 오류가 발생했습니다: {str(e)}'
        })

@require_GET
def debug_row_relationships(request):
    """행들의 복제 관계를 디버깅하는 함수"""
    try:
        user = User.objects.get(id=1)
        
        # 모든 행을 가져와서 복제 관계 확인
        rows = Row.objects.filter(user=user).order_by('id')
        
        debug_info = []
        for row in rows:
            # copy_from이 있는 AttributeValue 개수 확인
            attr_values_with_copy = AttributeValue.objects.filter(row=row, copy_from__gt=0)
            
            debug_info.append({
                'row_id': row.id,
                'original_row_ids': row.original_row_ids,
                'copied_row_ids': row.copied_row_ids,
                'copy_from_count': attr_values_with_copy.count(),
                'copy_from_values': list(attr_values_with_copy.values_list('copy_from', flat=True))
            })
        
        return JsonResponse({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'디버깅 중 오류가 발생했습니다: {str(e)}'
        })

@require_GET
def setup_test_cascade_attributes(request):
    """테스트용 cascade 속성을 설정하는 함수"""
    try:
        user = User.objects.get(id=1)
        
        # 테스트할 속성들
        test_attributes = ['회사명', '매출', '업종', '직원수']
        
        updated_count = 0
        for attr_name in test_attributes:
            try:
                attribute = Attribute.objects.get(name=attr_name, user=user)
                if not attribute.cascade:
                    attribute.cascade = True
                    attribute.save()
                    updated_count += 1
                    print(f"'{attr_name}' 속성의 cascade를 활성화했습니다.")
            except Attribute.DoesNotExist:
                print(f"'{attr_name}' 속성을 찾을 수 없습니다.")
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'{updated_count}개의 속성에 cascade가 활성화되었습니다.',
            'updated_attributes': test_attributes[:updated_count]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Cascade 속성 설정 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def preview_excel(request):
    """엑셀 파일 미리보기 및 필드 매핑"""
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('file')
            if not excel_file:
                return JsonResponse({'success': False, 'error': '파일이 없습니다.'})
            
            if not excel_file.name.endswith('.xlsx'):
                return JsonResponse({'success': False, 'error': '엑셀 파일(.xlsx)만 지원합니다.'})
            
            # 엑셀 파일 읽기
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            # NaN 값을 빈 문자열로 변환
            df = df.fillna('')
            
            # 첫 10행만 미리보기용으로 사용
            preview_data = []
            for index, row in df.head(10).iterrows():
                row_dict = {}
                for column in df.columns:
                    value = row[column]
                    # NaN, None, 빈 값 처리
                    if pd.isna(value) or value is None or value == '':
                        row_dict[column] = ''
                    else:
                        # 숫자형 데이터를 문자열로 변환
                        row_dict[column] = str(value)
                preview_data.append(row_dict)
            
            # 사용자의 속성 목록 가져오기
            user = User.objects.get(id=1)  # 임시로 고정
            attributes = Attribute.objects.filter(user=user).values_list('name', flat=True)
            attribute_names = list(attributes)
            
            # 필드 매핑 생성 (엑셀 열 이름과 속성명 비교)
            mapping = {}
            for column in df.columns:
                if column in attribute_names:
                    mapping[column] = column
                else:
                    # 부분 일치 검색
                    for attr_name in attribute_names:
                        if column.lower() in attr_name.lower() or attr_name.lower() in column.lower():
                            mapping[column] = attr_name
                            break
            
            return JsonResponse({
                'success': True,
                'preview_data': preview_data,
                'mapping': mapping,
                'total_rows': len(df)
            })
            
        except Exception as e:
            print(f"엑셀 미리보기 오류: {str(e)}")
            return JsonResponse({'success': False, 'error': f'파일 처리 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})

@csrf_exempt
def upload_excel(request):
    """엑셀 파일 업로드 및 데이터 처리"""
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('file')
            if not excel_file:
                return JsonResponse({'success': False, 'error': '파일이 없습니다.'})
            
            if not excel_file.name.endswith('.xlsx'):
                return JsonResponse({'success': False, 'error': '엑셀 파일(.xlsx)만 지원합니다.'})
            
            # 엑셀 파일 읽기
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            # 사용자 정보
            user = User.objects.get(id=1)  # 임시로 고정
            
            # 사용자의 속성 목록 가져오기
            attributes = Attribute.objects.filter(user=user)
            attribute_dict = {attr.name: attr for attr in attributes}
            
            # 필드 매핑 생성
            mapping = {}
            for column in df.columns:
                if column in attribute_dict:
                    mapping[column] = column
                else:
                    # 부분 일치 검색
                    for attr_name in attribute_dict.keys():
                        if column.lower() in attr_name.lower() or attr_name.lower() in column.lower():
                            mapping[column] = attr_name
                            break
            
            added_count = 0
            
            # 각 행을 처리
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # 새 Row 생성
                        max_order = Row.objects.aggregate(max_order=models.Max('order'))['max_order']
                        new_order = (max_order + 1) if max_order is not None else 0
                        
                        new_row = Row.objects.create(order=new_order, user=user)
                        
                        # 매핑된 필드에 대해 AttributeValue 생성
                        for excel_column, value in row.items():
                            if pd.isna(value):  # NaN 값 건너뛰기
                                continue
                                
                            mapped_attr_name = mapping.get(excel_column)
                            if mapped_attr_name and mapped_attr_name in attribute_dict:
                                attr = attribute_dict[mapped_attr_name]
                                
                                # 값 처리
                                if attr.attributeType and attr.attributeType.name == 'dropdown':
                                    # 드롭다운의 경우 옵션 ID로 변환
                                    try:
                                        dropdown_option = DropdownAttribute.objects.filter(
                                            attribute=attr, 
                                            option__icontains=str(value)
                                        ).first()
                                        if dropdown_option:
                                            value_to_save = str(dropdown_option.id)
                                        else:
                                            # 옵션이 없으면 새로 생성 (color는 모델의 default=random_color 사용)
                                            dropdown_option = DropdownAttribute.objects.create(
                                                attribute=attr,
                                                option=str(value)
                                            )
                                            value_to_save = str(dropdown_option.id)
                                    except Exception as e:
                                        print(f"드롭다운 처리 오류: {str(e)}")
                                        continue
                                else:
                                    value_to_save = str(value)
                                
                                # AttributeValue 생성
                                AttributeValue.objects.create(
                                    row=new_row,
                                    attribute=attr,
                                    value=value_to_save
                                )
                        
                        added_count += 1
                        
                    except Exception as e:
                        print(f"행 {index + 1} 처리 오류: {str(e)}")
                        continue
            
            return JsonResponse({
                'success': True,
                'added_count': added_count,
                'message': f'{added_count}개 행이 성공적으로 추가되었습니다.'
            })
            
        except Exception as e:
            print(f"엑셀 업로드 오류: {str(e)}")
            return JsonResponse({'success': False, 'error': f'파일 처리 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})

@require_GET
def get_kanban_data(request):
    """특정 dropdown 속성에 대한 칸반보드 데이터를 반환하는 API"""
    try:
        user = User.objects.get(id=1)
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
            
            user = User.objects.get(id=1)
            
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