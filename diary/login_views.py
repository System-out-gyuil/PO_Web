from django.shortcuts import render, redirect
from django.views import View
from .models import User

class LoginView(View):
    def get(self, request):
        return render(request, 'diary/diary_login.html')
    
    def post(self, request):
        member_id = request.POST.get('member_id')
        member_pw = request.POST.get('member_pw')

        print(member_id, member_pw)

        try:
            member = User.objects.get(email=member_id, password=member_pw)

            # 로그인 성공 → 세션 저장
            request.session['diary_authenticated'] = True
            request.session['diary_member_id'] = member.id  # 👉 해당 행의 id 저장

            print(member.id)

            if member.id:
                return redirect('diary_list')

        except User.DoesNotExist:
            return render(request, 'diary/diary_login.html', {
                'error': '아이디 또는 비밀번호가 틀렸습니다.'
            })
    
class LogoutView(View):
    def get(self, request):
        return render(request, 'diary/logout.html')
