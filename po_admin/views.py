from django.shortcuts import render, redirect
from django.views import View
from counsel.models import Counsel
from config import ADMIN_PASSWORD  # 🔥 config에서 비밀번호 불러오기

class AdminLoginView(View):
    def get(self, request):
        return render(request, 'po_admin/po_admin_login.html')

    def post(self, request):
        password = request.POST.get('password')

        if password == ADMIN_PASSWORD:
            request.session['po_admin_authenticated'] = True  # 세션에 로그인 성공 기록
            return redirect('po_admin_list')
        else:
            return render(request, 'po_admin/po_admin_login.html', {'error': '비밀번호가 틀렸습니다.'})

class AdminCounselListView(View):
    def get(self, request):
        if not request.session.get('po_admin_authenticated'):
            return redirect('po_admin_login')  # 로그인 안 했으면 로그인 페이지로

        counsels = Counsel.objects.all().order_by('-created_at')
        return render(request, 'po_admin/po_admin.html', {'counsels': counsels})
