from django.shortcuts import render
from django.views import View
from config import BIZINFO_API_KEY
import requests


class BoardView(View):
    def get(self, request):
        page_index = int(request.GET.get("page_index", 1))

        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 10,
            "pageUnit": 20,
            "pageIndex": page_index
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = data.get("jsonArray", [])
            total_count = items[0].get("totCnt", 0) if items else 0

            # 다음 페이지 존재 여부
            has_next = (page_index * 10) < total_count

        except requests.exceptions.RequestException as e:
            print("요청 실패:", e)
            items = []
            total_count = 0
            has_next = False

        return render(request, 'board/board.html', {
            "items": items,
            "page_index": page_index,
            "has_next": has_next,
        })

class BoardDetailView(View):
    def get(self, request):
        page_index = request.GET.get("page_index")
        pblanc_id = request.GET.get("id")

        print(page_index)

        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 10,
            "pageUnit": 20,
            "pageIndex": page_index
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = data.get("jsonArray", [])
            item = next((i for i in items if i.get("pblancId") == pblanc_id), None)

        except Exception as e:
            print("상세보기 요청 실패:", e)
            item = None

        return render(request, "board/detail.html", {
            "item": item,
            "page_index": page_index
        })
