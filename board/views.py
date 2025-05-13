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

        # views.py

        REGIONS = [
            '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시',
            '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', '전북특별자치도', '전라남도',
            '경상북도', '경상남도', '제주특별자치도', '경북', '경남', '전북', '전남', '인천', '충북', '충남'
        ]

        REGION_MAP = {
            '서울특별시': '서울',
            '부산광역시': '부산',
            '대구광역시': '대구',
            '인천광역시': '인천',
            '광주광역시': '광주',
            '대전광역시': '대전',
            '울산광역시': '울산',
            '세종특별자치시': '세종',
            '경기도': '경기',
            '강원특별자치도': '강원',
            '충청북도': '충북',
            '충청남도': '충남',
            '전북특별자치도': '전북',
            '전라남도': '전남',
            '경상북도': '경북',
            '경상남도': '경남',
            '제주특별자치도': '제주',
        }

        # '경북', '전북' 등 약어도 포함 (이미 약어인 경우를 위해)
        REGION_SHORTS = list(REGION_MAP.values()) + ['경북', '경남', '전북', '전남', '충북', '충남', '인천']

        for item in items:
            # 긴 이름 매핑 먼저 확인
            found = False
            for full, short in REGION_MAP.items():
                if full in item.institution_name:
                    item.region = short
                    found = True
                    break

            if not found:
                # 약어가 institution_name 안에 그대로 포함돼 있다면 그대로 사용
                for short in REGION_SHORTS:
                    if short in item.institution_name:
                        item.region = short
                        found = True
                        break

            if not found:
                item.region = '전국'



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

