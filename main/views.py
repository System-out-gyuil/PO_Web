from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from elasticsearch import Elasticsearch
from datetime import datetime
import json  # 🔥 추가
from .config import ES_API_KEY

class MainView(View):
    def get(self, request):
        return render(request, 'main/main.html')

    def post(self, request):
        region = request.POST.get('region')
        industry = request.POST.get('industry')

        if region and industry:
            return redirect(f'/search/?region={region}&industry={industry}')
        else:
            return render(request, 'main/main.html')


class SearchResultView(View):
    def get(self, request):
        region = request.GET.get('region')
        industry = request.GET.get('industry')

        if not (region and industry):
            return redirect('main')

        es = Elasticsearch("https://0e0f4480a93d4cb78455e070163e467d.us-central1.gcp.cloud.es.io:443", api_key=ES_API_KEY)
        index_name = "po_index"

        def search_support_projects(region: str, industry: str, sample_size: int = 1000):
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

        def sort_key(project):
            try:
                end_date = project.get("모집기간", {}).get("모집종료일", "")
                if end_date == "9999-12-31":
                    return datetime.max
                return datetime.strptime(end_date, "%Y-%m-%d")
            except:
                return datetime.max

        matched_projects = sorted(search_support_projects(region, industry), key=sort_key)

        # 🔥 지원규모가 dict처럼 생긴 문자열이면 파싱하기
        for project in matched_projects:
            규모 = project.get('지원규모')
            if isinstance(규모, str):
                try:
                    parsed = json.loads(규모.replace("'", '"'))  # 홑따옴표 -> 쌍따옴표로 바꿔서 파싱
                    if isinstance(parsed, dict):
                        project['지원규모'] = parsed
                except json.JSONDecodeError:
                    pass  # 실패하면 그냥 문자열 유지

        paginator = Paginator(matched_projects, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'main/search_results.html', {
            'projects': page_obj,
            'region': region,
            'industry': industry,
        })
