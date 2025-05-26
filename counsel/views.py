from django.views import View
from django.http import JsonResponse
from .models import Counsel, Inquiry
from django.shortcuts import render
from main.models import Count

class CounselFormView(View):
    def get(self, request):
        company = request.GET.get("name", "")
        phone = request.GET.get("phone", "")
        region = request.GET.get("region", "")
        industry = request.GET.get("big_industry", "")
        industry_detail = request.GET.get("small_industry", "")
        start_date = request.GET.get("business_period", "")
        sales = request.GET.get("sales", "")
        consent = request.GET.get("consent") == "on"
        consent2 = request.GET.get("consent2") == "on"

        if start_date and '.' in start_date:
            parts = start_date.split('.')
            start_date = f'{parts[0]}년{parts[1]}월'
        else:
            start_date = ""

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

        count = Count.objects.get(count_type="inquiry")
        count.value += 1
        count.save()

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
