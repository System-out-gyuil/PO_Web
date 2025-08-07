from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q, Max
from django.core.paginator import Paginator
from django.conf import settings

from .models import (
    DiaryEntry, Category, Region, SalesStatus, BaseAttribute, 
    Attribute, AttributeValue, User, DropdownAttribute, Row, 
    AttributeType, CalendarSettings, UserAlarm
)
from .funding_calculator import FundingCalculator
from board.models import BizInfo

import json
import random
import re
import time
import uuid
import os
import logging
import base64
import hashlib
import hmac
import mimetypes
import tempfile
import subprocess
from datetime import datetime, timedelta, date
from types import SimpleNamespace
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError
from google.cloud import speech
import io
import requests
import pandas as pd
from openpyxl import load_workbook

from config import (
    GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_APPLICATION_CREDENTIALS2, 
    NAVER_CLOVA_SPEECH_SECRET_KEY, NAVER_CLOVA_SPEECH_INVOKE_URL, 
    OPEN_AI_API_KEY
)

# 분리된 모듈들에서 함수들 import
from .kanban_handlers import get_kanban_data, update_kanban_option_order
from .attribute_handlers import (
    add_attribute, delete_attribute, update_attribute_name,
    toggle_attribute_visibility, update_attribute_visibility,
    get_hidden_attributes, get_all_attributes, get_dropdown_attributes,
    filter_attributes_by_status
)
from .excel_handlers import preview_excel, upload_excel
from .calendar_handlers import get_calendar_settings, save_calendar_settings, calendar_events

from .data_utils import parse_korean_currency, parse_sales_amount, parse_business_data

from .cascade_handlers import toggle_cascade_attribute, get_cascade_attributes_list, sync_cascade_attributes

from .audio_handler import upload_audio_file, get_audio_files_by_date, delete_audio_file, update_audio_file_order
from .calendar_handlers import get_calendar_settings, save_calendar_settings, calendar_events
from .kanban_handlers import get_kanban_data, update_kanban_option_order
from .funding_calculator import FundingCalculator
from .data_utils import parse_korean_currency, parse_sales_amount, parse_business_data, calculate_business_years, formatToKoreanCurrency

logger = logging.getLogger(__name__)

# 로그인 상태 확인 뷰
@require_GET
def check_login_status(request):
    """로그인 상태를 확인하는 API"""
    try:
        # 세션에서 로그인 상태 확인
        is_authenticated = request.session.get('diary_authenticated', False)
        
        return JsonResponse({
            'is_authenticated': is_authenticated,
            'success': True
        })
    except Exception as e:
        logger.error(f'로그인 상태 확인 오류: {e}')
        return JsonResponse({
            'is_authenticated': False,
            'success': False,
            'error': str(e)
        })

# 현재 사용자 ID 반환 뷰
@require_GET
def get_current_user_id(request):
    """현재 로그인된 사용자의 ID를 반환하는 API"""
    try:
        # 세션에서 사용자 ID 확인
        user_id = request.session.get('diary_member_id')
        
        if user_id:
            return JsonResponse({
                'success': True,
                'user_id': str(user_id)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': '로그인되지 않음'
            })
    except Exception as e:
        logger.error(f'사용자 ID 조회 오류: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# 다이어리 목록 및 작성 폼
def diary_list(request):
    host = request.get_host()
    if 'namatji.com' in host:
        return redirect('login')

    # 로그인 상태 확인 강화
    if not request.session.get('diary_authenticated'):
        return redirect('login')
    
    # 사용자 ID 확인
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # 사용자가 존재하지 않는 경우 세션 정리 후 로그인 페이지로 리다이렉트
        request.session.flush()
        return redirect('login')
    
    # URL 파라미터에서 상태 ID 가져오기
    status_id = request.GET.get('status_id', 'all')
    if not status_id or status_id in ['undefined', 'null', None, '']:
        status_id = 'all'
    
    # detail 필터링 추가: 기본적으로 detail=False인 속성만 표시
    show_detail = request.GET.get('detail', '0') == '1'  # detail=1이면 상세 속성도 표시
    
    # 기본 속성 쿼리 (view_select 필터링 제거 - 상태별 필터링에서 처리)
    if show_detail:
        base_attributes = Attribute.objects.filter(user=user).order_by('sort_order', 'id')
        base_user_attributes = Attribute.objects.filter(user=user).order_by('sort_order', 'id')
    else:
        base_attributes = Attribute.objects.filter(user=user, detail=False).order_by('sort_order', 'id')
        base_user_attributes = Attribute.objects.filter(user=user, detail=False).order_by('sort_order', 'id')
    
    # 상태별 필터링 적용
    attributes = filter_attributes_by_status(base_attributes, status_id)
    user_attributes = filter_attributes_by_status(base_user_attributes, status_id)
    
    # 쿼리 최적화: select_related와 prefetch_related 적용
    # 모든 관련 데이터를 한 번에 가져오기
    rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
        'values__attribute__attributeType',
        'values__attribute__dropdown_attributes'
    ).order_by('order')
    
    # 세션 데이터 파싱 최적화 - 한 번만 파싱
    session_data = {
        'column_widths': {},
        'hidden_attributes': [],
        'status_tabs': [],
        'calendar_settings': {}
    }
    
    # 세션 데이터 파싱을 한 번에 처리
    for key, default_value in session_data.items():
        try:
            session_value = request.session.get(key, default_value)
            if isinstance(session_value, str):
                session_data[key] = json.loads(session_value)
            else:
                session_data[key] = session_value
        except (json.JSONDecodeError, TypeError):
            session_data[key] = default_value
    
    # 각 행의 속성 값들을 가져오기 (필터링된 속성만)
    rows_data = []
    # 드롭다운 옵션을 미리 캐시
    dropdown_cache = {}
    
    for row in rows:
        row_values = {}
        # 행의 모든 값들을 딕셔너리로 미리 구성
        row_value_dict = {value.attribute_id: value.value for value in row.values.all()}
        
        for attr in user_attributes:  # 이미 필터링된 속성들만 사용
            value = row_value_dict.get(attr.id, '')
            
            if attr.name == '매출' or '매출' in attr.name:
                numeric_value = parse_korean_currency(value)
                row_values[attr.name] = {
                    'label': value,  # 화면 표시용(한글 단위 등)
                    'value': numeric_value,  # 실제 숫자값
                    'color': ''
                }
            elif attr.attributeType and attr.attributeType.name == 'dropdown' and value.isdigit():
                # 드롭다운 캐시 사용
                if attr.id not in dropdown_cache:
                    dropdown_cache[attr.id] = {
                        dropdown_attr.id: dropdown_attr 
                        for dropdown_attr in attr.dropdown_attributes.all()
                    }
                
                dropdown = dropdown_cache[attr.id].get(int(value))
                
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
                    
                    # 드롭다운 캐시 사용
                    if attr.id not in dropdown_cache:
                        dropdown_cache[attr.id] = {
                            dropdown_attr.id: dropdown_attr 
                            for dropdown_attr in attr.dropdown_attributes.all()
                        }
                    
                    for selected_id in selected_ids:
                        dropdown = dropdown_cache[attr.id].get(selected_id)
                        if dropdown:
                            selected_options.append({
                                'id': dropdown.id,
                                'label': dropdown.option,
                                'color': dropdown.color
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
                except json.JSONDecodeError:
                    row_values[attr.name] = {
                        'label': value,
                        'color': '',
                        'raw_value': value,
                        'selected_options': [],
                        'multi_select': True
                    }
            else:
                row_values[attr.name] = {
                    'label': value,
                    'color': '',
                    'raw_value': value
                }
        
        rows_data.append({
            'id': row.id,
            'values': row_values
        })
    
    # 캐시 무효화를 위한 타임스탬프
    cache_timestamp = int(time.time())
    
    # 모든 드롭다운 옵션을 한 번에 수집 (캐시 활용)
    dropdown_options = {}
    for attr in user_attributes:
        if attr.attributeType and attr.attributeType.name == 'dropdown':
            if attr.id in dropdown_cache:
                dropdown_options[attr.name] = [
                    {'id': dropdown_attr.id, 'option': dropdown_attr.option, 'color': dropdown_attr.color, 'order': dropdown_attr.order}
                    for dropdown_attr in dropdown_cache[attr.id].values()
                ]
                # order로 정렬
                dropdown_options[attr.name].sort(key=lambda x: (x['order'], x['id']))
            else:
                dropdown_options[attr.name] = list(attr.dropdown_attributes.values('id', 'option', 'color', 'order').order_by('order'))
    
    context = {
        'rows': rows_data,
        'attributes': [
            {
                'name': attr.name,
                'assential': attr.assential,
                'detail': attr.detail,
                'width': attr.width,
                'attributeType_name': attr.attributeType.name if attr.attributeType else None,
                'dropdown_options': dropdown_options.get(attr.name, [])
            }
            for attr in user_attributes
        ],
        'all_attributes': attributes,
        'column_widths': session_data['column_widths'],
        'hidden_attributes': session_data['hidden_attributes'],
        'status_tabs': session_data['status_tabs'],
        'calendar_settings': session_data['calendar_settings'],
        'cache_timestamp': cache_timestamp,
        'status_id': status_id,
        'show_detail': show_detail,
        'is_authenticated': True,  # 로그인 상태 추가
        'is_admin': user.is_admin,  # 관리자 상태 추가
        'dropdown_options': dropdown_options  # 모든 드롭다운 옵션 추가
    }
    context['attributes_json'] = json.dumps(context['attributes'], ensure_ascii=False)
    context['dropdown_options_json'] = json.dumps(dropdown_options, ensure_ascii=False)  # JSON 형태로도 추가
    
    return render(request, 'diary/diary_list.html', context)

@require_GET
def fu_events(request):
    """이벤트 데이터를 반환하는 API"""
    try:
        # 사용자 정보 가져오기
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        
        # 모든 행 데이터 가져오기 (쿼리 최적화)
        rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
            'values__attribute__attributeType',
            'values__attribute__dropdown_attributes'
        ).order_by('order')
        
        events = []
        for row in rows:
            # 행의 속성값들을 딕셔너리로 미리 구성하여 N+1 쿼리 방지
            row_values = {attr_value.attribute.name: attr_value.value for attr_value in row.values.all() if attr_value.attribute}
            
            # 이벤트 데이터 생성
            event_data = {
                'id': row.id,
                'title': row_values.get('회사명', ''),
                'start': row_values.get('TA일정', ''),
                'end': row_values.get('TA일정', ''),
                'color': '#3788d8'
            }
            events.append(event_data)
        
        return JsonResponse({'events': events})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
    # 로그인 상태 확인
    if not request.session.get('diary_authenticated'):
        return redirect('login')
    
    # 사용자 ID 확인
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # 사용자가 존재하지 않는 경우 세션 정리 후 로그인 페이지로 리다이렉트
        request.session.flush()
        return redirect('login')
     
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Row not found'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid row ID'})
            
        try:
            attr = Attribute.objects.get(name=field, user=user)
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
        # AttributeValue 조회 또는 생성 - 중복 저장 방지
        try:
            with transaction.atomic():
                # 동시 요청으로 인한 중복 방지를 위해 기존 레코드 모두 삭제 후 새로 생성
                existing_records = AttributeValue.objects.filter(row=row, attribute=attr)
                
                if existing_records.exists():
                    # 기존 레코드가 있으면 모두 삭제
                    existing_records.delete()
                    print(f"기존 AttributeValue 레코드 삭제: {field_name}")
                
                # 새 레코드 생성
                attr_value = AttributeValue.objects.create(
                    row=row,
                    attribute=attr,
                    value=value_to_save
                )
                print(f"새 AttributeValue 생성: {field_name} = {value_to_save}")
                
        except Exception as e:
            print(f"AttributeValue 처리 중 오류: {e}")
            return JsonResponse({'success': False, 'error': f'속성 값 저장 중 오류: {str(e)}'})
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_entry) ===")
            print(f"속성 '{field}'의 cascade 값: {attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {value_to_save}")
            
            synced_count = sync_cascade_attributes(request, row_id, field, value_to_save)
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
        
        print(f"=== 새 행 생성 요청 ===")
        print(f"field: {field}")
        print(f"value: {value}")
        print(f"status_field: {status_field}")
        print(f"status_value: {status_value}")
        
        if not field:
            return JsonResponse({'success': False, 'error': 'Missing field'})
            
         
        user_id = request.session.get('diary_member_id')
        print(f"user_id: {user_id}")

        user = User.objects.get(id=user_id)
        
        # 새 Row 생성 (가장 위에 추가하도록 변경)
        # 기존 모든 행들의 order를 1씩 증가
        Row.objects.filter(user=user).update(order=models.F('order') + 1)
        
        # 새 행은 order=0으로 가장 위에 추가
        new_row = Row.objects.create(order=0, user=user)
        print(f"새 행 생성됨: row_id={new_row.id}, order=0 (가장 위에 추가)")
        
        # 첫 번째 필드 값 설정
        try:
            attr = Attribute.objects.get(name=field, user=user)
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
        print(f"첫 번째 필드 값 설정: {field}={value_to_save}")
        
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
                print(f"상태 필드 값 설정: {status_field}={status_value_to_save}")
            except Exception as e:
                print(f"상태 필드 생성 오류: {e}")
        
        print(f"=== 새 행 생성 완료: row_id={new_row.id} ===")
        return JsonResponse({'success': True, 'id': new_row.id})
        
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def update_row_field(request):
    if request.method == 'POST':
        print("===========update_row_field===========")
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
            
            print(f"=== update_row_field 디버그 ===")
            print(f"row_id: {row_id}")
            print(f"field_name: {field_name}")
            print(f"value: '{value}' (type: {type(value)})")
            print(f"value length: {len(str(value)) if value else 0}")
            print(f"value is empty: {value == ''}")
            print(f"value is None: {value is None}")
            print(f"========================")
            
            # 사용자와 행 조회
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
                
                # 빈 값 처리
                if value == '' or value is None:
                    print(f"  빈 값 처리 - 빈 문자열로 저장")
                    value_to_save = ''
                elif value.isdigit():
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
                    # 다른 형태
                    print(f"  다른 형태: '{value}'")
                    value_to_save = value

            else:
                value_to_save = str(value)
            
            # AttributeValue 조회 또는 생성 - 중복 저장 방지
            try:
                with transaction.atomic():
                    # 동시 요청으로 인한 중복 방지를 위해 기존 레코드 모두 삭제 후 새로 생성
                    existing_records = AttributeValue.objects.filter(row=row, attribute=attr)
                    
                    if existing_records.exists():
                        # 기존 레코드가 있으면 모두 삭제
                        existing_records.delete()
                        print(f"기존 AttributeValue 레코드 삭제: {field_name}")
                    
                    # 새 레코드 생성
                    attr_value = AttributeValue.objects.create(
                        row=row,
                        attribute=attr,
                        value=value_to_save
                    )
                    print(f"새 AttributeValue 생성: {field_name} = {value_to_save}")
                    
            except Exception as e:
                print(f"AttributeValue 처리 중 오류: {e}")
                return JsonResponse({'success': False, 'error': f'속성 값 저장 중 오류: {str(e)}'})
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if attr.cascade:
                print(f"=== Cascade 동기화 시작 ===")
                print(f"속성 '{field_name}'의 cascade 값: {attr.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {value_to_save}")
                
                synced_count = sync_cascade_attributes(request, row_id, field_name, value_to_save)
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
    
    # 사용자 정보 가져오기
    user_id = request.session.get('diary_member_id')
    user = User.objects.get(id=user_id)
    
    try:
        attr = Attribute.objects.get(name=field, user=user)
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
                # 색상이 제공되지 않으면 랜덤 색상 생성
                random_generated_color = random_color()
                dropdown, created = DropdownAttribute.objects.get_or_create(attribute=attr, option=option, defaults={'color': random_generated_color})
            
            # 상태 속성인 경우 view_select에 자동 추가
            if attr.name == '상태' or attr.name == '영업진행':
                # 해당 사용자의 모든 Attribute 행들을 가져와서 view_select에 새 옵션 추가
                user_attributes = Attribute.objects.filter(user=user)
                
                for user_attr in user_attributes:
                    # 기존 view_select 데이터 가져오기
                    view_select_data = user_attr.view_select if user_attr.view_select else {}
                    
                    # 새로 추가된 dropdown의 ID를 true로 설정
                    view_select_data[str(dropdown.id)] = True
                    
                    # 전체 탭(0번)도 true로 설정
                    view_select_data['0'] = True
                    
                    # Attribute 업데이트
                    user_attr.view_select = view_select_data
                    user_attr.save()
                
                print(f"상태 속성 '{attr.name}'의 새 옵션 '{dropdown.option}' (ID: {dropdown.id})을 모든 Attribute의 view_select에 추가 + 전체 탭 설정")
            
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
            old_option_name = dropdown.option  # 기존 옵션명 저장
            
            if name:
                dropdown.option = name
            if color:
                dropdown.color = color
            dropdown.save()
            
            # 상태 속성인 경우 view_select 업데이트
            if attr.name == '상태' or attr.name == '영업진행' and name:
                # 옵션 수정 후 모든 옵션들을 view_select에 다시 설정
                view_select_data = {}
                all_dropdown_options = DropdownAttribute.objects.filter(attribute=attr).order_by('id')
                
                for dropdown_option in all_dropdown_options:
                    option_id = str(dropdown_option.id)
                    # 모든 옵션을 true로 설정 (전체 탭 포함)
                    view_select_data[option_id] = True
                
                # 전체 탭(0번)도 true로 설정
                view_select_data['0'] = True
                
                attr.view_select = view_select_data
                attr.save()
                
                print(f"상태 속성 '{attr.name}'의 view_select 재설정: {len(all_dropdown_options)}개 옵션 + 전체 탭")
            
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
        
        # 상태 속성인 경우 view_select에서 해당 옵션 제거
        if attr.name == '상태' or attr.name == '영업진행':
            # 삭제할 옵션의 ID 저장
            deleted_option_id = str(dropdown.id)
            
            # 해당 사용자의 모든 Attribute 행들에서 해당 옵션 ID 제거
            user_attributes = Attribute.objects.filter(user=user)
            
            for user_attr in user_attributes:
                view_select_data = user_attr.view_select if user_attr.view_select else {}
                
                if deleted_option_id in view_select_data:
                    del view_select_data[deleted_option_id]
                    user_attr.view_select = view_select_data
                    user_attr.save()
            
            print(f"상태 속성 '{attr.name}'의 옵션 '{dropdown.option}' (ID: {deleted_option_id})을 모든 Attribute의 view_select에서 제거")
            
            # DropdownAttribute 삭제
            dropdown.delete()
        else:
            # DropdownAttribute 삭제
            dropdown.delete()
        
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
        
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid method'}, status=405)


@require_GET
def get_row_details(request, row_id):
    try:
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
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
        
        # 드롭다운 옵션을 미리 캐시하여 N+1 쿼리 방지
        dropdown_cache = {}
        for attr_value in row.values.all():
            if (attr_value.attribute and 
                attr_value.attribute.attributeType and 
                attr_value.attribute.attributeType.name == 'dropdown'):
                attr_id = attr_value.attribute.id
                if attr_id not in dropdown_cache:
                    dropdown_cache[attr_id] = {
                        dropdown_attr.id: dropdown_attr.option 
                        for dropdown_attr in attr_value.attribute.dropdown_attributes.all()
                    }
        
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
                    # 드롭다운 타입인 경우 텍스트 값으로 변환 (캐시 활용)
                    if attr_value.attribute.attributeType and attr_value.attribute.attributeType.name == 'dropdown':
                        if value and value.isdigit():
                            # 캐시된 dropdown 데이터에서 찾기
                            attr_id = attr_value.attribute.id
                            dropdown_options = dropdown_cache.get(attr_id, {})
                            value = dropdown_options.get(int(value), value)
                        elif value and value.startswith('[') and value.endswith(']'):
                            # 리스트 형태의 값인 경우 (예: [27]) 첫 번째 값만 추출
                            try:
                                import ast
                                list_value = ast.literal_eval(value)
                                if isinstance(list_value, list) and len(list_value) > 0:
                                    dropdown_id = list_value[0]
                                    # 캐시된 dropdown 데이터에서 찾기
                                    attr_id = attr_value.attribute.id
                                    dropdown_options = dropdown_cache.get(attr_id, {})
                                    value = dropdown_options.get(dropdown_id, str(dropdown_id))
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
def get_user_attributes(request):
    """사용자의 속성 목록을 반환하는 API"""
    try:
            
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        # select_related를 추가하여 N+1 쿼리 방지
        # 상세보기 모달용일 경우 detail_sort_order로 정렬, 일반적으로는 sort_order로 정렬
        is_detail_modal = request.GET.get('for_detail_modal', 'false').lower() == 'true'
        
        if is_detail_modal:
            attributes = Attribute.objects.filter(user=user).select_related('attributeType').order_by('detail_sort_order', 'id')
        else:
            attributes = Attribute.objects.filter(user=user).select_related('attributeType').order_by('-assential', 'id')  # 필수 속성 먼저, 그 다음 id 순
        
        attributes_data = []
        for attr in attributes:
            attr_data = {
                'id': attr.id,
                'name': attr.name,
                'type': attr.attributeType.name if attr.attributeType else 'text',
                'essential': attr.assential,  # essential 정보 추가
                'detail': attr.detail,  # detail 필드 추가
                'sort_order': attr.sort_order,
                'detail_sort_order': attr.detail_sort_order  # detail_sort_order 추가
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


@csrf_exempt
def update_detail_sort_order(request):
    """상세보기 모달에서 속성 순서를 업데이트하는 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user_id = request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'})

        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        attribute_orders = data.get('attribute_orders', [])
        
        # 트랜잭션으로 순서 업데이트
        with transaction.atomic():
            for order_data in attribute_orders:
                attribute_id = order_data.get('id')
                new_order = order_data.get('detail_sort_order')
                
                if attribute_id and new_order is not None:
                    Attribute.objects.filter(id=attribute_id, user=user).update(
                        detail_sort_order=new_order
                    )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attribute.cascade:
                print(f"=== Cascade 동기화 시작 (update_audio_text) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(audio_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(audio_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (update_audio_text) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade} - 동기화하지 않음")
            
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 정보 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attr = Attribute.objects.get(name='음성파일', user=user)
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
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attr.cascade:
                print(f"=== Cascade 동기화 시작 (update_audio_memo) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(audio_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(audio_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (update_audio_memo) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade} - 동기화하지 않음")
            
            logger.info(f"음성파일 메모 업데이트 성공: Row {row_id}, Date {date}, File {file_id}")
            return JsonResponse({'success': True, 'message': '메모가 성공적으로 저장되었습니다.'})
        else:
            return JsonResponse({'success': False, 'error': '해당 음성파일을 찾을 수 없습니다.'})
            
    except Exception as e:
        logger.error(f"음성파일 메모 업데이트 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': f'메모 저장 중 오류가 발생했습니다: {str(e)}'})



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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if expected_loans_attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_expected_loans) ===")
            print(f"속성 '기대출'의 cascade 값: {expected_loans_attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {value}")
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', value)
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 기대출 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_expected_loans) ===")
        else:
            print(f"속성 '기대출'의 cascade 값: {expected_loans_attr.cascade} - 동기화하지 않음")
        
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
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
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if expected_loans_attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_loan_amount) ===")
            print(f"속성 '기대출'의 cascade 값: {expected_loans_attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {loan_data_str}")
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', loan_data_str)
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 기대출 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_loan_amount) ===")
        else:
            print(f"속성 '기대출'의 cascade 값: {expected_loans_attr.cascade} - 동기화하지 않음")
        
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if debt_attribute.cascade:
            print(f"=== Cascade 동기화 시작 (update_debt_field) ===")
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(debt_data)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', json.dumps(debt_data))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 기대출 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_debt_field) ===")
        else:
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade} - 동기화하지 않음")
        
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
            attr_value = AttributeValue.objects.filter(row=row, attribute=debt_attribute).first()
            
            # JSON 데이터 파싱
            try:
                debt_data = json.loads(attr_value.value) if attr_value and attr_value.value else {}
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if debt_attribute.cascade:
            print(f"=== Cascade 동기화 시작 (save_debt_details) ===")
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(debt_data)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', json.dumps(debt_data))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 기대출 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (save_debt_details) ===")
        else:
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade} - 동기화하지 않음")
        
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
        biz_reception = ""

        for biz in biz_data:
            print(f'biz.reception_start : {biz.reception_start}')
            print(f'biz.reception_end : {biz.reception_end}')
            
            # DateField 객체를 문자열로 변환하여 비교
            start_str = str(biz.reception_start) if biz.reception_start else '1900-01-01'
            end_str = str(biz.reception_end) if biz.reception_end else '9999-12-31'
            
            if start_str == '1900-01-01' and end_str == '9999-12-31':
                biz_reception = "상시접수"
            elif start_str == '1900-01-01' and end_str != '9999-12-31':
                biz_reception = f"{end_str} 까지 접수"
            elif start_str != '1900-01-01' and end_str == '9999-12-31':
                biz_reception = f"{start_str} 부터 자금 소진시까지 접수"
            else:
                biz_reception = f"{start_str} ~ {end_str}"
            
            print(f'biz_reception : {biz_reception}')


            print(f'biz_data : {biz.pblanc_id}')
            pblanc_ids.append(biz.pblanc_id)
            recommended_notices.append({
                'pblanc_id': biz.pblanc_id,
                'title': biz.title,
                'institution': biz.institution_name,
                'apply_period': biz_reception,
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
        attr_value = AttributeValue.objects.filter(row=row, attribute=attribute).first()
        return attr_value.value if attr_value else None
    except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
        return None


def _get_debt_data(user, row):
    """기대출 데이터를 가져오는 헬퍼 함수"""
    try:
        attribute = Attribute.objects.get(user=user, name='기대출')
        attr_value = AttributeValue.objects.filter(row=row, attribute=attribute).first()
        
        if attr_value and attr_value.value:
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
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
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if audio_attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_audio_text_notes) ===")
            print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(data, ensure_ascii=False)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(data, ensure_ascii=False))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_audio_text_notes) ===")
        else:
            print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade} - 동기화하지 않음")
        
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

         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
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

        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_audio_file_order_and_notes) ===")
            print(f"속성 '음성파일'의 cascade 값: {attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(value, ensure_ascii=False)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(value, ensure_ascii=False))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_audio_file_order_and_notes) ===")
        else:
            print(f"속성 '음성파일'의 cascade 값: {attr.cascade} - 동기화하지 않음")

        print("=== update_audio_file_order_and_notes 완료 ===")
        return JsonResponse({'success': True})

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def entry_table_partial(request):
    # 로그인 상태 확인
    if not request.session.get('diary_authenticated'):
        return redirect('login')
    
    # 사용자 ID 확인
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # 사용자가 존재하지 않는 경우 세션 정리 후 로그인 페이지로 리다이렉트
        request.session.flush()
        return redirect('login')
    
    # URL 파라미터에서 상태 ID 가져오기
    status_id = request.GET.get('status_id', 'all')
    if not status_id or status_id in ['undefined', 'null', None, '']:
        status_id = 'all'
    
    # 기본 속성 쿼리
    base_attributes = Attribute.objects.filter(user=user, detail=False).select_related('attributeType').order_by('sort_order', 'id')
    
    # 상태별 필터링 적용
    user_attributes = filter_attributes_by_status(base_attributes, status_id)
    
    # 행 데이터도 상태별로 필터링
    rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
        'values__attribute__attributeType',
        'values__attribute__dropdown_attributes'
    ).order_by('order')
    
    # 상태별로 행 필터링 추가
    if status_id != 'all':
        # 상태 속성 찾기
        status_attribute = Attribute.objects.filter(user=user, name='상태').first()
        if status_attribute:
            # 해당 상태를 가진 행들만 필터링 (distinct 추가로 중복 방지)
            rows = rows.filter(values__attribute=status_attribute, values__value=status_id).distinct()
            print(f"상태 필터링 적용: status_id={status_id}, 필터링된 행 수: {rows.count()}")
        else:
            print(f"상태 속성을 찾을 수 없음: status_id={status_id}")
    else:
        print(f"전체 상태 표시: status_id={status_id}, 전체 행 수: {rows.count()}")
    
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
    
    attributes_list = [
        {
            'name': attr.name,
            'attributeType_name': attr.attributeType.name if attr.attributeType else '',
            'assential': attr.assential,
            'width': attr.width,
        }
        for attr in user_attributes
    ]

    # 캐시 헤더 추가로 브라우저 캐싱 비활성화 (새 행 생성 후 즉시 반영을 위해)
    response = render(request, 'diary/entry_table_partial.html', {
        'attributes': attributes_list,
        'rows': rows_data,
    })
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # 캐시 비활성화
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response



@csrf_exempt
def upload_note_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        row_id = request.POST.get('row_id')
        if not file or not row_id:
            return JsonResponse({'success': False, 'error': '파일 또는 row_id 누락'})
        
        # 파일 크기 제한 (20MB)
        max_file_size = 20 * 1024 * 1024  # 20MB
        if file.size > max_file_size:
            return JsonResponse({'success': False, 'error': '파일 크기가 20MB를 초과합니다.'})
        
        # 파일 해시 계산 (업로드 전에 먼저 계산)
        import hashlib
        file_hash = None
        try:
            hash_md5 = hashlib.md5()
            file.seek(0)
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
            file.seek(0)
            file_hash = hash_md5.hexdigest()
        except Exception as e:
            print(f"파일 해시 계산 실패: {e}")
        
        # === DB 저장 로직 추가 ===
        from .models import User, Row, Attribute, AttributeValue
        import json
        from django.db import transaction
        from django.db.models import Q

        user_id = request.session.get('diary_member_id')

        try:
            with transaction.atomic():
                user = User.objects.get(id=user_id)
                row = Row.objects.get(id=row_id, user=user)
                attr = Attribute.objects.get(name='음성파일', user=user)
                
                # 중복 데이터 문제 해결: get_or_create 대신 filter().first() 사용
                attr_value = AttributeValue.objects.filter(row=row, attribute=attr).first()
                if not attr_value:
                    attr_value = AttributeValue.objects.create(row=row, attribute=attr, value='{"data": {}}')
                
                # 기존 값이 있으면 파싱, 없으면 빈 dict
                try:
                    value_dict = json.loads(attr_value.value) if attr_value.value else {"data": {}}
                except Exception:
                    value_dict = {"data": {}}
                
                # 파일 해시 기반 중복 체크
                existing_files = value_dict.get("data", {})
                duplicate_file_id = None
                for fid, file_data in existing_files.items():
                    if (file_data.get('original_filename') == file.name and 
                        file_data.get('file_size') == file.size and
                        file_data.get('file_hash') == file_hash):
                        duplicate_file_id = fid
                        break
                
                if duplicate_file_id:
                    # 중복 파일이 이미 존재하는 경우 기존 파일 정보 반환
                    existing_file_info = existing_files[duplicate_file_id]
                    return JsonResponse({
                        'success': True, 
                        'file_info': existing_file_info, 
                        'file_id': duplicate_file_id,
                        'message': '이미 업로드된 파일입니다.'
                    })
                
                # S3 업로드
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
                    'file_hash': file_hash,  # 파일 해시 추가
                    'last_modified': file.last_modified if hasattr(file, 'last_modified') else None
                }
                # 파일 타입 판별
                if file.content_type.startswith('image/'):
                    file_info['type'] = 'image'
                elif file.content_type.startswith('audio/'):
                    file_info['type'] = 'audio'
                else:
                    file_info['type'] = 'file'
                
                # 고유 id 생성 (더 정확한 타임스탬프 사용)
                import time
                file_id = f'f{int(time.time()*1000000)}'  # 마이크로초 단위로 더 정확하게
                
                # order 필드 추가 (기존 아이템 개수 + 1)
                existing_count = len(value_dict.get("data", {}))
                file_info['order'] = existing_count
                
                value_dict["data"][file_id] = file_info
                attr_value.value = json.dumps(value_dict, ensure_ascii=False)
                attr_value.save()
                
                # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
                if attr.cascade:
                    print(f"=== Cascade 동기화 시작 (upload_note_file) ===")
                    print(f"속성 '음성파일'의 cascade 값: {attr.cascade}")
                    print(f"수정된 행 ID: {row_id}")
                    print(f"새 값: {json.dumps(value_dict, ensure_ascii=False)}")
                    
                    synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(value_dict, ensure_ascii=False))
                    if synced_count > 0:
                        print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                    else:
                        print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                    print(f"=== Cascade 동기화 종료 (upload_note_file) ===")
                else:
                    print(f"속성 '음성파일'의 cascade 값: {attr.cascade} - 동기화하지 않음")
                
                return JsonResponse({'success': True, 'file_info': file_info, 'file_id': file_id})
                
        except Exception as e:
            print(f"파일 업로드 중 오류: {e}")
            return JsonResponse({'success': False, 'error': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'})
    
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attr.cascade:
                print(f"=== Cascade 동기화 시작 (delete_note_file) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(current_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(current_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (delete_note_file) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade} - 동기화하지 않음")
            
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            
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
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attribute.cascade:
                print(f"=== Cascade 동기화 시작 (update_note_order_and_notes) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(existing_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(existing_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (update_note_order_and_notes) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade} - 동기화하지 않음")
            
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
            
            content_type = file_info.get('content_type', '')
            original_filename = file_info.get('original_filename', '')
            
            # HWP/HWPX 파일인 경우 PDF로 변환
            if (content_type in ['application/x-hwp', 'application/haansofthwp', 'application/vnd.hancom.hwp'] or
                original_filename.lower().endswith(('.hwp', '.hwpx'))):
                
                print(f"HWP/HWPX 파일 감지: {original_filename}")
                
                # LibreOffice 상태 확인
                if not check_libreoffice_status():
                    return JsonResponse({'success': False, 'error': '파일 변환에 실패했습니다.'})
                
                try:
                    # S3에서 파일 다운로드
                    temp_file_path = download_file_from_s3_for_preview(s3_key)
                    if not temp_file_path:
                        return JsonResponse({'success': False, 'error': '파일 다운로드에 실패했습니다.'})
                    
                    # HWP를 PDF로 변환
                    pdf_path = convert_hwp_to_pdf(temp_file_path)
                    if not pdf_path or not os.path.exists(pdf_path):
                        # 임시 파일 정리
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        return JsonResponse({'success': False, 'error': 'HWP 파일을 PDF로 변환하는데 실패했습니다.'})
                    
                    # 변환된 PDF를 S3에 업로드하고 미리보기 URL 생성
                    preview_url = upload_pdf_to_s3_for_preview(pdf_path, s3_key)
                    
                    # 임시 파일들 정리
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    
                    if preview_url:
                        return JsonResponse({'success': True, 'preview_url': preview_url, 'converted_to_pdf': True})
                    else:
                        return JsonResponse({'success': False, 'error': 'PDF 미리보기 URL 생성에 실패했습니다.'})
                        
                except Exception as e:
                    # 임시 파일 정리
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if 'pdf_path' in locals() and os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    return JsonResponse({'success': False, 'error': f'HWP 변환 중 오류가 발생했습니다: {str(e)}'})
            
            # 기존 로직 (HWP/HWPX가 아닌 경우)
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
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
        print(f'row_id: {row_id}, field_name: {field_name}')
        
        # file_id 파라미터 추가
        file_id = request.GET.get('file_id')
        print(f'file_id: {file_id}')
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        row = Row.objects.get(id=row_id, user=user)
        attr = Attribute.objects.get(name=field_name, user=user)
        attr_value = AttributeValue.objects.get(row=row, attribute=attr)
        file_data = json.loads(attr_value.value)

        print(f'file_data: {file_data}')
        
        # file_data가 리스트인 경우 file_id에 해당하는 파일 찾기
        if isinstance(file_data, list):
            if file_id:
                # file_id에 해당하는 파일 찾기
                target_file = None
                for file_info in file_data:
                    if (file_info.get('id') == file_id or 
                        file_info.get('stored_filename') == file_id or
                        file_info.get('original_filename') == file_id):
                        target_file = file_info
                        break
                
                if target_file:
                    file_info = target_file
                    print(f'찾은 파일: {file_info}')
                else:
                    print(f'file_id {file_id}에 해당하는 파일을 찾을 수 없음, 첫 번째 파일 사용')
                    if len(file_data) > 0:
                        file_info = file_data[0]
                    else:
                        return JsonResponse({'success': False, 'error': '파일 정보가 없습니다.'})
            else:
                # file_id가 없으면 첫 번째 파일 사용
                if len(file_data) > 0:
                    file_info = file_data[0]
                else:
                    return JsonResponse({'success': False, 'error': '파일 정보가 없습니다.'})
        else:
            # 단일 파일인 경우
            file_info = file_data
        
        s3_key = file_info.get('s3_key')
        if not s3_key:
            return JsonResponse({'success': False, 'error': 'S3 키가 없습니다.'})
        
        content_type = file_info.get('content_type', '')
        original_filename = file_info.get('original_filename', '')
        
        # HWP/HWPX 파일인 경우 PDF로 변환
        if (content_type in ['application/x-hwp', 'application/haansofthwp', 'application/vnd.hancom.hwp'] or
            original_filename.lower().endswith(('.hwp', '.hwpx'))):
            
            print(f"HWP/HWPX 파일 감지: {original_filename}")
            
            # LibreOffice 상태 확인
            if not check_libreoffice_status():
                return JsonResponse({'success': False, 'error': '파일 변환에 실패했습니다.'})
            
            try:
                # S3에서 파일 다운로드
                temp_file_path = download_file_from_s3_for_preview(s3_key)
                if not temp_file_path:
                    return JsonResponse({'success': False, 'error': '파일 다운로드에 실패했습니다.'})
                
                # HWP를 PDF로 변환
                pdf_path = convert_hwp_to_pdf(temp_file_path)
                if not pdf_path or not os.path.exists(pdf_path):
                    # 임시 파일 정리
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return JsonResponse({'success': False, 'error': 'HWP 파일을 PDF로 변환하는데 실패했습니다.'})
                
                # 변환된 PDF를 S3에 업로드하고 미리보기 URL 생성
                preview_url = upload_pdf_to_s3_for_preview(pdf_path, s3_key)
                
                # 임시 파일들 정리
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                if preview_url:
                    return JsonResponse({'success': True, 'preview_url': preview_url, 'converted_to_pdf': True})
                else:
                    return JsonResponse({'success': False, 'error': 'PDF 미리보기 URL 생성에 실패했습니다.'})
                    
            except Exception as e:
                # 임시 파일 정리
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if 'pdf_path' in locals() and os.path.exists(pdf_path):
                    os.remove(pdf_path)
                return JsonResponse({'success': False, 'error': f'HWP 변환 중 오류가 발생했습니다: {str(e)}'})
        
        # 기존 로직 (HWP/HWPX가 아닌 경우)
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
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
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # 소스 행 조회
        source_row = Row.objects.filter(id=source_row_id).first()
        if not source_row:
            return JsonResponse({'success': False, 'error': '복제할 행을 찾을 수 없습니다.'})
        
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
        
        # === 개선된 양방향 관계 설정 ===
        # 1. 새 행의 원본 행 ID들을 설정 (소스 행의 원본 행 ID들 + 소스 행 ID)
        new_original_ids = source_row.original_row_ids.copy()
        new_original_ids.append(source_row.id)
        new_row.original_row_ids = new_original_ids
        new_row.save()
        
        
        # 2. 소스 행의 복제된 행 목록에 새 행 추가
        source_row.add_copied_row(new_row.id)
        
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
                # 파일 타입인 경우 S3에서 파일 복사
                if (source_value.attribute and 
                    source_value.attribute.attributeType and 
                    source_value.attribute.attributeType.name == 'file' and 
                    source_value.value):
                    
                    
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
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
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
def save_column_width(request):
    # 컬럼 너비 저장
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    try:
        data = json.loads(request.body)
        attribute_name = data.get('attribute_name')
        width = data.get('width')
        if not attribute_name or width is None:
            return JsonResponse({'success': False, 'error': 'attribute_name과 width가 필요합니다'})
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        try:
            attribute = Attribute.objects.get(name=attribute_name, user=user)
            attribute.width = width
            attribute.save()
            return JsonResponse({'success': True, 'message': '컬럼 너비가 저장되었습니다.'})
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '속성을 찾을 수 없습니다'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def get_dependent_rows(request):
    """종속된 행들을 반환하는 API"""
    if request.method == 'POST':
        try:
            row_id = request.POST.get('row_id')
            field = request.POST.get('field')
            
            if not row_id or not field:
                return JsonResponse({'success': False, 'error': 'row_id와 field가 필요합니다'})
            
            # 사용자 정보 가져오기
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 현재 행 조회
            try:
                current_row = Row.objects.get(id=row_id, user=user)
            except Row.DoesNotExist:
                return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다'})
            
            dependent_rows = []
            
            # Cascade가 활성화된 속성인지 확인
            try:
                cascade_attribute = Attribute.objects.get(name=field, user=user, cascade=True)
                print(f"Cascade 속성 찾음: {field}")
            except Attribute.DoesNotExist:
                print(f"Cascade 속성을 찾을 수 없습니다: {field}")
                # Cascade가 false인 속성이면 종속된 행들을 찾지 않음
                return JsonResponse({
                    'success': True,
                    'dependent_rows': []
                })
            
            # === 새로운 행 복제 시스템을 사용한 종속된 행들 찾기 ===
            
            # 1. 현재 행의 원본 행들
            original_rows = []
            for original_id in current_row.original_row_ids:
                try:
                    original_row = Row.objects.get(id=original_id, user=user)
                    original_rows.append(original_row)
                except Row.DoesNotExist:
                    print(f"원본 행 {original_id}를 찾을 수 없습니다.")
                    continue
            
            # 2. 현재 행의 복제된 행들
            copied_rows = []
            for copied_id in current_row.copied_row_ids:
                try:
                    copied_row = Row.objects.get(id=copied_id, user=user)
                    copied_rows.append(copied_row)
                except Row.DoesNotExist:
                    print(f"복제된 행 {copied_id}를 찾을 수 없습니다.")
                    continue
            
            # 3. 원본 행들의 복제된 행들도 포함
            for original_row in original_rows:
                for copied_id in original_row.copied_row_ids:
                    try:
                        copied_row = Row.objects.get(id=copied_id, user=user)
                        if copied_row not in copied_rows and copied_row.id != row_id:
                            copied_rows.append(copied_row)
                    except Row.DoesNotExist:
                        continue
            
            # 4. 복제된 행들의 원본 행들도 포함
            for copied_row in copied_rows:
                for original_id in copied_row.original_row_ids:
                    try:
                        original_row = Row.objects.get(id=original_id, user=user)
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
            
            # 각 관련 행에 대해 해당 필드의 값을 가져와서 종속된 행 목록에 추가
            for dep_row in unique_related_rows:
                try:
                    attr_value = AttributeValue.objects.filter(row=dep_row, attribute=cascade_attribute).first()
                    if attr_value:
                        dependent_rows.append({
                            'row_id': dep_row.id,
                            'field': field,
                            'value': attr_value.value
                        })
                        print(f"종속된 행 추가: {dep_row.id}, {field}, {attr_value.value}")
                    else:
                        # 해당 속성의 값이 없으면 빈 값으로 설정
                        dependent_rows.append({
                            'row_id': dep_row.id,
                            'field': field,
                            'value': ''
                        })
                        print(f"종속된 행 추가 (빈 값): {dep_row.id}, {field}")
                except AttributeValue.DoesNotExist:
                    # 해당 속성의 값이 없으면 빈 값으로 설정
                    dependent_rows.append({
                        'row_id': dep_row.id,
                        'field': field,
                        'value': ''
                    })
                    print(f"종속된 행 추가 (빈 값): {dep_row.id}, {field}")
            
            return JsonResponse({
                'success': True,
                'dependent_rows': dependent_rows
            })
            
        except Exception as e:
            print(f"get_dependent_rows 오류: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})

@csrf_exempt
def get_column_widths(request):
    # 컬럼 너비 조회
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'GET method required'})
    try:
        user_id = request.session.get('diary_member_id')
        user = User.objects.get(id=user_id)
        
        # 사용자의 모든 속성에서 width가 설정된 것들만 가져오기
        attributes = Attribute.objects.filter(user=user, width__isnull=False)
        widths = {}
        
        for attribute in attributes:
            if attribute.width:
                widths[attribute.name] = attribute.width
        
        return JsonResponse({
            'success': True, 
            'widths': widths
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def get_dependent_rows(request):
    """종속된 행들을 반환하는 API"""
    if request.method == 'POST':
        try:
            row_id = request.POST.get('row_id')
            field = request.POST.get('field')
            
            if not row_id or not field:
                return JsonResponse({'success': False, 'error': 'row_id와 field가 필요합니다'})
            
            # 사용자 정보 가져오기
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 현재 행 조회
            try:
                current_row = Row.objects.get(id=row_id, user=user)
            except Row.DoesNotExist:
                return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다'})
            
            dependent_rows = []
            
            # Cascade가 활성화된 속성인지 확인
            try:
                cascade_attribute = Attribute.objects.get(name=field, user=user, cascade=True)
                print(f"Cascade 속성 찾음: {field}")
            except Attribute.DoesNotExist:
                print(f"Cascade 속성을 찾을 수 없습니다: {field}")
                # Cascade가 false인 속성이면 종속된 행들을 찾지 않음
                return JsonResponse({
                    'success': True,
                    'dependent_rows': []
                })
            
            # === 새로운 행 복제 시스템을 사용한 종속된 행들 찾기 ===
            
            # 1. 현재 행의 원본 행들
            original_rows = []
            for original_id in current_row.original_row_ids:
                try:
                    original_row = Row.objects.get(id=original_id, user=user)
                    original_rows.append(original_row)
                except Row.DoesNotExist:
                    print(f"원본 행 {original_id}를 찾을 수 없습니다.")
                    continue
            
            # 2. 현재 행의 복제된 행들
            copied_rows = []
            for copied_id in current_row.copied_row_ids:
                try:
                    copied_row = Row.objects.get(id=copied_id, user=user)
                    copied_rows.append(copied_row)
                except Row.DoesNotExist:
                    print(f"복제된 행 {copied_id}를 찾을 수 없습니다.")
                    continue
            
            # 3. 원본 행들의 복제된 행들도 포함
            for original_row in original_rows:
                for copied_id in original_row.copied_row_ids:
                    try:
                        copied_row = Row.objects.get(id=copied_id, user=user)
                        if copied_row not in copied_rows and copied_row.id != row_id:
                            copied_rows.append(copied_row)
                    except Row.DoesNotExist:
                        continue
            
            # 4. 복제된 행들의 원본 행들도 포함
            for copied_row in copied_rows:
                for original_id in copied_row.original_row_ids:
                    try:
                        original_row = Row.objects.get(id=original_id, user=user)
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
            
            # 각 관련 행에 대해 해당 필드의 값을 가져와서 종속된 행 목록에 추가
            for dep_row in unique_related_rows:
                try:
                    attr_value = AttributeValue.objects.filter(row=dep_row, attribute=cascade_attribute).first()
                    if attr_value:
                        dependent_rows.append({
                            'row_id': dep_row.id,
                            'field': field,
                            'value': attr_value.value
                        })
                        print(f"종속된 행 추가: {dep_row.id}, {field}, {attr_value.value}")
                    else:
                        # 해당 속성의 값이 없으면 빈 값으로 설정
                        dependent_rows.append({
                            'row_id': dep_row.id,
                            'field': field,
                            'value': ''
                        })
                        print(f"종속된 행 추가 (빈 값): {dep_row.id}, {field}")
                except AttributeValue.DoesNotExist:
                    # 해당 속성의 값이 없으면 빈 값으로 설정
                    dependent_rows.append({
                        'row_id': dep_row.id,
                        'field': field,
                        'value': ''
                    })
                    print(f"종속된 행 추가 (빈 값): {dep_row.id}, {field}")
            
            return JsonResponse({
                'success': True,
                'dependent_rows': dependent_rows
            })
            
        except Exception as e:
            print(f"get_dependent_rows 오류: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})

@csrf_exempt
def get_file_content_note(request, file_id):
    """텍스트 파일의 내용을 가져오는 API (CORS 문제 해결용)"""
    if request.method == 'GET':
        print(f"get_file_content_note 호출됨: {file_id}")
        try:
            row_id = request.GET.get('row_id')
            if not row_id:
                return JsonResponse({'success': False, 'error': 'row_id가 필요합니다.'})
             
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
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
            
            # 파일 확장자 확인
            filename = file_info.get('original_filename', '')
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            try:
                import boto3
                from django.conf import settings
                import chardet
                
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # S3에서 파일 내용 가져오기
                response = s3_client.get_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=s3_key
                )
                file_content = response['Body'].read()
                
                # 인코딩 감지 및 디코딩
                detected = chardet.detect(file_content)
                detected_encoding = detected['encoding']
                confidence = detected['confidence']
                
                print(f"감지된 인코딩: {detected_encoding}, 신뢰도: {confidence}")
                
                # 파일 확장자에 따른 기본 인코딩 설정
                default_encoding = 'utf-8'
                if file_ext in ['txt', 'log', 'csv']:
                    default_encoding = 'euc-kr'
                elif file_ext in ['json', 'xml', 'html', 'htm', 'css', 'js']:
                    default_encoding = 'utf-8'
                
                # 다양한 인코딩 시도
                encodings_to_try = [detected_encoding, default_encoding, 'utf-8', 'euc-kr', 'cp949', 'iso-8859-1']
                decoded_content = None
                used_encoding = None
                
                for encoding in encodings_to_try:
                    if not encoding:
                        continue
                    try:
                        decoded_content = file_content.decode(encoding)
                        used_encoding = encoding
                        
                        # 한글 파일의 경우 한글이 포함되어 있는지 확인
                        if file_ext in ['txt', 'log', 'csv']:
                            import re
                            korean_pattern = re.compile(r'[가-힣]')
                            if korean_pattern.search(decoded_content):
                                print(f"한글 텍스트 감지됨 - 인코딩: {encoding}")
                                break
                        else:
                            # 웹 파일들은 첫 번째 성공한 인코딩 사용
                            break
                    except (UnicodeDecodeError, LookupError):
                        print(f"인코딩 {encoding} 실패, 다음 시도...")
                        continue
                
                if not decoded_content:
                    # 모든 인코딩이 실패한 경우 기본값 사용
                    decoded_content = file_content.decode('utf-8', errors='replace')
                    used_encoding = 'utf-8 (fallback)'
                
                return JsonResponse({
                    'success': True, 
                    'content': decoded_content,
                    'encoding': used_encoding,
                    'detected_encoding': detected_encoding,
                    'confidence': confidence
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'파일 내용 읽기 실패: {str(e)}'})
                
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'})

@csrf_exempt
def submit_inquiry(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({
                    'success': False,
                    'message': '문의 내용을 입력해주세요.'
                })
            
            # 현재 로그인한 사용자 정보 가져오기
            user_id = request.session.get('diary_member_id')
            user_name = ''
            user_contact = ''
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    user_name = user.name or user.username or '익명'
                    user_contact = user.phone_number or user.email or ''
                except User.DoesNotExist:
                    user_name = '익명'
                    user_contact = ''
            else:
                user_name = '익명'
                user_contact = ''
            
            from .models import Inquiry
            inquiry = Inquiry.objects.create(
                name=user_name,
                company_name=data.get('company_name', '').strip(),
                contact=user_contact,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'message': '문의사항이 성공적으로 전송되었습니다.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'문의사항 전송 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': '잘못된 요청입니다.'
    })

@require_GET
def get_notifications(request):
    """사용자의 알림 목록을 반환하는 API"""
    try:
        user_id = request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
        
        user = User.objects.get(id=user_id)
        
        # 사용자의 알림 목록 가져오기 (최근 20개)
        user_alarms = UserAlarm.objects.filter(user=user).select_related('alarm').order_by('-created_at')[:20]
        
        notifications = []
        unread_count = 0
        
        for user_alarm in user_alarms:
            if not user_alarm.is_read:
                unread_count += 1
            
            # 새로운 content 구조에서 text만 추출
            content = user_alarm.alarm.content
            if isinstance(content, dict) and 'text' in content:
                message = content['text']
            elif isinstance(content, str):
                message = content
            else:
                message = '내용 없음'
            
            notifications.append({
                'id': user_alarm.id,
                'alarm_id': user_alarm.alarm.id,  # 공지 ID 추가
                'title': user_alarm.alarm.title,
                'message': message,
                'created_at': user_alarm.alarm.created_at.isoformat(),
                'is_read': user_alarm.is_read
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'알림을 불러오는 중 오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def mark_notification_read(request, notification_id):
    """알림을 읽음 상태로 표시하는 API"""
    try:
        user_id = request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
        
        user = User.objects.get(id=user_id)
        user_alarm = UserAlarm.objects.get(id=notification_id, user=user)
        
        user_alarm.mark_as_read()
        
        return JsonResponse({'success': True, 'message': '알림이 읽음 상태로 표시되었습니다.'})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    except UserAlarm.DoesNotExist:
        return JsonResponse({'success': False, 'message': '알림을 찾을 수 없습니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'알림 상태 변경 중 오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def convert_hwp_to_pdf(request):
    """HWP 파일을 LibreOffice를 사용하여 PDF로 변환하는 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        logger.info("=== HWP to PDF 변환 시작 ===")
        data = json.loads(request.body)
        row_id = data.get('row_id')
        field_name = data.get('field_name')
        file_id = data.get('file_id')
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        saved_name = data.get('saved_name')  # 게시판 파일용
        
        logger.info(f"요청 데이터: row_id={row_id}, field_name={field_name}, file_id={file_id}, file_name={file_name}")
        
        # 파일 URL에서 파일 다운로드
        import requests
        import tempfile
        import os
        
        try:
            # 파일 다운로드
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # 임시 디렉토리에 HWP 파일 저장
            with tempfile.TemporaryDirectory() as temp_dir:
                hwp_path = os.path.join(temp_dir, file_name)
                with open(hwp_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"HWP 파일 다운로드 완료: {hwp_path}")
                
                # LibreOffice로 PDF 변환
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, hwp_path
                ]
                
                logger.info(f"LibreOffice 명령어: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10분 타임아웃
                )
                
                logger.info(f"LibreOffice 변환 결과: returncode={result.returncode}")
                logger.info(f"LibreOffice stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"LibreOffice stderr: {result.stderr}")
                
                # 변환된 PDF 파일 확인
                pdf_name = os.path.splitext(file_name)[0] + '.pdf'
                pdf_path = os.path.join(temp_dir, pdf_name)
                
                if os.path.exists(pdf_path):
                    # PDF 파일을 S3에 업로드
                    from django.conf import settings
                    import boto3
                    
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.AWS_S3_REGION_NAME
                    )
                    
                    # S3 키 생성
                    pdf_s3_key = f"converted_pdfs/{file_id}_{pdf_name}"
                    
                    # PDF 파일을 S3에 업로드
                    with open(pdf_path, 'rb') as pdf_file:
                        s3_client.upload_fileobj(
                            pdf_file,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            pdf_s3_key,
                            ExtraArgs={'ContentType': 'application/pdf'}
                        )
                    
                    # S3 URL 생성
                    pdf_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{pdf_s3_key}"
                    
                    logger.info(f"PDF 변환 및 업로드 성공: {pdf_url}")
                    
                    return JsonResponse({
                        'success': True,
                        'pdf_url': pdf_url,
                        'message': 'HWP 파일이 PDF로 성공적으로 변환되었습니다.'
                    })
                else:
                    logger.error(f"PDF 변환 실패: {pdf_path} 파일이 존재하지 않습니다.")
                    return JsonResponse({
                        'success': False,
                        'error': 'HWP 파일 변환에 실패했습니다.',
                        'original_file_url': file_url,
                        'suggest_download': True,
                        'message': 'LibreOffice가 HWP 파일을 변환할 수 없습니다. 원본 파일을 다운로드하여 사용해주세요.'
                    })
                    
        except requests.RequestException as e:
            logger.error(f"파일 다운로드 실패: {e}")
            return JsonResponse({
                'success': False,
                'error': f'파일 다운로드 실패: {str(e)}',
                'original_file_url': file_url,
                'suggest_download': True,
                'message': '파일을 다운로드할 수 없습니다.'
            })
        except subprocess.TimeoutExpired:
            logger.error("LibreOffice 변환 타임아웃")
            return JsonResponse({
                'success': False,
                'error': '변환 시간이 초과되었습니다.',
                'original_file_url': file_url,
                'suggest_download': True,
                'message': '변환에 시간이 너무 오래 걸립니다. 원본 파일을 다운로드하여 사용해주세요.'
            })
        except Exception as e:
            logger.error(f"HWP 변환 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'변환 중 오류가 발생했습니다: {str(e)}',
                'original_file_url': file_url,
                'suggest_download': True,
                'message': '변환 중 오류가 발생했습니다. 원본 파일을 다운로드하여 사용해주세요.'
            })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return JsonResponse({'success': False, 'error': f'요청 데이터 파싱 오류: {str(e)}'})
    except Exception as e:
        logger.error(f"convert_hwp_to_pdf 함수에서 예상치 못한 오류: {e}")
        return JsonResponse({'success': False, 'error': f'오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def test_libreoffice(request):
    """LibreOffice 설치 상태를 확인하는 테스트 엔드포인트"""
    try:
        # LibreOffice 버전 확인
        result = subprocess.run(['libreoffice', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"LibreOffice 버전: {version}")
            
            # LibreOffice가 지원하는 파일 형식 확인
            result2 = subprocess.run(['libreoffice', '--help'], 
                                   capture_output=True, text=True, timeout=10)
            
            support_info = {
                'version': version,
                'hwp_support': 'LibreOffice는 HWP 파일을 제한적으로 지원합니다.',
                'conversion_issues': [
                    'HWP는 한글과컴퓨터의 독점 형식입니다',
                    'LibreOffice는 HWP 파일을 완전히 지원하지 않습니다',
                    '변환 시 레이아웃이나 서식이 깨질 수 있습니다',
                    '복잡한 HWP 파일은 변환에 실패할 수 있습니다'
                ],
                'recommendations': [
                    'HWP 파일은 원본 파일로 다운로드하여 한글 프로그램으로 열어주세요',
                    '필요시 한글 프로그램에서 PDF로 변환 후 사용하세요'
                ]
            }
            
            return JsonResponse({
                'success': True,
                'libreoffice_available': True,
                'version': version,
                'support_info': support_info,
                'message': 'LibreOffice는 설치되어 있지만 HWP 파일 변환은 제한적입니다.'
            })
        else:
            return JsonResponse({
                'success': False,
                'libreoffice_available': False,
                'error': result.stderr,
                'message': 'LibreOffice가 설치되어 있지만 실행할 수 없습니다.'
            })
    except FileNotFoundError:
        return JsonResponse({
            'success': False,
            'libreoffice_available': False,
            'error': 'LibreOffice가 설치되어 있지 않습니다.',
            'message': '서버에 LibreOffice를 설치해주세요.'
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'success': False,
            'libreoffice_available': False,
            'error': 'LibreOffice 응답 시간이 초과되었습니다.',
            'message': 'LibreOffice가 응답하지 않습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'libreoffice_available': False,
            'error': str(e),
            'message': f'LibreOffice 확인 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def test_hwp_conversion(request):
    """HWP 파일 변환을 실제로 테스트하는 엔드포인트"""
    try:
        logger.info("=== HWP 변환 테스트 시작 ===")
        
        # 간단한 테스트 파일 생성 (실제 HWP 파일이 아닌 텍스트 파일)
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("테스트 파일입니다.\n한글 텍스트입니다.")
            
            # LibreOffice로 텍스트 파일을 PDF로 변환 테스트
            cmd = [
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', temp_dir, test_file
            ]
            
            logger.info(f"LibreOffice 테스트 명령어: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            logger.info(f"LibreOffice 테스트 결과: returncode={result.returncode}")
            logger.info(f"LibreOffice stdout: {result.stdout}")
            logger.info(f"LibreOffice stderr: {result.stderr}")
            
            # 결과 확인
            pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]
            
            test_results = {
                'libreoffice_works': result.returncode == 0,
                'pdf_created': len(pdf_files) > 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'pdf_files': pdf_files
            }
            
            return JsonResponse({
                'success': True,
                'test_results': test_results,
                'message': 'LibreOffice 기본 변환 테스트 완료'
            })
            
    except Exception as e:
        logger.error(f"HWP 변환 테스트 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': f'테스트 중 오류가 발생했습니다: {str(e)}'
        })

def cleanup_duplicate_attribute_values():
    """
    중복된 AttributeValue 레코드를 정리하는 함수
    """
    try:
        with transaction.atomic():
            # 중복된 레코드 찾기 (row_id, attribute_id, value가 동일한 레코드들)
            from django.db import connection
            
            with connection.cursor() as cursor:
                # 중복 레코드 찾기
                cursor.execute("""
                    SELECT row_id, attribute_id, value, COUNT(*) as count
                    FROM diary_attributevalue
                    GROUP BY row_id, attribute_id, value
                    HAVING COUNT(*) > 1
                """)
                
                duplicates = cursor.fetchall()
                deleted_count = 0
                
                for row_id, attribute_id, value, count in duplicates:
                    # 각 그룹에서 첫 번째 레코드를 제외하고 나머지 삭제
                    cursor.execute("""
                        DELETE FROM diary_attributevalue 
                        WHERE row_id = %s AND attribute_id = %s AND value = %s
                        AND id NOT IN (
                            SELECT id FROM (
                                SELECT id FROM diary_attributevalue 
                                WHERE row_id = %s AND attribute_id = %s AND value = %s
                                ORDER BY id ASC
                                LIMIT 1
                            ) AS keep_ids
                        )
                    """, [row_id, attribute_id, value, row_id, attribute_id, value])
                    
                    deleted_count += cursor.rowcount
                
                print(f"중복 AttributeValue 레코드 {deleted_count}개 정리 완료")
                return deleted_count
                
    except Exception as e:
        print(f"중복 레코드 정리 중 오류: {e}")
        return 0

@csrf_exempt
def cleanup_duplicates_api(request):
    """
    중복 레코드 정리를 위한 API 엔드포인트
    """
    if request.method == 'POST':
        try:
            deleted_count = cleanup_duplicate_attribute_values()
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'message': f'중복 레코드 {deleted_count}개가 정리되었습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})

def check_libreoffice_status():
    """LibreOffice 설치 및 실행 상태 확인"""
    try:
        result = subprocess.run(['libreoffice', '--version'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"LibreOffice 상태 확인 실패: {e}")
        return False

def convert_hwp_to_pdf(hwp_path):
    """HWP를 PDF로 변환"""
    output_dir = os.path.dirname(hwp_path)
    try:
        # 파일 크기 확인
        file_size = os.path.getsize(hwp_path)
        print(f"📄 HWP 파일 크기: {file_size / (1024*1024):.2f} MB")
        
        # 파일 크기에 따른 timeout 조정
        if file_size > 50 * 1024 * 1024:  # 50MB 이상
            timeout = 1800  # 30분
            print("⏰ 대용량 파일 감지, timeout을 30분으로 설정")
        elif file_size > 10 * 1024 * 1024:  # 10MB 이상
            timeout = 900   # 15분
            print("⏰ 중간 크기 파일 감지, timeout을 15분으로 설정")
        else:
            timeout = 600   # 10분 (기본값)
            print("⏰ 기본 timeout 10분 설정")
        
        print("🖥️ LibreOffice 변환 시작...")
        
        result = subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            hwp_path,
            "--outdir", output_dir
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)

        print("🖥️ libreoffice stdout: " + result.stdout.decode())
        if result.stderr:
            print("🖥️ libreoffice stderr: " + result.stderr.decode())

        basename = os.path.splitext(os.path.basename(hwp_path))[0] + ".pdf"
        converted_pdf = os.path.join(output_dir, basename)

        if os.path.exists(converted_pdf):
            pdf_size = os.path.getsize(converted_pdf)
            print(f"✅ 변환 성공: {pdf_size / (1024*1024):.2f} MB")
            return converted_pdf
        else:
            print(f"[❌ 변환 실패] {converted_pdf} 파일이 존재하지 않습니다.")
            return ""
            
    except subprocess.TimeoutExpired:
        print(f"[⏰ Timeout 발생] {timeout}초 초과로 변환 실패")
        # LibreOffice 프로세스 강제 종료
        try:
            subprocess.run(["pkill", "-f", "libreoffice"], timeout=10)
            print("🔄 LibreOffice 프로세스 강제 종료 완료")
        except:
            print("⚠️ LibreOffice 프로세스 종료 실패")
        return ""
    except Exception as e:
        print(f"[예외 발생] HWP → PDF 변환 실패: {e}")
        return ""

def download_file_from_s3_for_preview(s3_key):
    """S3에서 파일을 임시로 다운로드하여 미리보기용으로 사용"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 임시 디렉토리에 파일 다운로드
        temp_dir = tempfile.gettempdir()
        temp_filename = f"preview_{os.path.basename(s3_key)}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        s3_client.download_file(
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            temp_path
        )
        
        return temp_path
    except Exception as e:
        print(f"S3 파일 다운로드 실패: {e}")
        return None

def upload_pdf_to_s3_for_preview(pdf_path, original_s3_key):
    """변환된 PDF를 S3에 업로드하여 미리보기용 URL 생성"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 원본 파일명에서 확장자만 PDF로 변경
        original_filename = os.path.basename(original_s3_key)
        pdf_filename = os.path.splitext(original_filename)[0] + "_preview.pdf"
        preview_s3_key = f"preview/{pdf_filename}"
        
        # PDF 파일을 S3에 업로드
        s3_client.upload_file(
            pdf_path,
            settings.AWS_STORAGE_BUCKET_NAME,
            preview_s3_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        
        # 미리보기용 presigned URL 생성
        signed_preview_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': preview_s3_key,
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=3600
        )
        
        return signed_preview_url
    except Exception as e:
        print(f"PDF S3 업로드 실패: {e}")
        return None

@csrf_exempt
def test_hwp_preview_conversion(request):
    """HWP 파일 미리보기 변환 기능 테스트"""
    if request.method == 'GET':
        try:
            # LibreOffice 상태 확인
            libreoffice_ok = check_libreoffice_status()
            
            return JsonResponse({
                'success': True,
                'libreoffice_available': libreoffice_ok,
                'message': 'HWP 미리보기 변환 기능이 준비되었습니다.' if libreoffice_ok else 'LibreOffice가 설치되지 않았습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'})

@csrf_exempt
def convert_hwp_to_pdf_board(request):
    """게시판용 HWP 파일을 LibreOffice를 사용하여 PDF로 변환하는 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        logger.info("=== 게시판 HWP to PDF 변환 시작 ===")
        data = json.loads(request.body)
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        saved_name = data.get('saved_name')
        
        logger.info(f"게시판 요청 데이터: file_name={file_name}, saved_name={saved_name}")
        
        if not file_url or not file_name:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # LibreOffice 상태 확인
        if not check_libreoffice_status():
            return JsonResponse({'success': False, 'error': '파일 변환에 실패했습니다.'})
        
        # 파일 URL에서 파일 다운로드
        import requests
        import tempfile
        import os
        
        try:
            # 파일 다운로드
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # 임시 디렉토리에 HWP 파일 저장
            with tempfile.TemporaryDirectory() as temp_dir:
                hwp_path = os.path.join(temp_dir, file_name)
                with open(hwp_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"게시판 HWP 파일 다운로드 완료: {hwp_path}")
                
                # LibreOffice로 PDF 변환
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, hwp_path
                ]
                
                logger.info(f"게시판 LibreOffice 명령어: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10분 타임아웃
                )
                
                logger.info(f"게시판 LibreOffice 변환 결과: returncode={result.returncode}")
                logger.info(f"게시판 LibreOffice stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"게시판 LibreOffice stderr: {result.stderr}")
                
                # 변환된 PDF 파일 확인
                pdf_name = os.path.splitext(file_name)[0] + '.pdf'
                pdf_path = os.path.join(temp_dir, pdf_name)
                
                if os.path.exists(pdf_path):
                    # PDF 파일을 S3에 업로드
                    from django.conf import settings
                    import boto3
                    
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.AWS_S3_REGION_NAME
                    )
                    
                    # S3 키 생성 (게시판용)
                    pdf_s3_key = f"converted_pdfs/board_{saved_name}_{pdf_name}"
                    
                    # PDF 파일을 S3에 업로드
                    with open(pdf_path, 'rb') as pdf_file:
                        s3_client.upload_fileobj(
                            pdf_file,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            pdf_s3_key,
                            ExtraArgs={'ContentType': 'application/pdf'}
                        )
                    
                    # S3 미리보기 URL 생성
                    pdf_preview_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': pdf_s3_key,
                            'ResponseContentDisposition': 'inline'
                        },
                        ExpiresIn=3600
                    )
                    
                    logger.info(f"게시판 PDF 변환 및 업로드 성공: {pdf_preview_url}")
                    
                    return JsonResponse({
                        'success': True,
                        'url': pdf_preview_url,
                        'message': 'HWP 파일이 PDF로 성공적으로 변환되었습니다.'
                    })
                else:
                    logger.error(f"게시판 PDF 변환 실패: {pdf_path} 파일이 존재하지 않습니다.")
                    return JsonResponse({
                        'success': False,
                        'error': 'HWP 파일 변환에 실패했습니다.',
                        'message': 'LibreOffice가 HWP 파일을 변환할 수 없습니다.'
                    })
                    
        except requests.RequestException as e:
            logger.error(f"게시판 파일 다운로드 실패: {e}")
            return JsonResponse({
                'success': False,
                'error': f'파일 다운로드 실패: {str(e)}',
                'message': '파일을 다운로드할 수 없습니다.'
            })
        except subprocess.TimeoutExpired:
            logger.error("게시판 LibreOffice 변환 타임아웃")
            return JsonResponse({
                'success': False,
                'error': '변환 시간이 초과되었습니다.',
                'message': '변환에 시간이 너무 오래 걸립니다.'
            })
        except Exception as e:
            logger.error(f"게시판 HWP 변환 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'변환 중 오류가 발생했습니다: {str(e)}',
                'message': '변환 중 오류가 발생했습니다.'
            })
        
    except json.JSONDecodeError as e:
        logger.error(f"게시판 JSON 파싱 오류: {e}")
        return JsonResponse({'success': False, 'error': f'요청 데이터 파싱 오류: {str(e)}'})
    except Exception as e:
        logger.error(f"convert_hwp_to_pdf_board 함수에서 예상치 못한 오류: {e}")
        return JsonResponse({'success': False, 'error': f'오류가 발생했습니다: {str(e)}'})


@csrf_exempt
def add_sample_row(request):
    """샘플 데이터를 추가하는 엔드포인트"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sample_data = data.get('sample_data', {})
            
            print(f"=== 샘플 데이터 추가 요청 ===")
            print(f"sample_data: {sample_data}")
            
            user_id = request.session.get('diary_member_id')
            if not user_id:
                return JsonResponse({'success': False, 'error': '로그인이 필요합니다.'})
            
            user = User.objects.get(id=user_id)
            
            # 사용자의 기존 드롭다운 속성들과 옵션들을 가져와서 샘플 데이터를 동적으로 생성
            dropdown_data = {}
            dropdown_attributes = Attribute.objects.filter(user=user, attributeType__name='dropdown')
            
            for attr in dropdown_attributes:
                options = list(DropdownAttribute.objects.filter(attribute=attr).values_list('option', flat=True))
                if options:
                    dropdown_data[attr.name] = options
            
            print(f"사용자의 드롭다운 속성들: {dropdown_data}")
            
            # 샘플 데이터에서 드롭다운 필드들을 사용자의 기존 옵션으로 교체
            final_sample_data = {}
            for field_name, field_value in sample_data.items():
                if field_name in dropdown_data and dropdown_data[field_name]:
                    # 드롭다운 필드인 경우 기존 옵션 중에서 랜덤 선택
                    final_sample_data[field_name] = random.choice(dropdown_data[field_name])
                    print(f"드롭다운 필드 {field_name}: 기존 옵션 중 선택 - {final_sample_data[field_name]}")
                else:
                    # 일반 필드인 경우 원래 값 사용
                    final_sample_data[field_name] = field_value
            
            # 새 Row 생성 (가장 위에 추가)
            # 기존 모든 행들의 order를 1씩 증가
            Row.objects.filter(user=user).update(order=models.F('order') + 1)
            
            # 새 행은 order=0으로 가장 위에 추가
            new_row = Row.objects.create(order=0, user=user)
            print(f"새 샘플 행 생성됨: row_id={new_row.id}, order=0 (가장 위에 추가)")
            
            # 각 필드별로 AttributeValue 생성
            for field_name, field_value in final_sample_data.items():
                if not field_value:  # 빈 값은 건너뜀
                    continue
                    
                try:
                    # 속성 찾기 또는 생성
                    attr, created = Attribute.objects.get_or_create(
                        name=field_name,
                        user=user,
                        defaults={
                            'attributeType': AttributeType.objects.get_or_create(name='text')[0],
                            'assential': False,
                            'view_select': True,
                            'order': Attribute.objects.filter(user=user).count() + 1
                        }
                    )
                    
                    if created:
                        print(f"새 속성 생성됨: {field_name}")
                    
                    attr_type = attr.attributeType.name if attr.attributeType else 'text'
                    value_to_save = field_value
                    
                    # Dropdown 속성인 경우 처리
                    if attr_type == 'dropdown':
                        # 드롭다운 옵션 찾기 또는 생성
                        dropdown_option, created = DropdownAttribute.objects.get_or_create(
                            attribute=attr,
                            option=field_value,
                            defaults={
                                'color': f"#{random.randint(0, 0xFFFFFF):06x}",  # 랜덤 색상
                                'order': DropdownAttribute.objects.filter(attribute=attr).count() + 1
                            }
                        )
                        
                        if created:
                            print(f"새 드롭다운 옵션 생성됨: {field_name} = {field_value}")
                        else:
                            print(f"기존 드롭다운 옵션 사용: {field_name} = {field_value}")
                        
                        value_to_save = str(dropdown_option.id)
                    
                    # AttributeValue 생성
                    AttributeValue.objects.create(
                        row=new_row,
                        attribute=attr,
                        value=value_to_save
                    )
                    print(f"샘플 데이터 필드 설정: {field_name}={field_value}")
                    
                except Exception as e:
                    print(f"필드 {field_name} 처리 중 오류: {e}")
                    continue
            
            print(f"=== 샘플 데이터 추가 완료: row_id={new_row.id} ===")
            return JsonResponse({
                'success': True, 
                'id': new_row.id,
                'company_name': final_sample_data.get('회사명', '샘플 회사')
            })
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return JsonResponse({'success': False, 'error': 'JSON 파싱 오류'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '유효하지 않은 사용자'})
        except Exception as e:
            print(f"샘플 데이터 추가 중 오류: {e}")
            return JsonResponse({'success': False, 'error': f'오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



