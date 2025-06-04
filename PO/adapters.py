from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import login
from django.conf import settings

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = request.user
        print("🔍 현재 request.user:", user)

        if user.is_authenticated:
            if not sociallogin.is_existing:
                sociallogin.connect(request, user)
        else:
            if sociallogin.is_existing:
                # ✅ 인증 백엔드 명시
                sociallogin.user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, sociallogin.user)
                print("✅ 기존 소셜 계정 사용자 로그인 처리 완료")
