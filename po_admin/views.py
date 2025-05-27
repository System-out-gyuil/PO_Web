from django.shortcuts import render, redirect
from django.views import View
from counsel.models import Counsel, Inquiry
from config import ADMIN_PASSWORD  # 🔥 config에서 비밀번호 불러오기
from main.models import Count, Count_by_date
from collections import defaultdict
from datetime import datetime, timedelta
from django.utils.timezone import localtime
from django.http import JsonResponse
from datetime import date

class AdminLoginView(View):
    def get(self, request):
        return render(request, 'po_admin/po_admin_login.html')

    def post(self, request):
        password = request.POST.get('password')

        if password == ADMIN_PASSWORD:
            request.session['po_admin_authenticated'] = True  # 세션에 로그인 성공 기록
            return redirect('po_admin_list')
        else:
            return render(request, 'po_admin/po_admin_login.html', {'error': '비밀번호가 틀렸습니다.'})

class AdminCounselListView(View):
    def get(self, request):
        if not request.session.get('po_admin_authenticated'):
            return redirect('po_admin_login')

        # 기본 데이터 조회
        counsels = Counsel.objects.all().order_by('-created_at')
        inquiries = Inquiry.objects.all().order_by('-created_at')
        counts = Count.objects.all()

        # 오늘 날짜 기준
        today = date.today()

        # 오늘 날짜만 필터링
        counts_by_date_today = Count_by_date.objects.filter(created_at__date=today)

        # 날짜별 카운트 수집: {count_type: 개수}
        grouped_counts_today = defaultdict(int)
        for item in counts_by_date_today:
            grouped_counts_today[item.count_type] += 1

        print(f'grouped_counts_today: {grouped_counts_today}\n')

        context = {
            'counsels': counsels,
            'inquiries': inquiries,
            'counts': counts,
            'grouped_counts_today': dict(grouped_counts_today),  # 템플릿에서 .items 사용 가능하게 변환
            'today': today
        }

        return render(request, 'po_admin/po_admin.html', context)

class CountByDateView(View):
    def get(self, request):
        start_str = request.GET.get("start")
        end_str = request.GET.get("end")
        result = {}

        try:
            if start_str and end_str:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            else:
                # 기본: 최근 7일
                end_date = date.today()
                start_date = end_date - timedelta(days=6)

            counts = Count_by_date.objects.filter(created_at__date__range=(start_date, end_date))

            grouped = defaultdict(lambda: defaultdict(int))
            for item in counts:
                created = item.created_at.date()
                grouped[created][item.count_type] += 1

            # dict(grouped) 은 {날짜: {count_type: count}} 구조
            response = {
                "counts": {str(k): dict(v) for k, v in grouped.items()},
                "start": str(start_date),
                "end": str(end_date)
            }

            print(f'response.get("counts"): {response.get("counts")}\n')
            return JsonResponse(response)

        except ValueError:
            return JsonResponse({"error": "잘못된 날짜 형식"}, status=400)
