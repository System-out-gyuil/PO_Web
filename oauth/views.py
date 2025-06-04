from allauth.socialaccount.models import SocialAccount
from django.views import View
from django.shortcuts import render, redirect

class OAuthLoginView(View):
    def get(self, request):
        # 소셜 로그인 로직
        user = SocialAccount.objects.get(user=request.user)
        # 소셜 로그인 플랫폼에서 유저의 정보를 가져오는 로직
        oauth_data = user.extra_data
        # 소셜 로그인 했을 시 어느 플랫폼을 이용했는지 확인
        member_type = user.provider
        # 카카오는 데이터 형식이 달라서 별도로 로직 구성
        if member_type == "kakao":
            member_email = oauth_data.get("kakao_account").get("email")
            member_name = oauth_data.get("properties").get("nickname")
            member_profile = oauth_data.get("properties").get("profile_image")
        else:
            member_email = oauth_data.get("email")
            member_name = oauth_data.get("name")
            member_profile = oauth_data.get("picture")

        print(member_email, member_name, member_profile)
        

        path = '/'

        return redirect(path)
