from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from board.models import BizInfo
import ast
from PO.management.commands.utils import update_count

class BoardView(View):
    def get(self, request):
        page_index = int(request.GET.get("page_index", 1))
        page_size = 10
        select_type = request.GET.get("select-type", "")
        keyword = request.GET.get("keyword", "").strip().lower()

        print(select_type, keyword)

        # ✅ DB 검색 쿼리
        queryset = BizInfo.objects.all()

        if select_type and keyword:
            if select_type == "title":
                queryset = queryset.filter(title__icontains=keyword)
            elif select_type == "region":
                queryset = queryset.filter(region__icontains=keyword)

        queryset = queryset.order_by("-registered_at")

        # ✅ Paginator 적용
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_index)
        items = list(page_obj)

        # ✅ 날짜 및 지역 리스트 포맷 처리
        for item in items:
            item.registered_at = item.registered_at.strftime("%y.%m.%d")

            # region이 문자열 형태의 리스트일 경우 → 실제 리스트로 변환
            if isinstance(item.region, str) and item.region.startswith("["):
                try:
                    item.region = ast.literal_eval(item.region)
                except (SyntaxError, ValueError):
                    item.region = [item.region]  # 파싱 실패 시 그냥 문자열을 리스트로 감쌈

        total_count = paginator.count
        total_pages = paginator.num_pages
        block_start = ((page_index - 1) // 10) * 10 + 1
        block_end = min(block_start + 9, total_pages)
        page_range = range(block_start, block_end + 1)

        update_count(request, "board")

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

        item.hashtag = item.hashtag.split(",")

        update_count(request, "board_detail")

        print(item.iframe_src)

        return render(request, "board/detail.html", {
            "item": item,
            "iframe_src": item.iframe_src,
            "page_index": page_index,
        })
