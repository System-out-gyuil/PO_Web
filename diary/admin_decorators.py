from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def admin_required(view_func):
    """관리자 권한이 필요한 뷰에 사용하는 데코레이터"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"admin_required 데코레이터 호출됨 - URL: {request.path}")
        print(f"세션 정보: {request.session}")
        
        # 세션에서 사용자 정보 확인
        user_id = request.session.get('user_id') or request.session.get('diary_member_id')
        if not user_id:
            print("user_id 또는 diary_member_id가 세션에 없음 - 로그인 페이지로 리다이렉트")
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
            messages.error(request, '로그인이 필요합니다.')
            return redirect('/sales/login/')  # 절대 경로 사용
        
        # 사용자 정보 가져오기
        from .models import User
        try:
            user = User.objects.get(id=user_id)
            print(f"사용자 정보: {user.name}, is_admin: {user.is_admin}")
        except User.DoesNotExist:
            print("사용자 정보를 찾을 수 없음 - 로그인 페이지로 리다이렉트")
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': '사용자 정보를 찾을 수 없습니다.'}, status=404)
            messages.error(request, '사용자 정보를 찾을 수 없습니다.')
            return redirect('/sales/login/')  # 절대 경로 사용
        
        # 관리자 권한 확인
        if not user.is_admin:
            print("관리자 권한 없음 - 로그인 페이지로 리다이렉트")
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': '관리자 권한이 필요합니다.'}, status=403)
            messages.error(request, '관리자 권한이 필요합니다.')
            return redirect('/sales/login/')  # 절대 경로 사용
        
        # 관리자인 경우 뷰 함수 실행
        request.user_obj = user  # 뷰에서 사용할 수 있도록 사용자 객체 추가
        return view_func(request, *args, **kwargs)
    
    return wrapper

def admin_required_json(view_func):
    """JSON 응답을 위한 관리자 권한 데코레이터"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 세션에서 사용자 정보 확인
        user_id = request.session.get('user_id') or request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
        
        # 사용자 정보 가져오기
        from .models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': '사용자 정보를 찾을 수 없습니다.'}, status=404)
        
        # 관리자 권한 확인
        if not user.is_admin:
            return JsonResponse({'error': '관리자 권한이 필요합니다.'}, status=403)
        
        # 관리자인 경우 뷰 함수 실행
        request.user_obj = user
        return view_func(request, *args, **kwargs)
    
    return wrapper
