from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from board.models import BizInfo
from elasticsearch import Elasticsearch
from config import ES_API_KEY
import math
import ast
from datetime import datetime
from main.models import Count, Count_by_date, IpAddress
from datetime import date

# ✅ Elasticsearch 클라이언트 설정
es = Elasticsearch(
    "https://0e0f4480a93d4cb78455e070163e467d.us-central1.gcp.cloud.es.io:443",
    api_key=ES_API_KEY
)

class BoardView(View):
    def get(self, request):
        page_index = int(request.GET.get("page_index", 1))
        page_size = 10
        select_type = request.GET.get("select-type", "")
        keyword = request.GET.get("keyword", "").strip().lower()

        print(select_type, keyword)

        if select_type and keyword:
            if select_type == "title":
                query = {
                    "wildcard": {
                        "title": f"*{keyword}*"
                    }
                }
            elif select_type == "region":
                query = {
                    "match": {
                        "region": keyword
                    }
                }

        else:
            query = { "match_all": {} }



        # ✅ Elasticsearch 요청
        es_response = es.search(
            index="bizinfo_index",
            body={
                "query": query,
                "sort": [{"registered_at": {"order": "desc"}}],
                "from": (page_index - 1) * page_size,
                "size": page_size
            }
        )

        total_count = es_response['hits']['total']['value']
        hits = es_response['hits']['hits']
        items = [hit["_source"] for hit in hits]

        for item in items:
            item["registered_at"] = datetime.strptime(item["registered_at"], "%Y-%m-%d").strftime("%y.%m.%d")

        # ✅ 페이지네이션 처리
        total_pages = math.ceil(total_count / page_size)
        block_start = ((page_index - 1) // 10) * 10 + 1
        block_end = min(block_start + 9, total_pages)
        page_range = range(block_start, block_end + 1)

        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip = get_client_ip(request)
        today = date.today()

        # ✅ 오늘 이 IP로 기록된 적 있는지 확인
        already_exists = IpAddress.objects.filter(ip_address=ip, created_at__date=today).exists()

        if not already_exists:
            # ✅ 조회수 증가
            count = Count.objects.get(count_type="board")
            count.value += 1
            count.save()

            Count_by_date.objects.create(count_type="board")

            # ✅ 오늘 처음 방문한 IP로 기록
            IpAddress.objects.create(ip_address=ip, count=1)
        else:
            print(f"{ip}는 이미 오늘 방문 기록 있음 (조회수 미증가)")

        return render(request, "board/board.html", {
            "items": items,
            "page_index": page_index,
            "page_range": page_range,
            "total_count": total_count,
            "total_pages": total_pages,
            "is_first_block": block_start == 1,
            "is_last_block": block_end == total_pages,
            "select_type": select_type,
            "keyword": keyword,
        })



class BoardDetailView(View):
    def get(self, request, pblanc_id):
        page_index = request.GET.get("page_index", 1)
        item = get_object_or_404(BizInfo, pblanc_id=pblanc_id)

        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        ip = get_client_ip(request)
        today = date.today()

        # ✅ 오늘 이 IP로 기록된 적 있는지 확인
        already_exists = IpAddress.objects.filter(ip_address=ip, created_at__date=today).exists()

        if not already_exists:
            # ✅ 조회수 증가
            count = Count.objects.get(count_type="board_detail")
            count.value += 1
            count.save()

            Count_by_date.objects.create(count_type="board_detail")

            # ✅ 오늘 처음 방문한 IP로 기록
            IpAddress.objects.create(ip_address=ip, count=1)
        else:
            print(f"{ip}는 이미 오늘 방문 기록 있음 (조회수 미증가)")

        return render(request, "board/detail.html", {
            "item": item,
            "iframe_src": item.iframe_src,
            "page_index": page_index,
        })
