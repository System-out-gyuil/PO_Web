from django.shortcuts import render
from django.http import HttpRequest

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