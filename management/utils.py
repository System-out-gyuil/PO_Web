from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

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
