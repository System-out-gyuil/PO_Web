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
from main.models import IpAddress

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

        end_date = date.today()
        start_date = end_date - timedelta(days=6)

        # Count_by_date (중복 포함)
        counts_by_date_range = Count_by_date.objects.filter(created_at__date__range=(start_date, end_date))
        grouped_counts_by_day = defaultdict(lambda: defaultdict(int))

        for item in counts_by_date_range:
            day = item.created_at.date()
            grouped_counts_by_day[str(day)][item.count_type] += 1

        # IP 기준 중복 제거
        ip_entries_range = IpAddress.objects.filter(created_at__date__range=(start_date, end_date))
        ip_by_day = defaultdict(set)
        for entry in ip_entries_range:
            day = entry.created_at.date()
            ip_by_day[day].add(entry.ip_address)

        ip_count_by_day = {str(day): len(ips) for day, ips in ip_by_day.items()}

        # ✅ IP 수를 counts에 통합
        for day_str, ip_count in ip_count_by_day.items():
            grouped_counts_by_day[day_str]["ip_total"] = ip_count


        context = {
            'counsels': counsels,
            'inquiries': inquiries,
            'counts': counts,
            'grouped_counts_by_day': dict(grouped_counts_by_day),  # ✅ 날짜별 카운트
            'ip_count_by_day': ip_count_by_day,  # ✅ 날짜별 중복 없는 IP
            'start': start_date,
            'end': end_date
        }

        return render(request, 'po_admin/po_admin.html', context)


class CountByDateView(View):
    def get(self, request):
        start_str = request.GET.get("start")
        end_str = request.GET.get("end")

        try:
            if start_str and end_str:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            else:
                end_date = date.today()
                start_date = end_date - timedelta(days=6)

            # ✅ 중복 포함 카운트 수집
            counts = Count_by_date.objects.filter(created_at__date__range=(start_date, end_date))
            grouped_counts_by_day = defaultdict(lambda: defaultdict(int))
            for item in counts:
                day = item.created_at.date()
                grouped_counts_by_day[str(day)][item.count_type] += 1

            # ✅ 중복 제거된 IP 수 수집
            ip_entries = IpAddress.objects.filter(created_at__date__range=(start_date, end_date))
            ip_by_day = defaultdict(set)  # {날짜: set(ip)}
            for entry in ip_entries:
                day = entry.created_at.date()
                ip_by_day[day].add(entry.ip_address)  # ✅ 필드명 주의

            # ✅ IP 수를 counts에 통합
            for day_str, ip_set in ip_by_day.items():
                grouped_counts_by_day[str(day_str)]["ip_total"] = len(ip_set)


            # ✅ 응답 JSON 구성
            response = {
                "counts": {str(k): dict(v) for k, v in grouped_counts_by_day.items()},
                "start": str(start_date),
                "end": str(end_date)
            }

            return JsonResponse(response)

        except ValueError:
            return JsonResponse({"error": "잘못된 날짜 형식"}, status=400)
