from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import re
from diary.models import ClassForm, AIClassTextElement, ClassFormTextElement

def ai_class(request: HttpRequest):
    # User-Agent를 통해 모바일 여부 감지
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # 모바일 기기 감지 (간단한 방법)
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone', 'blackberry']
    is_mobile = any(keyword in user_agent for keyword in mobile_keywords)
    
    # 더 정확한 모바일 감지를 위한 추가 조건
    if not is_mobile:
        # 화면 크기나 터치 지원 여부로도 판단
        is_mobile = 'touch' in user_agent or 'tablet' in user_agent
    
    # 텍스트 요소들을 데이터베이스에서 가져오기
    text_elements = {}
    for element in AIClassTextElement.objects.all():
        text_elements[element.key] = element.text
    
    context = {
        'is_mobile': is_mobile,
        'user_agent': user_agent,  # 디버깅용 (필요시 제거)
        'text_elements': text_elements,
    }
    
    return render(request, 'ai_class/ai_class.html', context)

def class_form(request: HttpRequest):
    # 텍스트 요소들을 데이터베이스에서 가져오기
    text_elements_flat = {}
    for element in ClassFormTextElement.objects.all():
        text_elements_flat[element.key] = element.text
    
    # 기본값 설정 (DB에 데이터가 없을 경우 사용)
    default_texts = {
        'form.title': '법인영업 원데이 클래스',
        'form.date': '일자 : 2025년 9월 16일(화요일) 15시 ~ 17시',
        'form.location': '장소 : 구로디지털단지역 인근 (자세한 주소는 추후 문자 안내), 주차가능',
        'form.capacity': '인원 : 선착순 10명',
        'form.bank': '기업은행 : 074-118859-04-015(주식회사 피오코퍼레이션)',
        'form.fee': '강의료 : 5만원',
        'form.notice': '신청서 접수 후 입금완료시, 클래스 참여 확정됩니다.',
        'form.label_name': '참석자 성함을 알려주세요',
        'form.placeholder_name': '이름을 입력해주세요',
        'form.label_phone': '참석자 연락처를 알려주세요',
        'form.placeholder_phone': '연락처를 입력해주세요. (예: 01012341234, 010-1234-1234, 010 1234 1234)',
        'form.phone_description': '연락처로 강의 관련 안내사항을 전달드립니다.',
        'form.button_text': '클래스 신청하기',
    }
    
    # 기본값과 병합 (DB 값이 우선)
    for key, default_value in default_texts.items():
        if key not in text_elements_flat:
            text_elements_flat[key] = default_value
    
    # 중첩 딕셔너리로 변환 (form.title -> text_elements['form']['title'])
    text_elements = {'form': {}}
    for key, value in text_elements_flat.items():
        if key.startswith('form.'):
            nested_key = key.replace('form.', '')
            text_elements['form'][nested_key] = value
        else:
            text_elements[key] = value
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # 유효성 검사
        errors = {}
        
        if not name:
            errors['name'] = '이름을 입력해주세요.'
        
        if not phone:
            errors['phone'] = '연락처를 입력해주세요.'
        elif not is_valid_phone_format(phone):
            errors['phone'] = '올바른 휴대폰 번호 형식을 입력해주세요. (예: 01012341234, 010-1234-1234, 010 1234 1234)'
        
        if errors:
            context = {
                'errors': errors,
                'name': name,
                'phone': phone,
                'text_elements': text_elements,
            }
            return render(request, 'ai_class/class_form.html', context)
        
        # 전화번호 형식 변환 (다양한 형식을 010-1234-1234로 통일)
        formatted_phone = format_phone_number(phone)
        
        try:
            # 데이터베이스에 저장
            ClassForm.objects.create(
                name=name,
                phone=formatted_phone
            )
            
            # 성공 메시지와 함께 리다이렉트
            messages.success(request, '클래스 신청이 완료되었습니다!')
            return redirect('sales:class_form_end')
            
        except Exception as e:
            errors['general'] = '저장 중 오류가 발생했습니다. 다시 시도해주세요.'
            context = {
                'errors': errors,
                'name': name,
                'phone': phone,
                'text_elements': text_elements,
            }
            return render(request, 'ai_class/class_form.html', context)
    
    context = {
        'text_elements': text_elements,
    }
    return render(request, 'ai_class/class_form.html', context)

def is_valid_phone_format(phone):
    """전화번호 형식이 유효한지 검사 (다양한 형식 허용)"""
    # 공백, 하이픈, 점 제거 후 숫자만 추출
    numbers = re.sub(r'[^0-9]', '', phone)
    
    # 010으로 시작하는 10-11자리 숫자인지 확인
    if len(numbers) == 11 and numbers.startswith('01'):
        return True
    elif len(numbers) == 10 and numbers.startswith('01'):
        return True
    
    return False

def format_phone_number(phone):
    """전화번호를 010-1234-1234 형식으로 변환"""
    # 숫자만 추출
    numbers = re.sub(r'[^0-9]', '', phone)
    
    if len(numbers) == 11 and numbers.startswith('01'):
        return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}"
    elif len(numbers) == 10 and numbers.startswith('01'):
        return f"{numbers[:3]}-{numbers[3:6]}-{numbers[6:]}"
    else:
        return phone  # 변환할 수 없는 경우 원본 반환

def class_form_end(request: HttpRequest):
    return render(request, 'ai_class/class_form_end.html')
