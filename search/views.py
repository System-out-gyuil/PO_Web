from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.core.paginator import Paginator
from datetime import datetime
import json
from config import ES_API_KEY
from elasticsearch import Elasticsearch
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from main.models import Industry
from board.models import BizInfo
from django.db.models import Q
from langchain_openai import ChatOpenAI
import tiktoken
from config import OPEN_AI_API_KEY
import ast
import re
from datetime import datetime, date
from main.models import Count, Count_by_date, IpAddress
from django.utils.decorators import method_decorator
from PO.management.commands.utils import update_count
from django.contrib.auth.mixins import LoginRequiredMixin


class SearchView(View):
    def get(self, request):
        update_count(request, "search")
        
        return render(request, 'main/search.html', {
            'is_authenticated': request.user.is_authenticated
        })


@method_decorator(csrf_exempt, name='dispatch')
class SearchIndustryAPIView(View):
    def post(self, request):
        body = json.loads(request.body)
        keyword = body.get("keyword", "").strip()

        data = Industry.objects.all()

        datas = ''

        for i in data:
            datas += f'대분류:{i.big_category} 소분류:{i.small_category},'

        text = f'업종분류:{datas} \n\n  질문:{keyword}, 내 업종이 정확히 뭔지 모르겠어\n 질문을 기반으로 업종분류에서 맞는 적합한 대분류-소분류를 뽑아줘. 결과는 \n "1번 : 대분류 - 소분류,\n 2번 : 대분류 - 소분류,\n 3번 : 대분류 - 소분류" 형식으로만 출력해.'

        llm = ChatOpenAI(
            temperature=0,
            model_name='gpt-4.1-mini',
            openai_api_key=OPEN_AI_API_KEY
        )

        user_input = text + datas

        response = llm.invoke(user_input)
        content = response.content.replace("**", "").replace("#", "").strip()
        # print("[GPT 응답 원본]:", content)

        clean_text = '\n'.join(line.lstrip() for line in content.split('\n'))

        return JsonResponse({"response": clean_text})

# 띄어쓰기 제외 검색
# @csrf_exempt
# def search_industry(request):
#     if request.method == "GET":
#         keyword = request.GET.get("q", "").strip()
        
#         keyword_no_space = keyword.replace(" ", "")
#         industries = Industry.objects.all()

#         filtered = [
#             i for i in industries
#             if keyword_no_space in i.big_category.replace(" ", "") or
#             keyword_no_space in i.small_category.replace(" ", "")
#         ][:40]

#         results = [
#             {
#                 "big_category": ind.big_category,
#                 "small_category": ind.small_category
#             }
#             for ind in industries
#         ]

#         return JsonResponse(results, safe=False)
    
@csrf_exempt
def search_industry(request):
    if request.method == "GET":
        keyword = request.GET.get("q", "").strip()
        
        # Q 객체를 이용해 big_category 또는 small_category에 keyword가 포함된 항목을 검색
        industries = Industry.objects.filter(
            Q(big_category__icontains=keyword) | Q(small_category__icontains=keyword)
        ).distinct()[:40]

        results = [
            {
                "big_category": ind.big_category,
                "small_category": ind.small_category
            }
            for ind in industries
        ]
        return JsonResponse(results, safe=False)

class SearchAIResultView(View):
    def get(self, request):
        region = request.GET.get("region", "")
        business_style = request.GET.get("business_style", "")
        big_industry = request.GET.get("big_industry", "")
        small_industry = request.GET.get("small_industry", "")
        period = request.GET.get("business_period", "")
        export = request.GET.get("export", "")
        sales = request.GET.get("sales", "")
        employees = request.GET.get("employees", "")


        start_date = datetime.strptime(period, "%y.%m")
        today = datetime.today()
        year_diff = today.year - start_date.year
        if today.month < start_date.month:
            year_diff -= 1

        if year_diff < 3:
            period = "3년 미만"
        elif year_diff >= 3:
            period = "3년 이상"

        empl = ""

        if employees in ["1~4인", "5~9인"] and big_industry in ["광업", "제조업", "건설업", "운수업"] :
            empl = "소상공인"
        elif employees == "1~4인":
            empl = "소상공인"
        elif employees in ["10인 이상", "5~9인"]:
            empl = "중소기업"

        data = BizInfo.objects.filter(
                                        (Q(region__contains=region) | Q(region__contains="전국"))\
                                       & Q(possible_industry__contains=big_industry) \
                                       & Q(revenue__contains=sales)\
                                       & Q(business_period__contains=period) \
                                       & (Q(export_performance__contains=export) | Q(export_performance__contains="무관"))\
                                       & Q(target__contains=empl)
                                       )

        datas = ''
        datas2 = []
        num = 0

        for i in data:
            if "ADD" in i.pblanc_id and employees != "5인 이상":
                obj = BizInfo.objects.get(pblanc_id=i.pblanc_id)
                obj.region = obj.region.replace("[", "").replace("]", "")
                obj.possible_industry = obj.possible_industry.replace("[", "").replace("]", "")
                try:
                    reception_end_date = obj.reception_end
                    today = datetime.today().date()

                    # "9999-12-31" 은 무시
                    if reception_end_date == date(9999, 12, 31):
                        obj.d_day = "none"
                    else:
                        obj.d_day = (reception_end_date - today).days
                except Exception as e:
                    print(f"날짜 파싱 오류: {e}")
                    obj.d_day = "none"

                obj.score = '100'
                obj.reason = '지원 대상 해당 및 지역 일치'
                datas2.append(obj)

            else:
                num += 1
                datas += f'id: {i.pblanc_id},\n title:{i.title},\n summary:{i.noti_summary},\n region:{i.region}\n\n'

        text = f"""
        당신은 지원사업 매칭 전문가입니다.
        주어진 기업 정보와 지원사업 정보를 깊이 있게 분석하여 지원사업이 해당 회사에 도움이 되는지 판단해야 합니다.

        ## 기업 정보
        - 사업지 주소지: {region}
        - 업종: 대분류 - {big_industry}, 소분류 - {small_industry}
        - 작년 매출: {sales}
        - 수출 실적: {export}
        - 직원 수: {employees}

        ## 요청 사항
        1. 기업 정보와 지원사업 정보를 철저히 비교 분석하세요.
        2. 지원사업이 회사의 현재 상황, 필요, 목표와 얼마나 잘 부합하는지 고려하세요.
        3. 회사가 지원사업의 요구사항을 충족시킬 수 있는지 평가하세요.
        4. 지원사업이 회사에 제공할 수 있는 구체적인 이점을 식별하세요.
        5. 잠재적인 불일치 또는 문제점도 고려하세요.

        ## 출력 형식
        각 공고에 대해 다음 정보를 포함한 딕셔너리 형태로 응답해주세요:
        - id: 공고 ID
        - title: 공고 제목
        - score: 적합도 점수  (100점 만점)
        - reason: 적합도 점수의 분석 근거 (100자 이내)\n\n

        주의사항:
        - 결과만 도출하세요. 추가적인 설명이나 소개는 하지 마세요.
        - 한국어로 출력하세요.
        - XML 태그를 사용하지 마세요.
        - 적합도 점수가 50점 이상인 공고만 보여주세요.

        이제 분석을 시작하고 지정된 형식으로 결과를 제시하세요.\n\n
        """

        llm = ChatOpenAI(
            temperature=0,
            model_name='gpt-4.1-mini',
            openai_api_key=OPEN_AI_API_KEY
        )

        user_input = text + datas
        response = llm.invoke(user_input)
        content = response.content.strip()

        # enc = tiktoken.encoding_for_model("gpt-4.1-mini")
        # tokens = enc.encode(user_input)
        # print(f"입력 토큰 수: {len(tokens)}")

        # GPT 응답에서 ```python ... ``` 블록 추출
        try:
            content_cleaned = None

            # 1. 코드 블록 추출
            match = re.search(r"```(?:json|python)?\n([\s\S]*?)```", content)
            if match:
                content_cleaned = match.group(1).strip()
            else:
                if "matching_results" in content:
                    start = content.index("matching_results")
                    content_cleaned = content[start:].split("=", 1)[1].strip()
                elif "matching_opportunities" in content:
                    start = content.index("matching_opportunities")
                    content_cleaned = content[start:].split("=", 1)[1].strip()
                else:
                    content_cleaned = content.strip()

            # ✅ 추가 보정: 코드 블록 안에 대입문이 들어있는 경우 제거
            if content_cleaned.startswith("matching_opportunities") or content_cleaned.startswith("matching_results"):
                content_cleaned = content_cleaned.split("=", 1)[1].strip()

            # 파싱 시도 (JSON 우선 → 파이썬 fallback)
            try:
                contents = json.loads(content_cleaned)
            except json.JSONDecodeError:
                contents = ast.literal_eval(content_cleaned)

        except Exception as e:
            print("파싱 오류:", e)
            print("GPT 응답:", content)
            return render(request, "main/search_ai_result.html", {"datas": [], "error": "GPT 응답 파싱 실패"})

        for i in contents:
            try:
                obj = BizInfo.objects.get(pblanc_id=i.get("id"))
                obj.region = obj.region.replace("[", "").replace("]", "")
                obj.possible_industry = obj.possible_industry.replace("[", "").replace("]", "")

                # ✅ D-day 계산
                try:
                    reception_end_date = obj.reception_end
                    today = datetime.today().date()

                    # "9999-12-31" 은 무시
                    if reception_end_date == date(9999, 12, 31):
                        obj.d_day = "none"
                    else:
                        obj.d_day = (reception_end_date - today).days
                except Exception as e:
                    print(f"날짜 파싱 오류: {e}")
                    obj.d_day = "none"

                obj.score = i.get("score")
                obj.reason = i.get("reason")
                datas2.append(obj)

            except BizInfo.DoesNotExist:
                print(f"DB에 존재하지 않는 공고 ID: {i.get('id')}")
                continue

        update_count(request, "search_ai_result")

        unique_datas2 = []
        seen_ids = set()

        for obj in datas2:
            if obj.pblanc_id not in seen_ids:
                seen_ids.add(obj.pblanc_id)
                unique_datas2.append(obj)

        # 적합도 점수 높은 순 정렬
        datas2 = sorted(unique_datas2, key=lambda x: int(x.score), reverse=True)

        context = {
            "region": region,
            "business_style": business_style,
            "big_industry": big_industry,
            "small_industry": small_industry,
            "period": period,
            "export": export,
            "sales": sales,
            "employees": employees,
            "datas": datas2
        }

        return render(request, "main/search_ai_result.html", context)


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
