from django.views import View
from django.http import JsonResponse
from .models import Counsel, Inquiry
from django.shortcuts import render
from main.models import Count, Count_by_date, IpAddress
from datetime import date

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
            count = Count.objects.get(count_type="inquiry")
            count.value += 1
            count.save()

            Count_by_date.objects.create(count_type="inquiry")

            # ✅ 오늘 처음 방문한 IP로 기록
            IpAddress.objects.create(ip_address=ip, count=1)
        else:
            print(f"{ip}는 이미 오늘 방문 기록 있음 (조회수 미증가)")

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
