from django.shortcuts import render
from django.views import View
from board.models import BizInfo
from main.models import Count, IpAddress, Count_by_date
from django.http import HttpResponse
from datetime import date, timedelta
from PO.management.commands.utils import update_count

def get_week_of_month(dt: date) -> int:
    first_day = dt.replace(day=1)
    first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
    
    # 만약 1일이 월요일이라면 그게 첫째 주의 시작
    if first_day.weekday() == 0:
        first_monday = first_day
    
    delta_days = (dt - first_monday).days
    if delta_days < 0:
        return 1
    return delta_days // 7 + 1


# 구글 애드센스 ads.txt 검증용
class Ads(View):
    def get(self, request):
        return HttpResponse("google.com, pub-6882409851484122, DIRECT, f08c47fec0942fa0", content_type='text/plain')
    
class ImWeb(View):
    def get(self, request):
        return render(request, 'main/imweb.html')

class TestView(View):
    def get(self, request):
        return render(request, 'main/search_test.html')

class MainView(View):
    def get(self, request):
        biz_list_10 = BizInfo.objects.all().order_by('-registered_at')[:15]

        # 인기 공고 10개 직접 입력
        pblanc_ids = [
            'PBLN_000000000110190',
            'PBLN_000000000110170',
            'PBLN_000000000110168',
            'PBLN_000000000110160',
            'PBLN_000000000110189',
            'PBLN_000000000110182',
            'PBLN_000000000110162',
            'PBLN_000000000110165',
            'PBLN_000000000110184',
            'PBLN_000000000110169',
            'PBLN_000000000110167',
            'PBLN_000000000110188',
            'PBLN_000000000110185',
            'PBLN_000000000110183',
            'PBLN_000000000110164',
        ]

        biz_top_10 = list(BizInfo.objects.filter(pblanc_id__in=pblanc_ids))

        today = date.today()
        month = today.month
        week = get_week_of_month(today)
        current_week_str = f"{month}월 {week}주차"

        context = {
            'biz_list': biz_list_10,
            'biz_top_10': biz_top_10,
            'current_week_str': current_week_str
        }

        update_count(request, "main")
        return render(request, 'main/main.html', context)

class TermsOfServiceView(View):
    def get(self, request):
        return render(request, 'services/terms_of_service.html')

class PersonalInfoView(View):
    def get(self, request):
        return render(request, 'services/personal_info.html')



