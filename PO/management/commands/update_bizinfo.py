import os
import tempfile
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from board.models import BizInfo
from PO.management.commands.utils import fetch_iframe_src
from config import BIZINFO_API_KEY, CHROME_DRIVER_PATH, OPEN_AI_API_KEY, NAVER_CLOVA_OCR_API_KEY, NAVER_CLOUD_CLOVA_OCR_API_URL
from langchain_openai import ChatOpenAI
import pdfplumber
import uuid
import json
import time
import shutil
import re
from PIL import Image

class Command(BaseCommand):
    help = "BizInfo API 호출 및 DB 업데이트"

    def handle(self, *args, **kwargs):
        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 5,
            "pageUnit": 5,
            "pageIndex": 1
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            items = data.get("jsonArray", [])

            for item in items:
                pblanc_id = item.get("pblancId")
                if BizInfo.objects.filter(pblanc_id=pblanc_id).exists():
                    continue

                reception_start = datetime.strptime("19000101", "%Y%m%d").date()
                reception_end = datetime.strptime("99991231", "%Y%m%d").date()
                reception_raw = item.get("reqstBeginEndDe")
                if reception_raw and "~" in reception_raw:
                    try:
                        start_str, end_str = reception_raw.split("~")
                        reception_start = datetime.strptime(start_str.strip(), "%Y%m%d").date()
                        reception_end = datetime.strptime(end_str.strip(), "%Y%m%d").date()
                    except:
                        pass

                creatPnttm = item.get("creatPnttm")
                registered_at = (
                    datetime.strptime(creatPnttm, "%Y-%m-%d %H:%M:%S").date()
                    if creatPnttm else None
                )

                iframe_src = fetch_iframe_src(pblanc_id, CHROME_DRIVER_PATH)

                file_url = item.get("flpthNm")
                text, structured_data = "", {}
                if file_url:
                    try:
                        file_path = self.download_file(file_url)
                        text = self.extract_text(file_path)
                        structured_data = self.extract_structured_data(text)
                        os.remove(file_path)
                    except Exception as e:
                        self.stderr.write(f"파일 처리 실패: {file_url} - {e}")

                enroll_method = item.get("reqstMthPapersCn") or "신청 방법은 공고를 참고해주세요."

                employee_count = structured_data.get("직원수") if isinstance(structured_data, dict) else None
                revenue = structured_data.get("매출규모") if isinstance(structured_data, dict) else None

                BizInfo.objects.create(
                    pblanc_id=pblanc_id,
                    title=item.get("pblancNm"),
                    content=item.get("bsnsSumryCn"),
                    registered_at=registered_at,
                    reception_start=reception_start,
                    reception_end=reception_end,
                    institution_name=item.get("jrsdInsttNm"),
                    enroll_method=enroll_method,
                    target=item.get("trgetNm"),
                    field=item.get("pldirSportRealmLclasCodeNm"),
                    hashtag=item.get("hashtags"),
                    print_file_name=item.get("printFileNm"),
                    print_file_path=item.get("printFlpthNm"),
                    company_hall_path=item.get("pblancUrl"),
                    support_field=item.get("pldirSportRealmMlsfcCodeNm"),
                    application_form_name=item.get("fileNm") or "",
                    application_form_path=item.get("flpthNm") or "",
                    iframe_src=iframe_src,
                    extracted_text=text,
                    structured_json=structured_data,
                    employee_count=employee_count,
                    revenue=revenue
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))

    def download_file(self, url):
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        suffix = os.path.splitext(url)[-1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in response.iter_content(1024):
                tmp.write(chunk)
            return tmp.name

    def extract_text(self, file_path):
        if file_path.endswith(".pdf"):
            try:
                with pdfplumber.open(file_path) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                print(f"[PDF 추출 오류] {e}")

        elif file_path.endswith((".png", ".jpg", ".jpeg")):
            return self.ocr_image(file_path)
        
        elif file_path.endswith(".hwp"):
            pdf_path = file_path.replace(".hwp", ".pdf")
            return self.convert_hwp_to_pdf(file_path, pdf_path)
        
        return "오류"

    def ocr_image(self, image_path):
        image_format = os.path.splitext(image_path)[-1][1:]
        request_json = {
            'images': [{'format': image_format, 'name': 'demo'}],
            'requestId': str(uuid.uuid4()),
            'version': 'V1',
            'timestamp': int(time.time() * 1000)
        }
        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        with open(image_path, 'rb') as img_file:
            files = [('file', img_file)]
            headers = {'X-OCR-SECRET': NAVER_CLOVA_OCR_API_KEY}
            response = requests.post(NAVER_CLOUD_CLOVA_OCR_API_URL, headers=headers, data=payload, files=files)
            result = response.json()
            return " ".join([field['inferText'] for field in result['images'][0].get('fields', [])])

    def convert_hwp_to_pdf(self, hwp_path, output_pdf_path):
        txt_path = output_pdf_path.replace(".pdf", ".txt")
        try:
            os.system(f"hwp5txt '{hwp_path}' > '{txt_path}'")
            if os.path.exists(txt_path):
                with open(txt_path, encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"[hwp5txt 오류] 변환 실패: {e}")

        try:
            os.system(f"libreoffice --headless --convert-to pdf '{hwp_path}' --outdir '{os.path.dirname(output_pdf_path)}'")
            converted_path = os.path.join(os.path.dirname(output_pdf_path), os.path.basename(hwp_path).replace(".hwp", ".pdf"))
            if os.path.exists(converted_path):
                return self.extract_text(converted_path)
        except Exception as e:
            print(f"[libreoffice 오류] PDF 변환 실패: {e}")

        return ""

    def extract_structured_data(self, text):
        prompt = (
            "지원사업 공고문 내용에서 다음 항목을 JSON으로 정리해줘\n"
            "이 내용을 기반으로 허구 없이 정확하게 요약해줘. 추가적인 추론이나 가정은 하지 말고, 원문 기반으로만 작성해줘."
            "- 직원수 : 무관, 1~4인, 5인 이상, 매출규모 : 무관, 1억 이하, 1~5억, 5~10억, 10~30억, 30억 이상, 공고내용: 최소 450자 이상, 최대한 자세히 (500자 이상 권장)\n"
            "\n내용:\n" + text
        )
        llm = ChatOpenAI(temperature=0, model_name='gpt-4o-mini', openai_api_key=OPEN_AI_API_KEY)
        try:
            response = llm.invoke(prompt)
            content = response.content.strip().replace("```json", "").replace("```", "")
            return json.loads(content)
        except Exception as e:
            import traceback
            print(f"[GPT 오류] {e}")
            print(traceback.format_exc())
            return {
                "직원수": "오류",
                "매출규모": "오류",
                "공고내용": "오류"
            }

