from django.shortcuts import render, redirect
from django.views import View
from .models import Counsel

class CounselFormView(View):
    def get(self, request):
        return render(request, 'counsel/counsel_form.html')

    def post(self, request):
        # 데이터 추출
        company = request.POST.get('company')
        phone = request.POST.get('phone')
        region = request.POST.get('region')
        industry = request.POST.get('industry')
        start_date = request.POST.get('start_date')
        sales_2024 = request.POST.get('sales_2024')
        sales_2025 = request.POST.get('sales_2025')
        inquiry_type = request.POST.get('inquiry_type')

        # ✅ 동의 여부 체크박스 값: 체크시 'on', 미체크시 None
        consent = bool(request.POST.get('consent'))
        consent2 = bool(request.POST.get('consent2'))

        # 디버깅 로그 (선택)
        print(company, phone, region, industry, start_date, sales_2024, sales_2025, inquiry_type, consent, consent2)

        # DB 저장
        Counsel.objects.create(
            company=company,
            phone=phone,
            region=region,
            industry=industry,
            start_date=start_date,
            sales_2024=sales_2024,
            sales_2025=sales_2025,
            inquiry_type=inquiry_type,
            consent=consent,
            consent2=consent2
        )

        # 성공 후 thank_you 페이지로 리디렉션
        return redirect('thank_you')


class ThankYouView(View):
    def get(self, request):
        return render(request, 'counsel/thank_you.html')
