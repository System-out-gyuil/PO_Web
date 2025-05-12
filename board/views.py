from django.shortcuts import render, get_object_or_404
from django.views import View
from board.models import BizInfo
import math

class BoardView(View):
    def get(self, request):
        page_index = int(request.GET.get("page_index", 1))
        page_size = 10

        all_items = BizInfo.objects.order_by("-registered_at")
        total_count = all_items.count()
        total_pages = math.ceil(total_count / page_size)

        start = (page_index - 1) * page_size
        end = start + page_size
        items = all_items[start:end]

        has_next = page_index < total_pages

        # 페이징 블록 계산
        page_block = 10
        block_start = ((page_index - 1) // page_block) * page_block + 1
        block_end = min(block_start + page_block - 1, total_pages)
        page_range = range(block_start, block_end + 1)

        is_first_block = block_start == 1
        is_last_block = block_end == total_pages

        return render(request, 'board/board.html', {
            "items": items,
            "page_index": page_index,
            "has_next": has_next,
            "page_range": page_range,
            "total_count": total_count,
            "total_pages": total_pages,
            "is_first_block": is_first_block,
            "is_last_block": is_last_block,
        })


class BoardDetailView(View):
    def get(self, request, pblanc_id):  # ✅ URL 경로에서 직접 받음
        page_index = request.GET.get("page_index", 1)
        item = get_object_or_404(BizInfo, pblanc_id=pblanc_id)

        return render(request, "board/detail.html", {
        "item": item,
        "iframe_src": item.iframe_src,
        "page_index": page_index,
        "request": request
    })

