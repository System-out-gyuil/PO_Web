from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.contrib.sites.models import Site
from PO.settings import SITE_ID
from django.http import JsonResponse

class KakaoLoginView(View):
    def get(self, request):
        return render(request, "member/login.html")

class PopupCloseView(View):
    def get(self, request):
        return render(request, "member/popup_close.html")

class WhoAmIView(View):
    def get(self, request):
        return JsonResponse({'is_authenticated': request.user.is_authenticated})
