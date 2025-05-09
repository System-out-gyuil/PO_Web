from django.shortcuts import render
from django.views import View
from config import BIZINFO_API_KEY
import requests

# Selenium 관련 import
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

        item = None
        iframe_src = None

        # 1. API 요청으로 상세 데이터 가져오기
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
            print("🔴 공고 API 요청 실패:", e)

        # 2. Selenium으로 iframe src 추출
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

            # 최대 10초간 iframe이 DOM에 나타날 때까지 기다림
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )

            iframe_elements = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframe_elements:
                src = iframe.get_attribute("src")
                if src and ("pdf" in src.lower() or "viewer" in src.lower()):
                    iframe_src = src
                    if iframe_src.startswith("/"):
                        iframe_src = "https://www.bizinfo.go.kr" + iframe_src
                    break

            driver.quit()
        except Exception as e:
            print("⚠️ iframe 로딩 실패 또는 없음:", e)
            iframe_src = None

        return render(request, "board/detail.html", {
            "item": item,
            "page_index": page_index,
            "iframe_src": iframe_src
        })
