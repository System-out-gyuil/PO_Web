from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import re
from diary.models import ClassForm

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
    
    context = {
        'is_mobile': is_mobile,
        'user_agent': user_agent,  # 디버깅용 (필요시 제거)
    }
    
    return render(request, 'ai_class/ai_class.html', context)

def class_form(request: HttpRequest):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # 유효성 검사
        errors = {}
        
        if not name:
            errors['name'] = '이름을 입력해주세요.'
        
        if not phone:
            errors['phone'] = '연락처를 입력해주세요.'
        elif not re.match(r'^01[0-9]{8,9}$', phone):
            errors['phone'] = '올바른 휴대폰 번호를 입력해주세요.'
        
        if errors:
            context = {
                'errors': errors,
                'name': name,
                'phone': phone
            }
            return render(request, 'ai_class/class_form.html', context)
        
        # 전화번호 형식 변환 (01012341234 -> 010-1234-1234)
        formatted_phone = format_phone_number(phone)
        
        try:
            # 데이터베이스에 저장
            ClassForm.objects.create(
                name=name,
                phone=formatted_phone
            )
            
            # 성공 메시지와 함께 리다이렉트
            messages.success(request, '클래스 신청이 완료되었습니다!')
            return redirect('class')
            
        except Exception as e:
            errors['general'] = '저장 중 오류가 발생했습니다. 다시 시도해주세요.'
            context = {
                'errors': errors,
                'name': name,
                'phone': phone
            }
            return render(request, 'ai_class/class_form.html', context)
    
    return render(request, 'ai_class/class_form.html')

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

