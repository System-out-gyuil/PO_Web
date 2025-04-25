from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from elasticsearch import Elasticsearch
from datetime import datetime
import json

class MainView(View):
    def get(self, request):
        return render(request, 'main/main.html')

    def post(self, request):
        region = request.POST.get('region')
        industry = request.POST.get('industry')
        print(region, industry)

        # Elasticsearch 연결
        es = Elasticsearch("http://localhost:9200", verify_certs=False)
        index_name = "support_projects"

        # 검색 함수
        def search_support_projects(region: str, industry: str, sample_size: int = 20):
            query = {
                "query": {
                    "bool": {
                        "must": [
                            { "match": { "가능업종": industry } }
                        ],
                        "should": [
                            { "match_phrase": { "지역": region } },
                            { "wildcard": { "지역": f"*{region}*" } },
                            { "match_phrase": { "공고내용": region } },
                            { "wildcard": { "공고내용": f"*{region}*" } }
                        ],
                        "minimum_should_match": 1
                    }
                }
            }

            res = es.search(index=index_name, body=query, size=sample_size)

            return [hit["_source"] for hit in res["hits"]["hits"]]

        # 날짜 유효성 검사
        def is_valid_date_range(start_date: str, end_date: str) -> bool:
            try:
                today = datetime.today().date()
                if not end_date or end_date == "9999-12-31":
                    return True
                return datetime.strptime(end_date, "%Y-%m-%d").date() >= today
            except:
                return False

        # 날짜 포맷
        def format_date_range(start: str, end: str) -> str:
            if not end or end == "9999-12-31":
                return "사업비 소진 시까지 (상시접수)"
            if not start or start == "1111-12-31":
                return f"~ {end}"
            return f"{start} ~ {end}"

        # 정렬 기준: 모집 종료일이 빠른 순 (상시모집은 맨 뒤)
        def sort_key(project):
            try:
                end_date = project.get("모집기간", {}).get("모집종료일", "")
                if end_date == "9999-12-31":
                    return datetime.max
                return datetime.strptime(end_date, "%Y-%m-%d")
            except:
                return datetime.max

        # 문서 검색 및 정렬
        matched_projects = sorted(search_support_projects(region, industry), key=sort_key)

        return render(request, 'main/main.html', {'projects': matched_projects})

