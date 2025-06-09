from django.shortcuts import render
from django.views import View
from board.models import BizInfo
from main.models import Count, IpAddress, Count_by_date
from django.http import HttpResponse
from datetime import date
from PO.management.commands.utils import update_count

# 구글 애드센스 ads.txt 검증용
class Ads(View):
    def get(self, request):
        return HttpResponse("google.com, pub-6882409851484122, DIRECT, f08c47fec0942fa0", content_type='text/plain')

class MainView(View):
    def get(self, request):
        biz_list_10 = BizInfo.objects.all().order_by('-registered_at')[:15]

        # 인기 공고 10개 직접 입력
        pblanc_ids = [
            'PBLN_000000000109950',
            'PBLN_000000000110190',
            'PBLN_000000000110043',
            'PBLN_000000000110168',
            'PBLN_000000000110186',
            'PBLN_000000000110189',
            'PBLN_000000000110163',
            'PBLN_000000000110162',
            'PBLN_000000000110165',
            'PBLN_000000000110169',
            'PBLN_000000000110182',
            'PBLN_000000000110184',
            'PBLN_000000000110167',
            'PBLN_000000000110187',
            'PBLN_000000000110188',
        ]

        biz_top_10 = list(BizInfo.objects.filter(pblanc_id__in=pblanc_ids))

        context = {
            'biz_list': biz_list_10,
            'biz_top_10': biz_top_10
        }

        update_count(request, "main")

        return render(request, 'main/main.html', context)

class TermsOfServiceView(View):
    def get(self, request):
        return render(request, 'services/terms_of_service.html')

class PersonalInfoView(View):
    def get(self, request):
        return render(request, 'services/personal_info.html')



