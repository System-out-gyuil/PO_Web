from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from datetime import datetime
import json
from config import ES_API_KEY, BIZINFO_API_KEY
from board.models import BizInfo
from main.models import Count, IpAddress, Count_by_date
import requests
from django.http import HttpResponse
from datetime import date

# 구글 애드센스 ads.txt 검증용
class Ads(View):
    def get(self, request):
        return HttpResponse("google.com, pub-6882409851484122, DIRECT, f08c47fec0942fa0", content_type='text/plain')

class MainView(View):
    def get(self, request):
        biz_list_10 = BizInfo.objects.all().order_by('-registered_at')[:10]

        # 인기 공고 10개 직접 입력
        pblanc_ids = [
            'PBLN_000000000109562',
            'PBLN_000000000109448',
            'PBLN_000000000109555',
            'PBLN_000000000109464',
            'PBLN_000000000109685',
            'PBLN_000000000109439',
            'PBLN_000000000109783',
            'PBLN_000000000109668',
            'PBLN_000000000109768',
            'PBLN_000000000109784',
        ]

        biz_top_10 = list(BizInfo.objects.filter(pblanc_id__in=pblanc_ids))

        context = {
            'biz_list': biz_list_10,
            'biz_top_10': biz_top_10
        }


        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip = get_client_ip(request)
        today = date.today()

        # ✅ 오늘 이 IP로 기록된 적 있는지 확인
        already_exists = IpAddress.objects.filter(ip_address=ip, created_at__date=today).exists()

        if not already_exists:
            # ✅ 조회수 증가
            count = Count.objects.get(count_type="main")
            count.value += 1
            count.save()

            Count_by_date.objects.create(count_type="main")

            # ✅ 오늘 처음 방문한 IP로 기록
            IpAddress.objects.create(ip_address=ip, count=1)
        else:
            print(f"{ip}는 이미 오늘 방문 기록 있음 (조회수 미증가)")


        return render(request, 'main/main.html', context)

class TermsOfServiceView(View):
    def get(self, request):
        return render(request, 'services/terms_of_service.html')

class PersonalInfoView(View):
    def get(self, request):
        return render(request, 'services/personal_info.html')



