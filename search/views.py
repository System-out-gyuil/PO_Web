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
        detail_region = request.GET.get("detail_region", "")
        business_style = request.GET.get("business_style", "")
        big_industry = request.GET.get("big_industry", "")
        small_industry = request.GET.get("small_industry", "")
        period = request.GET.get("business_period", "")
        export = request.GET.get("export", "")
        sales = request.GET.get("sales", "")
        employees = request.GET.get("employees", "")

        print(region)
        print(detail_region)
        print(big_industry)
        print(export)
        print(sales)
        print(employees)

        # 지역 정보 구성 (상세지역이 있으면 포함)
        full_region = region
        if detail_region:
            full_region = f"{region} {detail_region}"

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

                                    #    & Q(target__contains=empl)\
        print(period)


        # detail_region이 포함된 데이터 먼저 검색 (정확한 일치만)
        if detail_region:
            # 상세지역이 정확히 포함된 데이터만 검색
            data_with_detail = BizInfo.objects.filter(
                                            (Q(region__contains=region) | Q(region__contains="전국") | Q(hashtag__contains=region))\
                                           & (Q(possible_industry__contains=big_industry) | Q(possible_industry__contains='무관')) \
                                           & (Q(revenue__contains=sales) | Q(revenue__contains='무관')) \
                                           & (Q(business_period__contains=period) | Q(business_period__contains='무관')) \
                                           & (
                                               # 상세지역이 포함된 경우만
                                               Q(noti_summary__contains=detail_region) | 
                                               Q(hashtag__contains=detail_region) | 
                                               Q(content__contains=detail_region) | 
                                               Q(title__contains=detail_region) |
                                               Q(region__contains=detail_region)
                                           )
                                           ).order_by('-registered_at')
            
            # detail_region이 포함되지 않은 데이터 검색
            # 단, 다른 상세지역만 특정되어 있는 경우는 제외
            data_without_detail = BizInfo.objects.filter(
                                            (Q(region__contains=region) | Q(region__contains="전국") | Q(hashtag__contains=region))\
                                           & (Q(possible_industry__contains=big_industry) | Q(possible_industry__contains='무관')) \
                                           & (Q(revenue__contains=sales) | Q(revenue__contains='무관')) \
                                           & (Q(business_period__contains=period) | Q(business_period__contains='무관')) \
                                           ).exclude(
                                               # detail_region이 포함된 데이터 제외
                                               Q(noti_summary__contains=detail_region) | 
                                               Q(hashtag__contains=detail_region) | 
                                               Q(content__contains=detail_region) | 
                                               Q(title__contains=detail_region) |
                                               Q(region__contains=detail_region)
                                           ).exclude(
                                               # 다른 상세지역만 특정되어 있는 경우 제외
                                               # regionDetails에 정의된 실제 상세지역 목록을 기반으로 필터링
                                               self._build_detail_region_exclude_query(region, detail_region)
                                           ).order_by('-registered_at')
            
            print(f"DEBUG: detail_region '{detail_region}' 포함된 데이터: {data_with_detail.count()}개")
            print(f"DEBUG: detail_region '{detail_region}' 포함되지 않았고 다른 상세지역도 없는 데이터: {data_without_detail.count()}개")
            
            # detail_region이 포함된 데이터가 100개 미만인 경우, 포함되지 않은 데이터도 추가
            if data_with_detail.count() < 100:
                # 포함되지 않은 데이터에서 필요한 만큼 추가 (중복 제거)
                needed_count = 100 - data_with_detail.count()
                additional_data = data_without_detail.exclude(
                    pblanc_id__in=data_with_detail.values_list('pblanc_id', flat=True)
                )[:needed_count]
                
                print(f"DEBUG: 추가할 데이터: {additional_data.count()}개")
                
                # 두 데이터셋 합치기 (최신순으로 정렬된 상태에서 100개로 제한)
                data = list(data_with_detail[:100]) + list(additional_data)
                # 최종적으로 100개로 제한
                data = data[:100]
            else:
                data = list(data_with_detail[:100])
        else:
            # detail_region이 없는 경우 기존 로직 사용
            data = BizInfo.objects.filter(
                                            (Q(region__contains=region) | Q(region__contains="전국"))\
                                           & Q(possible_industry__contains=big_industry) \
                                           & Q(revenue__contains=sales)\
                                           & Q(business_period__contains=period) \
                                           & (Q(export_performance__contains=export) | Q(export_performance__contains="무관"))\
                                           ).order_by('-registered_at')[:100]

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

        for i in datas2:
            print(i)

        context = {
            "region": region,
            "detail_region": detail_region,
            "full_region": full_region,
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

    def _build_detail_region_exclude_query(self, region, detail_region):
        """다른 상세지역만 특정되어 있는 경우를 제외하는 쿼리 구성"""
        # regionDetails에 정의된 실제 상세지역 목록
        region_details = {
            "서울": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
            "경기": ["수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시", "동두천시", "안산시", "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시", "용인시", "파주시", "이천시", "안성시", "김포시", "화성시", "광주시", "여주시", "양평군", "고양군", "연천군", "포천군", "가평군", "양주시", "포천시"],
            "인천": ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"],
            "강원": ["춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시", "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"],
            "경북": ["포항시", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시", "경산시", "군위군", "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "예천군", "봉화군", "울진군", "울릉군"],
            "경남": ["창원시", "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시", "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"],
            "부산": ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"],
            "대구": ["중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군"],
            "울산": ["중구", "남구", "동구", "북구", "울주군"],
            "대전": ["중구", "동구", "서구", "유성구", "대덕구"],
            "충북": ["청주시", "충주시", "제천시", "보은군", "옥천군", "영동군", "증평군", "진천군", "괴산군", "음성군", "단양군"],
            "충남": ["천안시", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시", "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"],
            "전북": ["전주시", "군산시", "익산시", "정읍시", "남원시", "김제시", "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"],
            "전남": ["목포시", "여수시", "순천시", "나주시", "광양시", "담양군", "곡성군", "구례군", "고흥군", "보성군", "화순군", "장흥군", "강진군", "해남군", "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"],
            "광주": ["동구", "서구", "남구", "북구", "광산구"],
            "제주": ["제주시", "서귀포시"],
            "세종": ["세종특별자치시"]
        }
        
        # 해당 지역의 상세지역 목록 가져오기
        if region in region_details:
            detail_regions = region_details[region]
            
            # detail_region을 제외한 다른 상세지역들로 쿼리 구성
            other_detail_regions = [dr for dr in detail_regions if dr != detail_region]
            
            # 다른 상세지역이 포함된 데이터를 제외하는 쿼리
            exclude_queries = []
            for other_detail in other_detail_regions:
                exclude_queries.extend([
                    Q(noti_summary__contains=other_detail),
                    Q(hashtag__contains=other_detail),
                    Q(content__contains=other_detail),
                    Q(title__contains=other_detail),
                    Q(region__contains=other_detail)
                ])
            
            # OR 조건으로 결합 (하나라도 포함되면 제외)
            if exclude_queries:
                combined_query = exclude_queries[0]
                for query in exclude_queries[1:]:
                    combined_query |= query
                return combined_query
        
        # 해당 지역의 상세지역 정보가 없으면 빈 쿼리 반환
        return Q()


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
