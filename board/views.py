from django.shortcuts import render
from django.views import View
from config import BIZINFO_API_KEY
import requests
# 🔽 Selenium 관련 import
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

# chromedriver 위치 (절대경로 권장)
CHROMEDRIVER_PATH = "C:/Users/user/Desktop/po/Code/chromedriver.exe"

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

        # 1. 공고 상세 데이터 가져오기
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

        # 2. Selenium으로 iframe의 src 추출
        iframe_src = None
        try:
            detail_url = f"https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId={pblanc_id}"

            options = webdriver.ChromeOptions()
            options.add_argument('--headless=chrome')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')

            service = Service(executable_path=CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(detail_url)
            time.sleep(1)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # iframe with pdf or viewer in src
            iframe_tags = soup.find_all("iframe")
            pdf_iframes = [iframe for iframe in iframe_tags if "pdf" in iframe.get("src", "").lower() or "viewer" in iframe.get("src", "").lower()]

            if pdf_iframes:
                iframe_src = pdf_iframes[0].get("src")
                # 전체 경로로 조합
                if iframe_src and iframe_src.startswith("/"):
                    iframe_src = "https://www.bizinfo.go.kr" + iframe_src

            driver.quit()
        except Exception as e:
            print("iframe 크롤링 실패:", e)
            iframe_src = None

        return render(request, "board/detail.html", {
            "item": item,
            "page_index": page_index,
            "iframe_src": iframe_src
        })
