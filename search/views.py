from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
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
from main.models import Count, Count_by_date
class SearchView(View):
    def get(self, request):

        count = Count.objects.get(count_type="search")
        count.value += 1
        count.save()

        count_by_date = Count_by_date.objects.create(count_type="search")
        count_by_date.save()

        return render(request, 'main/search.html')
    
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
        period = request.GET.get("period", "")
        export = request.GET.get("export", "")
        sales = request.GET.get("sales", "")
        employees = request.GET.get("employees", "")

        data = BizInfo.objects.filter((Q(region__contains=region) | Q(region__contains="전국")) & Q(possible_industry__contains=big_industry) & Q(revenue__contains=sales) & Q(hashtag__contains=region))
        

        datas = ''
        datas2 = []

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

            if i.noti_summary:
                datas += f'id: {i.pblanc_id},\n title:{i.title},\n summary:{i.noti_summary},\n region:{i.region}\n\n'

        text = f"""
        당신은 중소기업 지원사업 매칭 전문가입니다.

        ## 기업 정보
        - 사업지 주소지: {region}
        - 업종: 대분류 - {big_industry}, 소분류 - {small_industry}
        - 작년 매출: {sales}
        - 수출 실적: {export}
        - 직원 수: {employees}

        ## 요청 사항
        - 아래 지원 공고 목록을 기반으로, 선정 가능성이 높은 공고를 알려주세요.
        - 지역과 업종은 반드시 일치해야 합니다.
        - 적합도 점수를 100점 만점으로 평가하여 우선순위를 정해주세요.
        - 점수가 70점 이상인 공고만 보여주세요.
        - 동일한 공고는 한 번만 표시해주세요, 절대로 중복이 나타나선 안됩니다. **ID가 같은 공고는 하나만 포함해주세요**
        - 절대 내용을 지어내거나 ID를 임의로 변경하지 마세요.
        - 적합도 점수에 대한 근거(지역과 업종 제외한 다른 근거)를 20자 이내로 작성해주세요.
        - title, summary 등 모두 검토하여 절대로 지역과 업종이 일치하지 않는 공고는 보여주지 마세요.
        - title에 만약 다른 지역 이름이 적혀있을 시 절대로 해당 공고는 보여주지 마시오.

        ## 출력 형식
        각 공고에 대해 다음 정보를 포함한 딕셔너리 형태로 응답해주세요:
        - id: 공고 ID
        - title: 공고 제목
        - score: 적합도 점수
        - reason: 적합도 점수의 근거
        """

        llm = ChatOpenAI(
            temperature=0,
            model_name='gpt-4o-mini',
            openai_api_key=OPEN_AI_API_KEY
        )

        user_input = text + datas
        response = llm.invoke(user_input)
        content = response.content.strip()
        print("[GPT 응답 원본]:", content)

        enc = tiktoken.encoding_for_model("gpt-4o-mini")
        tokens = enc.encode(user_input)
        print(f"입력 토큰 수: {len(tokens)}")

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
            print(i.get("id"), "\n")
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

        count = Count.objects.get(count_type="search_ai_result")
        count.value += 1
        count.save()

        count_by_date = Count_by_date.objects.create(count_type="search_ai_result")
        count_by_date.save()

        unique_datas2 = []
        seen_ids = set()

        for obj in datas2:
            if obj.pblanc_id not in seen_ids:
                seen_ids.add(obj.pblanc_id)
                unique_datas2.append(obj)

        datas2 = unique_datas2


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
