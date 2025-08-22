from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.db import models, transaction
from django.conf import settings

from .models import (
    Region, SalesStatus,
    Attribute, AttributeValue, User, DropdownAttribute, Row, 
    UserAlarm, Diary_diary_count, DailyViewRecord
)
from board.models import BizInfo
from main.models import BizTop
from django.utils import timezone
from datetime import date, timedelta
import json
import random
import time
import uuid
import os
import logging
from datetime import datetime
import boto3
from django.db.models import Sum, Count

# 분리된 모듈들에서 함수들 import
from .attribute_handlers import filter_attributes_by_status

from .cascade_handlers import sync_cascade_attributes
from .data_utils import parse_korean_currency, parse_sales_amount, parse_business_data, calculate_business_years, formatToKoreanCurrency

logger = logging.getLogger(__name__)

def get_week_of_month(dt: date) -> int:
    first_day = dt.replace(day=1)
    first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
    
    # 만약 1일이 월요일이라면 그게 첫째 주의 시작
    if first_day.weekday() == 0:
        first_monday = first_day
    
    delta_days = (dt - first_monday).days
    if delta_days < 0:
        return 1
    return delta_days // 7 + 1

# 세션 데이터 파싱을 위한 헬퍼 함수
def parse_session_data(request, keys_with_defaults):
    """세션 데이터를 효율적으로 파싱하는 헬퍼 함수"""
    session_data = {}
    for key, default_value in keys_with_defaults.items():
        try:
            session_value = request.session.get(key, default_value)
            if isinstance(session_value, str):
                session_data[key] = json.loads(session_value)
            else:
                session_data[key] = session_value
        except (json.JSONDecodeError, TypeError):
            session_data[key] = default_value
    return session_data

# 로그인 상태 확인 뷰
@require_GET
def check_login_status(request):
    """로그인 상태를 확인하는 API"""
    try:
        # 세션에서 로그인 상태 확인
        is_authenticated = request.session.get('diary_authenticated', False)
        
        if is_authenticated:
            # 로그인된 사용자의 ID 가져오기
            user_id = request.session.get('diary_member_id')
            if user_id:
                
                try:
                    user = User.objects.get(id=user_id)
                    
                    # use_date가 설정되어 있는지 확인
                    if user.use_date:
                        # 현재 날짜와 use_date 비교 (타입 통일)
                        current_date = timezone.now().date()
                        use_date = user.use_date.date() if hasattr(user.use_date, 'date') else user.use_date
                        if current_date > use_date:
                            # 사용 기간이 만료된 경우 세션 정리
                            request.session.flush()
                            return JsonResponse({
                                'is_authenticated': False,
                                'success': True,
                                'expired': True,
                                'message': '사용 기간이 만료되었습니다.'
                            })
                except User.DoesNotExist:
                    # 사용자를 찾을 수 없는 경우 세션 정리
                    request.session.flush()
                    return JsonResponse({
                        'is_authenticated': False,
                        'success': True,
                        'message': '사용자 정보를 찾을 수 없습니다.'
                    })
        
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

    # IP 주소 가져오기
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    
    # IP 카운트 업데이트
    try:
        current_date = timezone.now().date()
        
        # 기존 IP 카운트 업데이트
        ip_count, created = Diary_diary_count.objects.get_or_create(
            ip=ip,
            defaults={'count': 1}
        )
        if not created:
            ip_count.count += 1
            ip_count.updated_at = timezone.now()
            ip_count.save()
        
        # 일별 상세 기록 추가
        daily_record, created = DailyViewRecord.objects.get_or_create(
            ip=ip,
            date=current_date,
            page_type='diary',
            defaults={'count': 1}
        )
        if not created:
            daily_record.count += 1
            daily_record.save()
            
    except Exception as e:
        # 에러 발생 시 로그 기록 (선택사항)
        print(f"IP 카운트 업데이트 중 오류 발생: {e}")

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
    
    # 사용자의 남은 이용기간
    use_date = user.use_date
    
    # use_date를 YYYY-MM-DD 형식으로 변환하고 남은 일수 계산
    formatted_use_date = None
    remaining_days = None
    
    if use_date:
        try:
            # datetime 객체를 YYYY-MM-DD 형식으로 변환
            formatted_use_date = use_date.strftime('%Y-%m-%d')
            
            # 오늘 날짜와 비교하여 남은 일수 계산
            from datetime import date
            today = date.today()
            use_date_only = use_date.date()
            remaining_days = (use_date_only - today).days
            
            
        except Exception as e:
            formatted_use_date = str(use_date)
            remaining_days = None
    
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
    
    # 드롭다운 옵션을 미리 캐시하여 N+1 쿼리 방지
    dropdown_cache = {}
    for attr in user_attributes:
        if attr.attributeType and attr.attributeType.name == 'dropdown':
            dropdown_cache[attr.id] = {
                dropdown_attr.id: dropdown_attr 
                for dropdown_attr in attr.dropdown_attributes.all()
            }
    
    # 세션 데이터 파싱 최적화 - 한 번만 파싱
    session_keys = {
        'column_widths': {},
        'hidden_attributes': [],
        'status_tabs': [],
        'calendar_settings': {}
    }
    session_data = parse_session_data(request, session_keys)
    
    # 각 행의 속성 값들을 가져오기 (필터링된 속성만)
    rows_data = []
    
    # 지원사업 속성에서 알림 정보 미리 계산
    support_business_attr = None
    try:
        support_business_attr = Attribute.objects.get(name='지원사업', user=user)
    except Attribute.DoesNotExist:
        support_business_attr = None
    
    for row in rows:
        row_values = {}
        # 행의 모든 값들을 딕셔너리로 미리 구성하여 N+1 쿼리 방지
        row_value_dict = {value.attribute_id: value.value for value in row.values.all()}
        
        # 알림 상태 확인
        has_notifications = False
        if support_business_attr:
            try:
                attr_value = AttributeValue.objects.get(attribute=support_business_attr, row=row)
                if attr_value.value:
                    # 데이터 타입에 따른 분기 처리
                    if isinstance(attr_value.value, dict):
                        alerts = attr_value.value.get('알림', [])
                        has_notifications = len(alerts) > 0
                    elif isinstance(attr_value.value, str):
                        try:
                            # JSON 파싱 시도
                            parsed_data = json.loads(attr_value.value.replace("'", '"').replace('True', 'true').replace('False', 'false'))
                            if isinstance(parsed_data, dict):
                                alerts = parsed_data.get('알림', [])
                                has_notifications = len(alerts) > 0
                        except (json.JSONDecodeError, AttributeError):
                            has_notifications = False
            except AttributeValue.DoesNotExist:
                has_notifications = False
        
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
            'values': row_values,
            'has_notifications': has_notifications
        })
    
    # 캐시 무효화를 위한 타임스탬프
    cache_timestamp = int(time.time())
    
    # 모바일 디바이스 감지
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_mobile = any(mobile_device in user_agent for mobile_device in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 
        'windows phone', 'opera mini', 'mobile safari'
    ])
    
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
                # 캐시에 없는 경우에만 쿼리 실행
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
        'dropdown_options': dropdown_options,  # 모든 드롭다운 옵션 추가
        'is_mobile': is_mobile,  # 모바일 여부 추가
        'formatted_use_date': formatted_use_date,  # 사용 가능 기간 (YYYY-MM-DD 형식)
        'remaining_days': remaining_days,  # 남은 일수
    }
    context['attributes_json'] = json.dumps(context['attributes'], ensure_ascii=False)
    context['dropdown_options_json'] = json.dumps(dropdown_options, ensure_ascii=False)  # JSON 형태로도 추가
    
    return render(request, 'diary/diary_list.html', context)

def random_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])

@csrf_exempt
def bizinfo(request):
    if request.method == 'GET':
        try:
            biz_list_10 = BizInfo.objects.all().order_by('-registered_at')[:15]
            biz_top_10 = BizTop.objects.all().order_by('-update_date')[:15]

            pblanc_ids = [biz.pblanc_id for biz in biz_top_10]
            biz_top_10 = list(BizTop.objects.filter(pblanc_id__in=pblanc_ids))

            # 데이터를 직렬화 가능한 형태로 변환
            biz_list_data = []
            for biz in biz_list_10:
                biz_list_data.append({
                    'pblanc_id': biz.pblanc_id,
                    'title': biz.title,
                    'registered_at': biz.registered_at,
                    # 필요한 다른 필드들도 추가
                })

            biz_top_data = []
            for biz in biz_top_10:
                biz_top_data.append({
                    'pblanc_id': biz.pblanc_id,
                    'title': biz.title,
                    'registered_at': biz.update_date,
                    # 필요한 다른 필드들도 추가
                })

            response_data = {
                'success': True,
                'biz_list': biz_list_data,
                'biz_top': biz_top_data,
                'message': '데이터를 성공적으로 가져왔습니다.'
            }
            
            return JsonResponse(response_data, safe=False)
            
        except Exception as e:
            error_data = {
                'success': False,
                'error': str(e),
                'message': '데이터를 가져오는 중 오류가 발생했습니다.'
            }
            return JsonResponse(error_data, status=500, safe=False)
    
    elif request.method == 'POST':
        # POST 요청 처리 (필요한 경우)
        try:
            data = json.loads(request.body)
            # POST 데이터 처리 로직
            response_data = {
                'success': True,
                'message': 'POST 요청이 성공적으로 처리되었습니다.'
            }
            return JsonResponse(response_data, safe=False)
        
        except json.JSONDecodeError:
            error_data = {
                'success': False,
                'error': '잘못된 JSON 형식입니다.',
                'message': '요청 데이터를 파싱할 수 없습니다.'
            }
            return JsonResponse(error_data, status=400, safe=False)
        except Exception as e:
            error_data = {
                'success': False,
                'error': str(e),
                'message': 'POST 요청 처리 중 오류가 발생했습니다.'
            }
            return JsonResponse(error_data, status=500, safe=False)
    
    else:
        # 지원하지 않는 HTTP 메서드
        error_data = {
            'success': False,
            'error': '지원하지 않는 HTTP 메서드입니다.',
            'message': 'GET 또는 POST 메서드만 지원합니다.'
        }
        return JsonResponse(error_data, status=405, safe=False)

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

@csrf_exempt
def create_new_row(request):
    """새 행 생성을 위한 엔드포인트"""
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value', '')
        status_field = request.POST.get('status_field')
        status_value = request.POST.get('status_value')
        
        logger.info(f"새 행 생성 요청: field={field}, value={value}, status_field={status_field}")
        
        if not field:
            return JsonResponse({'success': False, 'error': 'Missing field'})
            
         
        user_id = request.session.get('diary_member_id')
        logger.debug(f"user_id: {user_id}")

        user = User.objects.get(id=user_id)
        
        # 새 Row 생성 (가장 위에 추가하도록 변경)
        # 기존 모든 행들의 order를 1씩 증가
        Row.objects.filter(user=user).update(order=models.F('order') + 1)
        
        # 새 행은 order=0으로 가장 위에 추가
        new_row = Row.objects.create(order=0, user=user)
        logger.info(f"새 행 생성됨: row_id={new_row.id}, order=0 (가장 위에 추가)")
        
        # 첫 번째 필드 값 설정
        try:
            attr = Attribute.objects.get(name=field, user=user)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Attribute 조회 오류: {str(e)}'})
            
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
            except (ValueError, Exception) as e:
                return JsonResponse({'success': False, 'error': f'Dropdown 처리 오류: {str(e)}'})
        else:
            value_to_save = value
            
        # 새 Row에 AttributeValue 생성
        AttributeValue.objects.create(
            row=new_row,
            attribute=attribute,
            value=value_to_save
        )
        logger.info(f"첫 번째 필드 값 설정: {field}={value_to_save}")
        
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
                        AttributeValue.objects.create(
                            row=new_row,
                            attribute=status_attr,
                            value=status_value_to_save
                        )
                        logger.info(f"상태 필드 값 설정: {status_field}={status_value_to_save}")
                else:
                    status_value_to_save = status_value
                    AttributeValue.objects.create(
                        row=new_row,
                        attribute=status_attr,
                        value=status_value_to_save
                    )
                    logger.info(f"상태 필드 값 설정: {status_field}={status_value_to_save}")
            except Exception as e:
                logger.error(f"상태 필드 생성 오류: {e}")
        
        logger.info(f"새 행 생성 완료: row_id={new_row.id}")
        return JsonResponse({'success': True, 'id': new_row.id})
        
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def update_row_field(request):
    if request.method == 'POST':
        logger.info("=== update_row_field 시작 ===")
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
            
            logger.debug(f"update_row_field: row_id={row_id}, field_name={field_name}, value='{value}'")
            
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
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'속성 조회 중 오류: {str(e)}'})
            
            # 드롭다운 타입인 경우 특별 처리
            if attr.attributeType and attr.attributeType.name == 'dropdown':
                logger.debug(f"Dropdown 필드 처리 - {attr.name}: value='{value}'")
                
                # 빈 값 처리
                if value == '' or value is None:
                    logger.debug(f"  빈 값 처리 - 빈 문자열로 저장")
                    value_to_save = ''
                elif value.isdigit():
                    # 단일 선택
                    logger.debug(f"  단일 선택 처리")
                    value_to_save = value
                elif value.startswith('[') and value.endswith(']'):
                    # 다중선택(dropdown) 필드인 경우
                    logger.debug(f"다중선택 처리 - {attr.name}: value='{value}'")
                    try:
                        selected_ids = json.loads(value)
                        logger.debug(f"  JSON 파싱 성공: {selected_ids}")
                        value_to_save = value  # JSON 배열 형태로 저장
                    except json.JSONDecodeError as e:
                        logger.error(f"  JSON 파싱 실패: {e}")
                        value_to_save = value
                else:
                    # 다른 형태
                    logger.debug(f"  다른 형태: '{value}'")
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
                        logger.debug(f"기존 AttributeValue 레코드 삭제: {field_name}")
                    
                    # 새 레코드 생성
                    attr_value = AttributeValue.objects.create(
                        row=row,
                        attribute=attr,
                        value=value_to_save
                    )
                    logger.debug(f"새 AttributeValue 생성: {field_name} = {value_to_save}")
                    
            except Exception as e:
                logger.error(f"AttributeValue 처리 중 오류: {e}")
                return JsonResponse({'success': False, 'error': f'속성 값 저장 중 오류: {str(e)}'})
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if attr.cascade:
                logger.info(f"=== Cascade 동기화 시작 ===")
                logger.info(f"속성 '{field_name}'의 cascade 값: {attr.cascade}")
                logger.info(f"수정된 행 ID: {row_id}")
                logger.info(f"새 값: {value_to_save}")
                
                synced_count = sync_cascade_attributes(request, row_id, field_name, value_to_save)
                if synced_count > 0:
                    logger.info(f"Cascade 동기화 완료: {field_name} 속성이 {synced_count}개 행에 동기화됨")
                else:
                    logger.info(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                logger.info(f"=== Cascade 동기화 종료 ===")
            else:
                logger.debug(f"속성 '{field_name}'의 cascade 값: {attr.cascade} - 동기화하지 않음")
            
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
    
    # 기본 속성 쿼리 - 한 번에 모든 필요한 데이터 가져오기
    base_attributes = Attribute.objects.filter(user=user, detail=False).select_related('attributeType').order_by('sort_order', 'id')
    
    # 상태별 필터링 적용
    user_attributes = filter_attributes_by_status(base_attributes, status_id)
    
    # 속성 ID 목록을 미리 추출하여 쿼리 최적화
    attribute_ids = [attr.id for attr in user_attributes]
    
    # 행 데이터 쿼리 최적화 - 상태별 필터링을 포함하여 한 번에 처리
    if status_id != 'all':
        # 상태 속성 찾기
        status_attribute = Attribute.objects.filter(user=user, name='상태').first()
        if status_attribute:
            # 해당 상태를 가진 행들만 필터링 (distinct 추가로 중복 방지)
            rows = Row.objects.filter(
                user=user,
                values__attribute=status_attribute, 
                values__value=status_id
            ).distinct().select_related('user').prefetch_related(
                'values__attribute__attributeType',
                'values__attribute__dropdown_attributes'
            ).order_by('order')
            logger.debug(f"상태 필터링 적용: status_id={status_id}, 필터링된 행 수: {rows.count()}")
        else:
            logger.debug(f"상태 속성을 찾을 수 없음: status_id={status_id}")
            # 상태 속성이 없으면 빈 결과 반환
            rows = Row.objects.none()
    else:
        logger.debug(f"전체 상태 표시: status_id={status_id}")
        rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
            'values__attribute__attributeType',
            'values__attribute__dropdown_attributes'
        ).order_by('order')
    
    # 드롭다운 옵션을 미리 캐시하여 N+1 쿼리 방지
    dropdown_cache = {}
    for attr in user_attributes:
        if attr.attributeType and attr.attributeType.name == 'dropdown':
            dropdown_cache[attr.id] = {
                dropdown_attr.id: dropdown_attr 
                for dropdown_attr in attr.dropdown_attributes.all()
            }
    
    # 각 행의 속성 값들을 가져오기 (필터링된 속성만)
    rows_data = []
    
    # 지원사업 속성에서 알림 정보 미리 계산
    support_business_attr = None
    try:
        support_business_attr = Attribute.objects.get(name='지원사업', user=user)
    except Attribute.DoesNotExist:
        support_business_attr = None
    
    for row in rows:
        row_values = {}
        # 행의 모든 값들을 딕셔너리로 미리 구성하여 N+1 쿼리 방지
        row_value_dict = {value.attribute_id: value.value for value in row.values.all()}
        
        # 알림 상태 확인
        has_notifications = False
        if support_business_attr:
            try:
                attr_value = AttributeValue.objects.get(attribute=support_business_attr, row=row)
                if attr_value.value:
                    # 데이터 타입에 따른 분기 처리
                    if isinstance(attr_value.value, dict):
                        alerts = attr_value.value.get('알림', [])
                        has_notifications = len(alerts) > 0
                    elif isinstance(attr_value.value, str):
                        try:
                            # JSON 파싱 시도
                            parsed_data = json.loads(attr_value.value.replace("'", '"').replace('True', 'true').replace('False', 'false'))
                            if isinstance(parsed_data, dict):
                                alerts = parsed_data.get('알림', [])
                                has_notifications = len(alerts) > 0
                        except (json.JSONDecodeError, AttributeError):
                            has_notifications = False
            except AttributeValue.DoesNotExist:
                has_notifications = False
        
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
                try:
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
                except (json.JSONDecodeError, TypeError):
                    # JSON 파싱 실패 시 기본값 사용
                    row_values[attr.name] = {
                        'type': 'file',
                        'label': '파일',
                        'download_url': '',
                        'file_size': 0,
                        'content_type': '',
                        'original_filename': '파일'
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
            'values': row_values,
            'has_notifications': has_notifications
        })
    
    # 속성 리스트 생성 - 이미 메모리에 있는 데이터 활용
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
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'속성 조회 중 오류: {str(e)}'})
            
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
                logger.debug(f"원본 행 {original_id}의 copied_row_ids 업데이트: {original_row.copied_row_ids}")
            except Row.DoesNotExist:
                logger.warning(f"원본 행 {original_id}를 찾을 수 없습니다.")
                continue
        
        # 4. 소스 행의 모든 복제된 행들에도 새 행을 복제된 행으로 추가
        for copied_id in source_row.copied_row_ids:
            try:
                copied_row = Row.objects.get(id=copied_id)
                copied_row.add_copied_row(new_row.id)
                logger.debug(f"복제된 행 {copied_id}의 copied_row_ids 업데이트: {copied_row.copied_row_ids}")
            except Row.DoesNotExist:
                logger.warning(f"복제된 행 {copied_id}를 찾을 수 없습니다.")
                continue
        
        # 5. 새 행의 복제된 행 목록에 소스 행의 모든 복제된 행들 추가
        new_copied_ids = source_row.copied_row_ids.copy()
        new_row.copied_row_ids = new_copied_ids
        new_row.save()
        logger.debug(f"새 행의 copied_row_ids 설정: {new_row.copied_row_ids}")
        
        # 6. 새 행의 복제된 행 목록에 소스 행도 추가 (양방향 관계 완성)
        if source_row.id not in new_row.copied_row_ids:
            new_row.copied_row_ids.append(source_row.id)
            new_row.save()
            logger.debug(f"새 행의 copied_row_ids에 소스 행 추가: {new_row.copied_row_ids}")
        
        # 7. 소스 행의 원본 행 목록에 새 행 추가 (양방향 관계 완성)
        if new_row.id not in source_row.original_row_ids:
            source_row.original_row_ids.append(new_row.id)
            source_row.save()
            logger.debug(f"소스 행의 original_row_ids에 새 행 추가: {source_row.original_row_ids}")
        
        # 8. 소스 행을 다시 조회하여 최신 상태 확인 및 강제 업데이트
        source_row.refresh_from_db()
        if new_row.id not in source_row.copied_row_ids:
            source_row.copied_row_ids.append(new_row.id)
            source_row.save()
            logger.debug(f"소스 행 강제 업데이트 후 copied_row_ids: {source_row.copied_row_ids}")
        
        # 9. 새 행도 다시 조회하여 최신 상태 확인 및 강제 업데이트
        new_row.refresh_from_db()
        if source_row.id not in new_row.copied_row_ids:
            new_row.copied_row_ids.append(source_row.id)
            new_row.save()
            logger.debug(f"새 행 강제 업데이트 후 copied_row_ids: {new_row.copied_row_ids}")
        
        # === AttributeValue 복사 ===
        source_values = AttributeValue.objects.filter(row=source_row)
        logger.info(f"복사할 AttributeValue 개수: {source_values.count()}")
        
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
                        logger.debug(f"파일 데이터 파싱 성공: {file_data}")
                        
                        original_filename = file_data.get('original_filename', '')
                        stored_filename = file_data.get('stored_filename', '')
                        s3_key = file_data.get('s3_key', '')
                        
                        logger.debug(f"파일 정보 - 원본명: {original_filename}, 저장명: {stored_filename}, S3키: {s3_key}")
                        
                        if s3_key and stored_filename:
                            # 새로운 파일명 생성 (UUID 사용)
                            file_extension = os.path.splitext(original_filename)[1] if original_filename else ''
                            new_filename = f"{uuid.uuid4()}{file_extension}"
                            logger.debug(f"새 파일명 생성: {new_filename}")
                            
                            # S3에서 파일 복사
                            logger.debug(f"S3 파일 복사 시작: {s3_key} -> {new_filename}")
                            copy_result = copy_s3_file(s3_key, new_filename)
                            logger.debug(f"S3 복사 결과: {copy_result}")
                            
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
                                
                                logger.debug(f"새 파일 데이터 생성: {new_file_data}")
                                
                                # 새로운 파일 정보로 AttributeValue 생성
                                new_attr_value = AttributeValue.objects.create(
                                    row=new_row,
                                    attribute=source_value.attribute,
                                    value=json.dumps(new_file_data, ensure_ascii=False),
                                    copy_from=source_row.id  # 원본 행 ID 저장
                                )
                                logger.debug(f"새 AttributeValue 생성 완료: ID {new_attr_value.id}")
                            else:
                                # S3 복사 실패 시 새로운 파일명으로 원본 파일 정보 복사
                                error_msg = '알 수 없는 오류'
                                if isinstance(copy_result, dict):
                                    error_msg = copy_result.get('error', '알 수 없는 오류')
                                logger.warning(f"파일 복사 실패, 새로운 파일명으로 원본 정보 복사: {error_msg}")
                                
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
                                logger.debug(f"원본 파일 정보로 새 AttributeValue 생성 완료")
                        else:
                            # 파일 정보가 없거나 불완전한 경우 원본 그대로 복사
                            logger.warning(f"파일 정보 불완전, 원본 그대로 복사")
                            AttributeValue.objects.create(
                                row=new_row,
                                attribute=source_value.attribute,
                                value=source_value.value,
                                copy_from=source_row.id  # 원본 행 ID 저장
                            )
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        # JSON 파싱 실패 시 원본 그대로 복사
                        logger.error(f"파일 정보 파싱 실패, 원본 그대로 복사: {e}")
                        AttributeValue.objects.create(
                            row=new_row,
                            attribute=source_value.attribute,
                            value=source_value.value,
                            copy_from=source_row.id  # 원본 행 ID 저장
                        )
                else:
                    # 파일이 아닌 경우 원본 그대로 복사
                    logger.debug(f"일반 속성 복사: {source_value.attribute.name if source_value.attribute else 'None'}")
                    AttributeValue.objects.create(
                        row=new_row,
                        attribute=source_value.attribute,
                        value=source_value.value,
                        copy_from=source_row.id  # 원본 행 ID 저장
                    )
                logger.debug(f"=== AttributeValue 복사 완료 ===")
            except Exception as e:
                # 개별 AttributeValue 복사 중 오류가 발생해도 계속 진행
                logger.error(f"AttributeValue 복사 중 오류 발생: {e}")
                continue
        
        logger.info(f"복제 완료: 새 행 ID {new_row.id}")
        
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
    logger.info(f"=== S3 파일 복사 시작 ===")
    logger.info(f"소스 S3 키: {source_s3_key}")
    logger.info(f"새 파일명: {new_filename}")
    
    try:
        # S3 클라이언트 생성
        logger.debug("S3 클라이언트 생성 중...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        logger.debug("S3 클라이언트 생성 완료")
        
        # 새로운 S3 키 생성
        new_s3_key = f"{settings.AWS_LOCATION}/{new_filename}"
        logger.debug(f"새 S3 키: {new_s3_key}")
        
        # S3에서 파일 복사
        logger.debug("S3 파일 복사 실행 중...")
        s3_client.copy_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CopySource={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': source_s3_key},
            Key=new_s3_key
        )
        logger.debug("S3 파일 복사 완료")
        
        # 새로운 다운로드 URL 생성
        new_download_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{new_s3_key}"
        logger.debug(f"새 다운로드 URL: {new_download_url}")
        
        # 새로운 서명된 다운로드 URL 생성
        try:
            logger.debug("서명된 다운로드 URL 생성 중...")
            new_signed_download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': new_s3_key
                },
                ExpiresIn=300  # 5분
            )
            logger.debug("서명된 다운로드 URL 생성 완료")
        except Exception as e:
            logger.error(f"새로운 서명된 다운로드 URL 생성 실패: {e}")
            new_signed_download_url = new_download_url
        
        # 새로운 서명된 미리보기 URL 생성
        try:
            logger.debug("서명된 미리보기 URL 생성 중...")
            new_signed_preview_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': new_s3_key,
                    'ResponseContentDisposition': 'inline'
                },
                ExpiresIn=300  # 5분
            )
            logger.debug("서명된 미리보기 URL 생성 완료")
        except Exception as e:
            logger.error(f"새로운 서명된 미리보기 URL 생성 실패: {e}")
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
        logger.info(f"S3 파일 복사 성공: {result}")
        return result
        
    except Exception as e:
        logger.error(f"S3 파일 복사 실패: {e}")
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
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'속성 처리 중 오류: {str(e)}'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
                logger.debug(f"Cascade 속성 찾음: {field}")
            except Exception as e:
                logger.debug(f"Cascade 속성 조회 중 오류: {str(e)}")
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
                    logger.warning(f"원본 행 {original_id}를 찾을 수 없습니다.")
                    continue
            
            # 2. 현재 행의 복제된 행들
            copied_rows = []
            for copied_id in current_row.copied_row_ids:
                try:
                    copied_row = Row.objects.get(id=copied_id, user=user)
                    copied_rows.append(copied_row)
                except Row.DoesNotExist:
                    logger.warning(f"복제된 행 {copied_id}를 찾을 수 없습니다.")
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
            
            logger.debug(f"동기화할 관련 행들: {[row.id for row in unique_related_rows]}")
            
            # 각 관련 행에 대해 해당 필드의 값을 가져와서 종속된 행 목록에 추가
            for dep_row in unique_related_rows:
                try:
                    attr_value = AttributeValue.objects.get(row=dep_row, attribute=cascade_attribute)
                    dependent_rows.append({
                        'row_id': dep_row.id,
                        'field': field,
                        'value': attr_value.value
                    })
                    logger.debug(f"종속된 행 추가: {dep_row.id}, {field}, {attr_value.value}")
                except AttributeValue.DoesNotExist:
                    # 해당 속성의 값이 없으면 빈 값으로 설정
                    dependent_rows.append({
                        'row_id': dep_row.id,
                        'field': field,
                        'value': ''
                    })
                    logger.debug(f"종속된 행 추가 (빈 값): {dep_row.id}, {field}")
            
            return JsonResponse({
                'success': True,
                'dependent_rows': dependent_rows
            })
            
        except Exception as e:
            logger.error(f"get_dependent_rows 오류: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})



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

@require_GET
def get_daily_view_counts(request):
    """일별 조회수 통계를 반환하는 API"""
    try:
        page_type = request.GET.get('page_type', 'diary')  # main 또는 diary
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # 날짜 범위 설정
        if start_date and end_date:
            # 특정 기간 조회
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            date_filter = {'date__range': [start_date, end_date]}
        else:
            # 전체 기간 조회 (날짜 필터 없음)
            start_date = None
            end_date = None
            date_filter = {}

        # 일별 조회수 집계
        daily_counts = DailyViewRecord.objects.filter(
            page_type=page_type,
            **date_filter
        ).values('date').annotate(
            total_count=Sum('count'),
            unique_ips=Count('ip', distinct=True)
        ).order_by('date')
        
        # 날짜별로 데이터 구성
        date_data = {}
        for record in daily_counts:
            date_data[record['date'].isoformat()] = {
                'total_count': record['total_count'],
                'unique_ips': record['unique_ips']
            }
        
        # 전체 기간 통계
        total_stats = DailyViewRecord.objects.filter(
            page_type=page_type,
            **date_filter
        ).aggregate(
            total_count=Sum('count'),
            total_unique_ips=Count('ip', distinct=True)
        )
        
        response_data = {
            'success': True,
            'page_type': page_type,
            'daily_data': date_data,
            'total_stats': total_stats
        }
        
        # 날짜 범위가 지정된 경우에만 start_date, end_date 포함
        if start_date and end_date:
            response_data['start_date'] = start_date.isoformat()
            response_data['end_date'] = end_date.isoformat()
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_GET
def get_daily_view_details(request):
    """특정 날짜의 상세 조회수 정보를 반환하는 API"""
    try:
        page_type = request.GET.get('page_type', 'diary')
        date_str = request.GET.get('date')
        
        if not date_str:
            return JsonResponse({'success': False, 'error': '날짜가 필요합니다.'})
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 해당 날짜의 상세 정보
        daily_records = DailyViewRecord.objects.filter(
            page_type=page_type,
            date=target_date
        ).order_by('-count', 'ip')
        
        records_data = []
        for record in daily_records:
            records_data.append({
                'ip': record.ip,
                'count': record.count,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            })
        
        # 해당 날짜 통계
        date_stats = daily_records.aggregate(
            total_count=Sum('count'),
            unique_ips=Count('ip', distinct=True)
        )
        
        return JsonResponse({
            'success': True,
            'date': date_str,
            'page_type': page_type,
            'records': records_data,
            'stats': date_stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



