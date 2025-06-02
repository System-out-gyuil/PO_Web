from django.views import View
from django.http import JsonResponse
from .models import Counsel, Inquiry
from django.shortcuts import render
from main.models import Count, Count_by_date, IpAddress
from datetime import date
from django.http import JsonResponse
from django.views import View
from .models import Counsel
from PO.management.commands.utils import update_count

class CounselFormView(View):
    def get(self, request):
        company = request.GET.get("name", "").strip()
        phone = request.GET.get("phone", "").strip()
        region = request.GET.get("region", "").strip()
        industry = request.GET.get("big_industry", "").strip()
        industry_detail = request.GET.get("small_industry", "").strip()
        start_date = request.GET.get("business_period", "").strip()
        sales = request.GET.get("sales", "").strip()
        consent = request.GET.get("consent") == "on"
        consent2 = request.GET.get("consent2") == "on"

        if start_date and '.' in start_date:
            parts = start_date.split('.')
            start_date = f'{parts[0]}년{parts[1]}월'
        else:
            start_date = ""

        # 필수값이 하나라도 없으면 저장하지 않음
        required_fields = [company, phone, region, industry, industry_detail, start_date, sales]
        if not all(required_fields):
            return JsonResponse({"status": "error", "message": "모든 항목을 입력해주세요."}, status=400)

        Counsel.objects.create(
            company=company,
            phone=phone,
            region=region,
            industry=industry,
            industry_detail=industry_detail,
            start_date=start_date,
            sales=sales,
            consent=consent,
            consent2=consent2
        )

        return JsonResponse({"status": "success"})

    
class InquiryView(View):
    def get(self, request):

        update_count(request, "inquiry")

        return render(request, 'counsel/inquiry.html')
    
    def post(self, request):
        name = request.POST.get("name", "")
        phone = request.POST.get("phone", "")
        inquiry = request.POST.get("inquiry", "")
        consent = request.POST.get("consent") == "on"
        consent2 = request.POST.get("consent2") == "on"

        Inquiry.objects.create(
            name=name,
            phone=phone,
            inquiry=inquiry,
            consent=consent,
            consent2=consent2
        )

        print(name, phone, inquiry, consent, consent2)
        
        return render(request, 'counsel/thank_you.html')
