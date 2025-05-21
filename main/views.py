from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from datetime import datetime
import json
from config import ES_API_KEY
from board.models import BizInfo

class MainView(View):
    def get(self, request):
        biz_list_10 = BizInfo.objects.all()[:10]
        

        context = {
            'biz_list': biz_list_10
        }

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



