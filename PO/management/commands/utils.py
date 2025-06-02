from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from main.models import Count, IpAddress, Count_by_date


def fetch_iframe_src(pblanc_id, chrome_driver_path):
    detail_url = f"https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId={pblanc_id}"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=chrome')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        service = Service(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(detail_url)

        WebDriverWait(driver, 10).until(
            lambda d: any(
                iframe.get_attribute("src") and ("pdf" in iframe.get_attribute("src").lower() or "viewer" in iframe.get_attribute("src").lower())
                for iframe in d.find_elements(By.TAG_NAME, "iframe")
            )
        )

        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            src = iframe.get_attribute("src")
            if src and ("pdf" in src.lower() or "viewer" in src.lower()):
                return src

    except Exception as e:
        print(f"⚠️ iframe 추출 실패({pblanc_id}):", e)
        return None

    finally:
        driver.quit()

def is_bot_request(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    suspicious_keywords = [
        'bot', 'crawl', 'spider', 'python-requests', 'aiohttp',
        'httpclient', 'curl', 'wget', 'scrapy'
    ]
    return any(keyword in ua for keyword in suspicious_keywords)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def update_count(request, count_type):
    ip = get_client_ip(request)
    today = date.today()

    # ✅ 봇이 아닌 경우에만 처리
    if not is_bot_request(request):
        ip_record = IpAddress.objects.filter(ip_address=ip, count_type=count_type).first()

        if not ip_record or ip_record.created_at.date() < today:
            count = Count.objects.get(count_type=count_type)
            count.value += 1
            count.save()

            Count_by_date.objects.create(count_type=count_type)

            if ip_record:
                ip_record.created_at = date.today()
                ip_record.save()
            else:
                IpAddress.objects.create(ip_address=ip, count_type=count_type)