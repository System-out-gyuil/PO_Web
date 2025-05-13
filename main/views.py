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

        print(data)

        if data["region"] and data["industry"]:
            query_string = "&".join([f"{k}={v}" for k, v in data.items() if v])
            return redirect(f"/search/?{query_string}")
        else:
            return render(request, 'main/main.html')


class SearchResultView(View):
    def get(self, request):
        region = request.GET.get('region')
        industry = request.GET.get('industry')
        business_period = request.GET.get('business-period')
        export = request.GET.get('export')
        sales_volume = request.GET.get('sales-volume')
        member_number = request.GET.get('member-number')

        filters = {
            "region": region,
            "industry": industry,
            "business_period": business_period,
            "export": export,
            "sales_volume": sales_volume,
            "member_number": member_number,
        }

        region_map = {
                    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시", "인천": "인천광역시",
                    "광주": "광주광역시", "대전": "대전광역시", "울산": "울산광역시", "세종": "세종특별자치시",
                    "경기": "경기도", "강원": "강원특별자치도", "충북": "충청북도", "충남": "충청남도",
                    "전북": "전라북도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도", "제주": "제주특별자치도"
                }

        if not (region and industry):
            return redirect('main')

        es = Elasticsearch(
            "https://0e0f4480a93d4cb78455e070163e467d.us-central1.gcp.cloud.es.io:443",
            api_key=ES_API_KEY
        )
        index_name = "po_index"

        def expand_keywords(field, value):

            keyword_mappings = {
                "export": {
                    "있음": ["수출", "보유"],
                    "없음": ["없음", "미보유"],
                    "희망": ["희망", "계획"],
                    "무관": []
                },
                "sales_volume": {
                    "없음": ["없음", "0원"],
                    "1억 이하": ["1억 이하", "1억 미만"],
                    "1~5억": ["1억", "2억", "3억", "4억", "5억"],
                    "5~10억": ["5억", "6억", "7억", "8억", "9억", "10억"],
                    "10~30억": ["10억", "20억", "30억"],
                    "30억 이상": ["30억", "50억", "100억", "초과"],
                    "무관": []
                },
                "business_period": {
                    "예비창업": ["예비창업", "법인설립 전", "창업 전"],
                    "1년 이하": ["1년 이하", "0.5년", "6개월", "1년 미만"],
                    "1~3년": ["1년", "2년", "3년"],
                    "3~7년": ["3년", "4년", "5년", "6년", "7년"],
                    "7년 이상": ["7년 이상", "10년", "15년", "20년"],
                    "무관": []
                },
                "member_number": {
                    "없음": ["0명", "없음", "무"],
                    "1~4인": ["1인", "2인", "3인", "4인"],
                    "5인 이상": ["5인", "10인", "50인", "100인"],
                    "무관": []
                }
            }

            result = []
            keywords = keyword_mappings.get(field, {}).get(value, [])
            for kw in keywords:
                result.append({"wildcard": {field: f"*{kw}*"}})
            return result

        def search_support_projects(filters: dict, sample_size: int = 100):
            must_conditions = []
            should_conditions = []

            if filters["industry"]:
                must_conditions.append({"match": {"가능업종": filters["industry"]}})

            if filters["region"]:
                should_conditions += [
                    {"match_phrase": {"지역": filters["region"]}},
                    {"wildcard": {"지역": f"*{filters['region']}*"}},
                    {"wildcard": {"공고내용": f"*{filters['region']}*"}}
                ]

            if filters["business_period"]:
                should_conditions.extend(expand_keywords("business_period", filters["business_period"]))
                should_conditions.extend(expand_keywords("사업기간", filters["business_period"]))

            if filters["export"]:
                should_conditions.extend(expand_keywords("export", filters["export"]))
                should_conditions.extend(expand_keywords("수출실적여부", filters["export"]))

            if filters["sales_volume"]:
                should_conditions.extend(expand_keywords("sales_volume", filters["sales_volume"]))
                should_conditions.extend(expand_keywords("매출규모", filters["sales_volume"]))

            if filters["member_number"]:
                should_conditions.extend(expand_keywords("member_number", filters["member_number"]))
                should_conditions.extend(expand_keywords("상시근로자수", filters["member_number"]))

            query = {
                "query": {
                    "bool": {
                        "must": must_conditions,
                        "should": should_conditions,
                        "minimum_should_match": 1
                    }
                }
            }

            res = es.search(index=index_name, body=query, size=sample_size)
            return [hit["_source"] for hit in res["hits"]["hits"]]

        def compute_match_score(project, filters):
            score = 0

            # 지역 비교 (줄임말 매핑 처리)
            user_region = filters["region"]
            full_region = region_map.get(user_region, user_region)
            # 지역과 공고내용에 포함되어 있다면 SCORE 추가
            if full_region in project.get("지역", "") or full_region in project.get("공고내용", ""):
                score += 1

            # 업종 비교 (list 포함 여부)
            industry = filters["industry"]
            if industry and industry in project.get("가능업종", ""):
                score += 1

            # 사업기간 포함 여부
            if filters["business_period"] and filters["business_period"] in project.get("사업기간", ""):
                score += 1

            # 수출 여부
            if filters["export"]:
                if "무관" in project.get("수출실적여부", "") or filters["export"] in project.get("수출실적여부", ""):
                    score += 1

            # 매출규모
            if filters["sales_volume"]:
                if "무관" in project.get("매출규모", "") or filters["sales_volume"] in project.get("매출규모", ""):
                    score += 1

            # 직원 수
            if filters["member_number"]:
                if "무관" in project.get("직원수", "") or filters["member_number"] in project.get("직원수", ""):
                    score += 1

            return score

        def parse_end_date(project):
            try:
                end_date = project.get("모집기간", {}).get("모집종료일", "")
                if end_date == "9999-12-31":
                    return datetime.max
                return datetime.strptime(end_date, "%Y-%m-%d")
            except:
                return datetime.max

        matched_projects = search_support_projects(filters)

        score_5 = []
        score_4 = []
        score_3 = []
        score_2 = []
        score_1 = []

        for project in matched_projects:
            project["매칭점수"] = compute_match_score(project, filters)

            if project["매칭점수"] == 5:
                score_5.append(project)
            elif project["매칭점수"] == 4:
                score_4.append(project)
            elif project["매칭점수"] == 3:
                score_3.append(project)
            elif project["매칭점수"] == 2:
                score_2.append(project)
            elif project["매칭점수"] == 1:
                score_1.append(project)

            규모 = project.get('지원규모')
            if isinstance(규모, str):
                try:
                    parsed = json.loads(규모.replace("'", '"'))
                    if isinstance(parsed, dict):
                        project['지원규모'] = parsed
                except json.JSONDecodeError:
                    pass

        matched_projects = sorted(
            matched_projects,
            key=lambda p: (-p["매칭점수"], parse_end_date(p))
        )

        paginator = Paginator(matched_projects, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'main/search_results.html', {
            'results': page_obj,
            'region': region,
            'industry': industry,
        })
