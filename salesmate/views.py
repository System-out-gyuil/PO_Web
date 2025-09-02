from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import random
import string
from datetime import timedelta
from .models import User, EmailVerification

# Create your views here.
class SalesmateView(View):
    def get(self, request):
        # 로그인 상태 확인 (선택적)
        user_id = request.session.get('salesmate_member_id')
        user_name = request.session.get('salesmate_member_name', '게스트')
        is_admin = False
        
        # 로그인된 사용자가 있는 경우에만 사용자 정보 확인
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if user.activate:
                    user_name = user.name
                    is_admin = user.is_admin
                else:
                    # 비활성화된 사용자는 세션만 정리하고 게스트로 처리
                    request.session.flush()
                    user_name = '게스트'
            except User.DoesNotExist:
                # 사용자가 존재하지 않으면 세션만 정리하고 게스트로 처리
                request.session.flush()
                user_name = '게스트'
        
        context = {
            'user_name': user_name,
            'is_admin': is_admin,
            'is_logged_in': bool(user_id and request.session.get('salesmate_authenticated')),
        }
        
        return render(request, 'salesmate/salesmate_main.html', context)

class SalesmateLoginView(View):
    def get(self, request):
        # 로그인된 사용자인지 확인
        if request.session.get('salesmate_authenticated'):
            user_id = request.session.get('salesmate_member_id')
            try:
                user = User.objects.get(id=user_id)
                if user.activate:
                    # 로그인된 사용자는 메인 페이지로 리다이렉트
                    return redirect('/salesmate/')
            except User.DoesNotExist:
                # 사용자가 존재하지 않으면 세션 정리
                request.session.flush()
        
        return render(request, 'salesmate/salesmate_login.html')
    
    def post(self, request):
        try:
            member_id = request.POST.get('member_id', '').strip()
            member_pw = request.POST.get('member_pw', '').strip()
            
            if not member_id or not member_pw:
                return JsonResponse({
                    'success': False,
                    'message': '이메일과 비밀번호를 입력해주세요.'
                })
            
            # 사용자 조회
            try:
                user = User.objects.get(email=member_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': '존재하지 않는 이메일입니다.'
                })
            
            # 비밀번호 확인
            if not check_password(member_pw, user.password):
                return JsonResponse({
                    'success': False,
                    'message': '비밀번호가 올바르지 않습니다.'
                })
            
            # 활성화 상태 확인
            if not user.activate:
                return JsonResponse({
                    'success': False,
                    'message': '관리자 승인 대기 중입니다. 승인 후 로그인 가능합니다.'
                })
            
            # 세션에 로그인 정보 저장
            request.session['salesmate_authenticated'] = True
            request.session['salesmate_member_id'] = user.id
            request.session['salesmate_member_name'] = user.name
            
            return JsonResponse({
                'success': True,
                'message': '로그인 성공',
                'redirect_url': '/salesmate/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'로그인 중 오류가 발생했습니다: {str(e)}'
            })

class SalesmateSignupView(View):
    def post(self, request):
        try:
            signup_id = request.POST.get('signup_id', '').strip()
            signup_pw = request.POST.get('signup_pw', '').strip()
            signup_pw_confirm = request.POST.get('signup_pw_confirm', '').strip()
            signup_manager_name = request.POST.get('signup_manager_name', '').strip()
            signup_company_name = request.POST.get('signup_company_name', '').strip()
            signup_phone = request.POST.get('signup_phone', '').strip()
            verification_code = request.POST.get('verification_code', '').strip()
            
            # 필수 필드 검증
            if not all([signup_id, signup_pw, signup_pw_confirm, signup_manager_name, signup_company_name, signup_phone, verification_code]):
                return JsonResponse({
                    'success': False,
                    'message': '모든 필드를 입력해주세요.'
                })
            
            # 비밀번호 확인
            if signup_pw != signup_pw_confirm:
                return JsonResponse({
                    'success': False,
                    'message': '비밀번호가 일치하지 않습니다.'
                })
            
            # 이메일 중복 확인
            if User.objects.filter(email=signup_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': '이미 사용 중인 이메일입니다.'
                })
            
            # 이메일 인증 확인
            try:
                verification = EmailVerification.objects.get(
                    email=signup_id,
                    verification_code=verification_code,
                    is_verified=True
                )
                
                # 인증번호 만료 확인
                if verification.is_expired():
                    return JsonResponse({
                        'success': False,
                        'message': '인증번호가 만료되었습니다. 다시 인증해주세요.'
                    })
                    
            except EmailVerification.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': '이메일 인증을 완료해주세요.'
                })
            
            # 사용자 생성 (activate=False로 생성하여 관리자 승인 대기 상태)
            user = User.objects.create(
                email=signup_id,
                password=make_password(signup_pw),
                name=signup_manager_name,
                company_name=signup_company_name,
                manager_name=signup_manager_name,
                phone_number=signup_phone,
                activate=False  # 관리자 승인 대기 상태
            )
            
            # 인증 정보 삭제
            verification.delete()
            
            return JsonResponse({
                'success': True,
                'message': '회원가입이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'회원가입 중 오류가 발생했습니다: {str(e)}'
            })

class SalesmateCheckEmailDuplicateView(View):
    def post(self, request):
        try:
            email = request.POST.get('email', '').strip()
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': '이메일을 입력해주세요.'
                })
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': '이미 사용 중인 이메일입니다.'
                })
            
            return JsonResponse({
                'success': True,
                'message': '사용 가능한 이메일입니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'이메일 중복 확인 중 오류가 발생했습니다: {str(e)}'
            })

class SalesmateSendVerificationEmailView(View):
    def post(self, request):
        try:
            email = request.POST.get('email', '').strip()
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': '이메일을 입력해주세요.'
                })
            
            # 6자리 랜덤 인증번호 생성
            verification_code = ''.join(random.choices(string.digits, k=6))
            
            # 기존 인증 정보 삭제
            EmailVerification.objects.filter(email=email).delete()
            
            # 새 인증 정보 생성 (5분 후 만료)
            expires_at = timezone.now() + timedelta(minutes=5)
            EmailVerification.objects.create(
                email=email,
                verification_code=verification_code,
                expires_at=expires_at
            )
            
            # 이메일 발송
            subject = '[Salesmate] 이메일 인증번호'
            message = f'''
안녕하세요.

Salesmate 회원가입을 위한 이메일 인증번호입니다.

인증번호: {verification_code}

이 인증번호는 5분 후 만료됩니다.
인증번호를 정확히 입력해주세요.

            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'success': True,
                'message': '인증번호가 발송되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'인증번호 발송 중 오류가 발생했습니다: {str(e)}'
            })

class SalesmateVerifyEmailView(View):
    def post(self, request):
        try:
            email = request.POST.get('email', '').strip()
            verification_code = request.POST.get('verification_code', '').strip()
            
            if not email or not verification_code:
                return JsonResponse({
                    'success': False,
                    'message': '이메일과 인증번호를 입력해주세요.'
                })
            
            try:
                verification = EmailVerification.objects.get(
                    email=email,
                    verification_code=verification_code
                )
                
                # 인증번호 만료 확인
                if verification.is_expired():
                    return JsonResponse({
                        'success': False,
                        'message': '인증번호가 만료되었습니다. 다시 발송해주세요.'
                    })
                
                # 인증 완료 처리
                verification.is_verified = True
                verification.save()
                
                return JsonResponse({
                    'success': True,
                    'message': '이메일 인증이 완료되었습니다.'
                })
                
            except EmailVerification.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': '올바르지 않은 인증번호입니다.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'이메일 인증 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class SalesmateLogoutView(View):
    def post(self, request):
        try:
            # 세션 정보 삭제
            request.session.pop('salesmate_authenticated', None)
            request.session.pop('salesmate_member_id', None)
            request.session.pop('salesmate_member_name', None)
            
            return JsonResponse({
                'success': True,
                'message': '로그아웃되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'로그아웃 중 오류가 발생했습니다: {str(e)}'
            })

class SalesmatePersonalInfoView(View):
    def get(self, request):
        return render(request, 'salesmate/personal_info.html')

class SalesmateTermsOfServiceView(View):
    def get(self, request):
        return render(request, 'salesmate/terms_of_service.html')

class SalesmateAdminView(View):
    def get(self, request):
        # 관리자 권한 확인
        if not request.session.get('salesmate_authenticated'):
            return redirect('/salesmate/login/')
        
        user_id = request.session.get('salesmate_member_id')
        try:
            user = User.objects.get(id=user_id)
            if not user.is_admin:
                return redirect('/salesmate/')
        except User.DoesNotExist:
            return redirect('/salesmate/login/')
        
        # 승인 대기 중인 사용자 목록
        pending_users = User.objects.filter(activate=False).order_by('-created_at')
        
        # 승인된 사용자 목록
        approved_users = User.objects.filter(activate=True).order_by('-created_at')
        
        context = {
            'pending_users': pending_users,
            'approved_users': approved_users,
        }
        
        return render(request, 'salesmate/admin.html', context)

class SalesmateApproveUserView(View):
    def post(self, request):
        # 관리자 권한 확인
        if not request.session.get('salesmate_authenticated'):
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
        
        user_id = request.session.get('salesmate_member_id')
        try:
            admin_user = User.objects.get(id=user_id)
            if not admin_user.is_admin:
                return JsonResponse({'success': False, 'message': '관리자 권한이 필요합니다.'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
        
        try:
            target_user_id = request.POST.get('user_id')
            if not target_user_id:
                return JsonResponse({'success': False, 'message': '사용자 ID가 필요합니다.'})
            
            target_user = User.objects.get(id=target_user_id)
            target_user.activate = True
            target_user.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{target_user.name}님의 회원가입이 승인되었습니다.'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '승인할 사용자를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'승인 처리 중 오류가 발생했습니다: {str(e)}'})

class SalesmateRejectUserView(View):
    def post(self, request):
        # 관리자 권한 확인
        if not request.session.get('salesmate_authenticated'):
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
        
        user_id = request.session.get('salesmate_member_id')
        try:
            admin_user = User.objects.get(id=user_id)
            if not admin_user.is_admin:
                return JsonResponse({'success': False, 'message': '관리자 권한이 필요합니다.'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
        
        try:
            target_user_id = request.POST.get('user_id')
            if not target_user_id:
                return JsonResponse({'success': False, 'message': '사용자 ID가 필요합니다.'})
            
            target_user = User.objects.get(id=target_user_id)
            target_user.delete()  # 사용자 삭제
            
            return JsonResponse({
                'success': True, 
                'message': f'{target_user.name}님의 회원가입이 거부되었습니다.'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': '거부할 사용자를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'거부 처리 중 오류가 발생했습니다: {str(e)}'})