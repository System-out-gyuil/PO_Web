from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from datetime import datetime
import json
from config import ES_API_KEY, BIZINFO_API_KEY
from board.models import BizInfo
from main.models import Count, IpAddress
import requests

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
                # 프록시를 거쳤을 경우, 실제 IP는 리스트 맨 앞에 있음
                ip = x_forwarded_for.split(',')[0]
            else:
                # 직접 접속일 경우
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip = get_client_ip(request)

        print(f'접속 ip: {ip}')

        ip_address = IpAddress.objects.filter(ip_address=ip).first()
        if ip_address:
            ip_address.count += 1
            ip_address.save()
        else:
            IpAddress.objects.create(ip_address=ip, count=1)

        count = Count.objects.get(count_type="main")
        count.value += 1
        count.save()


        return render(request, 'main/main.html', context)

    def post(self, request):
        data = {
            "region": request.POST.get("region", ""),
            "industry": request.POST.get("industry", ""),
            "business_period": request.POST.get("business-period", ""),
            "export": request.POST.get("export", ""),
            "sales_volume": request.POST.get("sales-volume", ""),
            "member_number": request.POST.get("member-number", ""),
        }

        if all(data.values()):
            query_string = "&".join([f"{k}={v}" for k, v in data.items() if v])
            return redirect(f"/search/result/?{query_string}")
        else:
            return render(request, 'main/main.html')

class TermsOfServiceView(View):
    def get(self, request):
        return render(request, 'services/terms_of_service.html')

class PersonalInfoView(View):
    def get(self, request):
        return render(request, 'services/personal_info.html')



