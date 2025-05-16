from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from datetime import datetime
import json
from config import ES_API_KEY


class MainView(View):
    def get(self, request):
        return render(request, 'main/main.html')

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
            return redirect(f"/search/?{query_string}")
        else:
            return render(request, 'main/main.html')



class SearchResultView(View):
    def get(self, request):
        region = request.GET.get('region')
        industry = request.GET.get('industry')
        business_period = request.GET.get('business_period')
        export = request.GET.get('export')
        sales_volume = request.GET.get('sales_volume')
        member_number = request.GET.get('member_number')
        search_text = request.GET.get('search', '').strip()
        score_filter = request.GET.get('score')
        exact_filter = request.GET.get('exact') == 'true'

        filters = {
            "region": region,
            "industry": industry,
            "business_period": business_period,
            "export": export,
            "sales_volume": sales_volume,
            "member_number": member_number,
        }

        if filters["sales_volume"] == "없음":
            filters["sales_volume"] = "1억 이하"

        if not (region and industry):
            return redirect('main')

        es = Elasticsearch(
            "https://0e0f4480a93d4cb78455e070163e467d.us-central1.gcp.cloud.es.io:443",
            api_key=ES_API_KEY
        )

        def search_support_projects(filters: dict, search_text="", sample_size=500):
            must = []
            should = []

            if search_text:
                must.append({
                    "multi_match": {
                        "query": search_text,
                        "fields": ["title", "content", "noti_summary"]
                    }
                })

            if filters["region"]:
                region_fields = ["region", "title", "content", "noti_summary"]
                must.extend([
                    {"wildcard": {field: f"*{filters['region']}*"}}
                    for field in region_fields
                ])

            if filters["industry"]:
                industry_fields = ["noti_summary", "possible_industry", "content"]
                should.extend([
                    {"wildcard": {field: f"*{filters['industry']}*"}}
                    for field in industry_fields
                ])

            if filters["business_period"]:
                should.append({"wildcard": {"business_period": f"*{filters['business_period']}*"}})

            if filters["export"]:
                should.append({"wildcard": {"export_performance": f"*{filters['export']}*"}})

            if filters["sales_volume"]:
                should.append({"wildcard": {"revenue": f"*{filters['sales_volume']}*"}})

            if filters["member_number"]:
                should.append({"wildcard": {"employee_count": f"*{filters['member_number']}*"}})

            query = {
                "query": {
                    "bool": {
                        "must": must,
                        "should": should,
                        "minimum_should_match": 1 if should else 0
                    }
                },
                "sort": [{"registered_at": {"order": "desc"}}]
            }

            res = es.search(index="bizinfo_index", body=query, size=sample_size)
            return [hit["_source"] for hit in res["hits"]["hits"]]

        def compute_match_score(project, filters):
            score = 0
            log = []

            def flatten_and_join(*fields):
                parts = []
                for f in fields:
                    v = project.get(f, "")
                    if isinstance(v, list):
                        parts.extend(v)
                    elif isinstance(v, str):
                        parts.append(v)
                return " ".join(parts)

            if filters["region"] and filters["region"] in flatten_and_join("region", "title", "content", "noti_summary"):
                score += 1
                log.append("region")

            if filters["industry"] and filters["industry"] in flatten_and_join("noti_summary", "possible_industry", "content"):
                score += 1
                log.append("industry")

            if filters["business_period"] and filters["business_period"] in str(project.get("business_period", "")):
                score += 1
                log.append("business_period")

            if filters["export"] and filters["export"] in str(project.get("export_performance", "")):
                score += 1
                log.append("export")

            if filters["sales_volume"] and filters["sales_volume"] in str(project.get("revenue", "")):
                score += 1
                log.append("sales_volume")

            if filters["member_number"] and filters["member_number"] in str(project.get("employee_count", "")):
                score += 1
                log.append("member_number")

            project["debug_matched_fields"] = log
            return score

        def parse_end_date(project):
            try:
                end_date = project.get("모집기간", {}).get("모집종료일", "")
                if end_date == "9999-12-31":
                    return datetime.max
                return datetime.strptime(end_date, "%Y-%m-%d")
            except:
                return datetime.max

        matched_projects = search_support_projects(filters, search_text)

        for project in matched_projects:
            project["매칭점수"] = compute_match_score(project, filters)

            규모 = project.get('지원규모')
            if isinstance(규모, str):
                try:
                    parsed = json.loads(규모.replace("'", '"'))
                    if isinstance(parsed, dict):
                        project['지원규모'] = parsed
                except json.JSONDecodeError:
                    pass

        for p in matched_projects:
            period = p.get("business_period")
            if str(period) == "['사업자 등록 전']":
                p["사업기간요약"] = "예비 창업"
            elif str(period) == "['사업자 등록 전', '1년 이하', '1~3년']":
                p["사업기간요약"] = "예비 창업 ~ 3년"
            elif str(period) == "['사업자 등록 전', '1년 이하', '1~3년', '3~7년']":
                p["사업기간요약"] = "예비 창업 ~ 7년"
            elif str(period) == "['사업자 등록 전', '1년 이하', '1~3년', '3~7년', '7년 이상']":
                p["사업기간요약"] = "무관"
            elif str(period) == "['1년 이하', '1~3년']":
                p["사업기간요약"] = "사업 시작 ~ 3년"
            elif str(period) == "['1년 이하', '1~3년', '3~7년']":
                p["사업기간요약"] = "사업 시작 ~ 7년"
            elif str(period) == "['1년 이하', '1~3년', '3~7년', '7년 이상']":
                p["사업기간요약"] = "사업 시작 이상"
            elif str(period) == "['1~3년', '3~7년']":
                p["사업기간요약"] = "1~7년"
            elif str(period) == "['1~3년', '3~7년', '7년 이상']":
                p["사업기간요약"] = "1~7년"
            elif str(period) == "['3~7년', '7년 이상']":
                p["사업기간요약"] = "3년 이상"
            else:
                if isinstance(period, list) and "사업자 등록 전" in period:
                    p["사업기간요약"] = "예비 창업"
                else:
                    p["사업기간요약"] = ", ".join(period) if isinstance(period, list) else str(period)

        if score_filter:
            try:
                score_filter = int(score_filter)
                if exact_filter:
                    # ✅ exact=true인 경우: 해당 점수 전체 표시 (페이지네이션 적용)
                    matched_projects = [p for p in matched_projects if p.get("매칭점수", 0) == score_filter]
                else:
                    # ✅ score 필터는 있지만 exact는 없을 때: 기본 동작으로 6,5,4점 하나씩만 노출
                    filtered = []
                    for target_score in [6, 5, 4]:
                        for p in matched_projects:
                            if p.get("매칭점수", 0) == target_score:
                                filtered.append(p)
                                break
                    matched_projects = filtered
            except ValueError:
                pass
        else:
            # ✅ 6, 5, 4점만 각 하나씩 추림
            filtered = []
            for target_score in [6, 5, 4]:
                for p in matched_projects:
                    if p.get("매칭점수", 0) == target_score:
                        filtered.append(p)
                        break  # 해당 점수 중 첫 번째만 추가
            matched_projects = filtered

        matched_projects = sorted(matched_projects, key=lambda p: (-p["매칭점수"], parse_end_date(p)))

        if exact_filter:
            paginator = Paginator(matched_projects, 5)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            results = page_obj
        else:
            results = matched_projects

        return render(request, 'main/search_results.html', {
            'results': results,
            'region': region,
            'industry': industry,
            'sales_volume': sales_volume,
            'member_number': member_number,
            'business_period': business_period,
            'export': export,
            'score': score_filter,
        })



class TermsOfServiceView(View):
    def get(self, request):
        return render(request, 'services/terms_of_service.html')


class PersonalInfoView(View):
    def get(self, request):
        return render(request, 'services/personal_info.html')
