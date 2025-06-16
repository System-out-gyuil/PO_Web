from django.shortcuts import render, redirect
from django.views import View
from counsel.models import Counsel, Inquiry
from board.models import BizInfo
from config import ADMIN_PASSWORD  # 🔥 config에서 비밀번호 불러오기
from main.models import Count, Count_by_date
from collections import defaultdict
from datetime import datetime, timedelta
from django.utils.timezone import localtime
from django.http import JsonResponse
from datetime import date
from main.models import IpAddress
from django.contrib.auth.models import User
from po_admin.models import CustUser, AdminMember
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db.models import Max

class AdminLoginView(View):
    def get(self, request):
        return render(request, 'po_admin/po_admin_login.html')

    def post(self, request):
        member_id = request.POST.get('member_id')
        member_pw = request.POST.get('member_pw')

        try:
            member = AdminMember.objects.get(member_id=member_id, member_pw=member_pw)

            # 로그인 성공 → 세션 저장
            request.session['po_admin_authenticated'] = True
            request.session['admin_member_id'] = member.id  # 👉 해당 행의 id 저장

            if member.id == 1:
                return redirect('po_admin_list')
            else:
                return redirect('po_admin_another')

        except AdminMember.DoesNotExist:
            return render(request, 'po_admin/po_admin_login.html', {
                'error': '아이디 또는 비밀번호가 틀렸습니다.'
            })
        
class AdminAnotherView(View):
    def get(self, request):
        if not request.session.get('po_admin_authenticated'):
            return redirect('po_admin_login')
        
        member_id = request.session.get('admin_member_id')

        cust_users = CustUser.objects.filter(admin_member_id=member_id).order_by('-alarm')

        region_list = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
        industry_list = ['농업, 임업 및 어업', '광업', '제조업', '전기, 가스, 증기 및 공기 조절 공급업', '수도, 하수 및 폐기물 처리, 원료 재생업', '건설업', '도매 및 소매업', '운수 및 창고업', '숙박 및 음식점업', '정보통신업', '금융 및 보험업', '부동산업', '전문, 과학 및 기술 서비스업', '사업시설 관리, 사업 지원 및 임대 서비스업', '교육서비스업', '보건업 및 사회복지 서비스업', '예술 스포츠 및 여가관련 서비스업', '협회 및 단체, 수리 및 기타 개인서비스업']
        export_experience_list = ["있음", "없음", "희망"]

        context = { 
            'cust_users': cust_users,
            'region_list': region_list,
            'industry_list': industry_list,
            'export_experience_list': export_experience_list,
            'today': date.today(),
            'yesterday': date.today() - timedelta(days=1),
        }
        return render(request, 'po_admin/po_admin_another.html', context)


class AdminCounselListView(View):
    def get(self, request):
        if not request.session.get('po_admin_authenticated'):
            return redirect('po_admin_login')
        
        member_id = request.session.get('admin_member_id')

        if member_id != 1:
            return redirect('po_admin_another')
        
        # 기본 데이터 조회
        counsels = Counsel.objects.all().order_by('-created_at')
        inquiries = Inquiry.objects.all().order_by('-created_at')
        kakaos = User.objects.all().order_by('-date_joined')
        cust_users = CustUser.objects.all().order_by('-alarm')
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

        region_list = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
        industry_list = ['농업, 임업 및 어업', '광업', '제조업', '전기, 가스, 증기 및 공기 조절 공급업', '수도, 하수 및 폐기물 처리, 원료 재생업', '건설업', '도매 및 소매업', '운수 및 창고업', '숙박 및 음식점업', '정보통신업', '금융 및 보험업', '부동산업', '전문, 과학 및 기술 서비스업', '사업시설 관리, 사업 지원 및 임대 서비스업', '교육서비스업', '보건업 및 사회복지 서비스업', '예술 스포츠 및 여가관련 서비스업', '협회 및 단체, 수리 및 기타 개인서비스업']
        export_experience_list = ["있음", "없음", "희망"]

        # ① 선택된 작성자
        writer = request.GET.get("writer")          # ex) "po_admin"

        # ② 기본 쿼리셋
        cust_users_qs = CustUser.objects.all()

        # ③ 작성자 필터 적용
        if writer and writer != "all":
            cust_users_qs = cust_users_qs.filter(
                admin_member_id__member_id=writer
            )

        cust_users = cust_users_qs.order_by("-alarm")

        # ④ 작성자 목록 (distinct)
        writer_list = (
            CustUser.objects
            .select_related("admin_member_id")
            .values_list("admin_member_id__member_id", flat=True)
            .distinct()
        )

        print(writer_list)

        # 날짜 계산
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 토(5)·일(6)이면 금요일(4)까지 뒤로 이동
        if yesterday.weekday() >= 5:
            # ex) 토요일→1 day, 일요일→2 days 더 빼기
            yesterday -= timedelta(days=yesterday.weekday() - 4)

        context = {
            'counsels': counsels,
            'inquiries': inquiries,
            'kakaos': kakaos,
            'cust_users': cust_users,
            'counts': counts,
            'grouped_counts_by_day': dict(grouped_counts_by_day),  # ✅ 날짜별 카운트
            'ip_count_by_day': ip_count_by_day,  # ✅ 날짜별 중복 없는 IP
            'start': start_date,
            'end': end_date,
            'region_list': region_list,
            'industry_list': industry_list,
            'export_experience_list': export_experience_list,
            'today': today,
            'yesterday': yesterday,
            "cust_users": cust_users,
            "writer_list": writer_list,
            "selected_writer": writer or "all",
        }

        return render(request, 'po_admin/po_admin.html', context)


class CountByDateView(View):
    def get(self, request):
        start_str = request.GET.get("start")
        end_str   = request.GET.get("end")

        # ① 날짜 범위 결정 --------------------------------------------------
        if start_str and end_str:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date   = datetime.strptime(end_str,   "%Y-%m-%d").date()
        else:
            end_date   = date.today()
            start_date = end_date - timedelta(days=6)

        # ② 일별-페이지별 집계 ---------------------------------------------
        grouped = defaultdict(lambda: defaultdict(int))      # {날짜: {type: count}}
        qs = Count_by_date.objects.filter(
            created_at__date__range=(start_date, end_date)
        )
        for item in qs:
            day = item.created_at.date()
            grouped[str(day)][item.count_type] += 1

        # ③ IP 중복 제거 카운트 합치기 --------------------------------------
        ip_day = defaultdict(set)                            # {날짜: set(ip)}
        for ip in IpAddress.objects.filter(
            created_at__date__range=(start_date, end_date)
        ):
            ip_day[ip.created_at.date()].add(ip.ip_address)

        for d, ip_set in ip_day.items():
            grouped[str(d)]["ip_total"] = len(ip_set)

        # ④ **페이지별 총합** 계산 ------------------------------------------
        total_by_page = defaultdict(int)                     # {type: 총합}
        for day_counts in grouped.values():
            for ctype, cnt in day_counts.items():
                total_by_page[ctype] += cnt

        # ⑤ 응답 ------------------------------------------------------------
        return JsonResponse({
            "counts" : {d: dict(v) for d, v in grouped.items()},
            "totals" : dict(total_by_page),                  
            "start"  : str(start_date),
            "end"    : str(end_date),
        })



class CustUserSaveView(View):
    @csrf_exempt
    def post(self, request):
        company_name = request.POST.get("company_name")
        region = request.POST.get("region")
        region_detail = request.POST.get("region_detail")
        start_date = request.POST.get("start_date")
        employee_count = request.POST.get("employee_count")
        industry = request.POST.get("industry")
        sales_for_year = request.POST.get("sales_for_year")
        export_experience = request.POST.get("export_experience")
        job_description = request.POST.get("job_description")

        member_id = request.session.get('admin_member_id')
        admin_member = AdminMember.objects.get(id=member_id)

        cust_user = CustUser.objects.create(
            company_name=company_name,
            region=region,
            region_detail=region_detail,
            start_date=start_date,
            employee_count=employee_count,
            industry=industry,
            sales_for_year=int(sales_for_year),
            export_experience=export_experience,
            job_description=job_description,
            admin_member_id=admin_member
        )
            
        sales = int(sales_for_year)
        period = start_date
        export = export_experience
        empl = int(employee_count)
        employees = ""

        today = datetime.today()
        year_diff = today.year - datetime.strptime(period, "%Y-%m-%d").year
        if today.month < datetime.strptime(period, "%Y-%m-%d").month:
            year_diff -= 1

        if year_diff < 3:
            period = "3년 미만"
        elif year_diff >= 3:
            period = "3년 이상"

        if sales >= 3000000000:
            sales = "30억 이상"
        elif sales >= 1000000000:
            sales = "10~30억"
        elif sales >= 500000000:
            sales = "5~10억"
        elif sales > 100000000:
            sales = "1~5억"
        elif sales <= 100000000:
            sales = "1억 이하"
        else:
            sales = "매출없음"

        if empl == 0:
            employees = "직원 없음"
        elif empl <= 4:
            employees = "1~4인"
        elif empl <= 9:
            employees = "5~9인"
        elif empl <= 10:
            employees = "10인 이상"
            

        if employees in ["1~4인", "5~9인"] and industry in ["광업", "제조업", "건설업", "운수업"] :
            empl = "소상공인"
        elif employees == "1~4인":
            empl = "소상공인"
        elif employees in ["10인 이상", "5~9인"]:
            empl = "중소기업"

        if export == "있음":
            export = "수출 실적 보유"
            
        # ------------------- 지원사업 조회 -------------------
        datas = BizInfo.objects.filter(
            (Q(region__contains=region) | Q(region__contains="전국")) &
            Q(possible_industry__contains=industry) &
            Q(revenue__contains=sales) &
            Q(business_period__contains=period) &
            (Q(export_performance__contains=export) | Q(export_performance__contains="무관")) &
            Q(target__contains=empl)
        ).order_by('-registered_at')

        # ① pblanc_id를 쉼표로 이어진 문자열로 저장
        pblanc_ids = list(datas.values_list("pblanc_id", flat=True))
        cust_user.possible_product = ",".join(pblanc_ids)

        # ② 최신 registered_at 날짜 구해서 alarm 컬럼에 저장
        latest_date = datas.aggregate(latest=Max('registered_at'))['latest']  # datetime 객체
        # 또는 latest_date = datas.first().registered_at  # 이미 order_by('-registered_at') 했으므로 동일

        if latest_date:
            # alarm이 CharField라면 문자열로 변환 (예: YYYY-MM-DD)
            cust_user.alarm = latest_date.strftime('%Y-%m-%d')
            # alarm이 DateTimeField/DateField라면 그대로 할당해도 됨
        else:
            cust_user.alarm = ''  # 조회 결과가 없을 때 처리(필요 시)

        cust_user.save()

        return JsonResponse({"success": True})
    
        
class CustUserUpdateView(View):
    def post(self, request):
        cust_user_id = request.POST.get("cust_user_id")
        cust_user = CustUser.objects.get(id=cust_user_id)

        company_name = request.POST.get("company_name")
        region = request.POST.get("region")
        region_detail = request.POST.get("region_detail")
        start_date = request.POST.get("start_date")
        employee_count = request.POST.get("employee_count")
        industry = request.POST.get("industry")
        sales_for_year = request.POST.get("sales_for_year")
        export_experience = request.POST.get("export_experience")
        job_description = request.POST.get("job_description")

        cust_user.company_name = company_name
        cust_user.region = region
        cust_user.region_detail = region_detail
        cust_user.start_date = start_date
        cust_user.employee_count = employee_count
        cust_user.industry = industry
        cust_user.sales_for_year = sales_for_year
        cust_user.export_experience = export_experience
        cust_user.job_description = job_description

        print(f'sales_for_year: {sales_for_year}')

        sales = int(sales_for_year)
        period = start_date
        export = export_experience
        empl = int(employee_count)
        employees = ""

        today = datetime.today()
        year_diff = today.year - datetime.strptime(start_date, "%Y-%m-%d").year
        if today.month < datetime.strptime(start_date, "%Y-%m-%d").month:
            year_diff -= 1

        if year_diff < 3:
            period = "3년 미만"
        elif year_diff >= 3:
            period = "3년 이상"

        if sales >= 3000000000:
            sales = "30억 이상"
        elif sales >= 1000000000:
            sales = "10~30억"
        elif sales >= 500000000:
            sales = "5~10억"
        elif sales > 100000000:
            sales = "1~5억"
        elif sales <= 100000000:
            sales = "1억 이하"
        else:
            sales = "매출없음"

        if empl == 0:
            employees = "직원 없음"
        elif empl <= 4:
            employees = "1~4인"
        elif empl <= 9:
            employees = "5~9인"
        elif empl <= 10:
            employees = "10인 이상"
            

        if employees in ["1~4인", "5~9인"] and industry in ["광업", "제조업", "건설업", "운수업"] :
            empl = "소상공인"
        elif employees == "1~4인":
            empl = "소상공인"
        elif employees in ["10인 이상", "5~9인"]:
            empl = "중소기업"

        if export == "있음":
            export = "수출 실적 보유"
            
        # ------------------- 지원사업 조회 -------------------
        datas = BizInfo.objects.filter(
            (Q(region__contains=region) | Q(region__contains="전국")) &
            Q(possible_industry__contains=industry) &
            Q(revenue__contains=sales) &
            Q(business_period__contains=period) &
            (Q(export_performance__contains=export) | Q(export_performance__contains="무관")) &
            Q(target__contains=empl)
        ).order_by('-registered_at')

        # ① pblanc_id를 쉼표로 이어진 문자열로 저장
        pblanc_ids = list(datas.values_list("pblanc_id", flat=True))
        cust_user.possible_product = ",".join(pblanc_ids)

        # ② 최신 registered_at 날짜 구해서 alarm 컬럼에 저장
        latest_date = datas.aggregate(latest=Max('registered_at'))['latest']  # datetime 객체
        # 또는 latest_date = datas.first().registered_at  # 이미 order_by('-registered_at') 했으므로 동일

        if latest_date:
            # alarm이 CharField라면 문자열로 변환 (예: YYYY-MM-DD)
            cust_user.alarm = latest_date.strftime('%Y-%m-%d')
            # alarm이 DateTimeField/DateField라면 그대로 할당해도 됨
        else:
            cust_user.alarm = ''  # 조회 결과가 없을 때 처리(필요 시)

        cust_user.save()

        return JsonResponse({"success": True})
    
class CustUserPossibleProductView(View):
    def post(self, request):
        cust_user_id = request.POST.get("cust_user_id")
        cust_user = CustUser.objects.get(id=cust_user_id)

        pblanc_ids = [pid.strip() for pid in cust_user.possible_product.split(",") if pid.strip()]

        data_list = list(
            BizInfo.objects.filter(pblanc_id__in=pblanc_ids)
            .order_by('-registered_at')
            .values()
        )

        # 날짜 계산
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 토(5)·일(6)이면 금요일(4)까지 뒤로 이동
        if yesterday.weekday() >= 5:
            # ex) 토요일→1 day, 일요일→2 days 더 빼기
            yesterday -= timedelta(days=yesterday.weekday() - 4)

        context = {
            "datas": data_list,
            "today": today,
            "yesterday": yesterday,
        }

        return JsonResponse(context, safe=False)


