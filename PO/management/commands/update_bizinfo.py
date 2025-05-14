import os
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
import re
from PIL import Image
import mimetypes
import subprocess

class Command(BaseCommand):
    help = "BizInfo API 호출 및 DB 업데이트"

    def handle(self, *args, **kwargs):
        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 100,
            "pageUnit": 5,
            "pageIndex": 3
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
                file_name = item.get("printFileNm")
                file_path = ""
                text, structured_data = "", {}
                if file_url:
                    try:
                        file_path = self.download_file(file_url, file_name)
                        text = self.extract_text(file_path)
                        print("★★★★★", text, "★★★★★")
                        structured_data = self.extract_structured_data(text)
                        os.remove(file_path)

                    except Exception as e:
                        self.stderr.write(f"파일 처리 실패: {file_path} - {e}")

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
                    employee_count=employee_count,
                    revenue=revenue
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))

    def download_file(self, url, file_name):
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        print(f"📦 Content-Type: {content_type}")

        # 파일 저장 위치: PO/files/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "files"))
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file_name)

        # 실제 저장
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        # 파일 시그니처로 유효성 확인 (예: PDF)
        try:
            with open(save_path, "rb") as f:
                magic = f.read(5)
                if file_name.endswith(".pdf") and magic != b"%PDF-":
                    raise ValueError(f"❌ 파일명은 PDF인데 실제는 PDF가 아닙니다! magic: {magic}")
                if file_name.endswith(".hwp") and magic[:4] != b'HWP\x20':
                    print(f"⚠️ HWP 시그니처도 아님: magic: {magic}")
        except Exception as e:
            print(f"📛 파일 시그니처 확인 실패: {e}")

        print(f"📥 저장 완료 → {save_path}")
        return save_path




    def extract_text(self, file_path):
        if file_path.endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
            print("📂 pdf full_text:", full_text)
            return full_text

        elif file_path.endswith((".jpg", ".jpeg", ".png")):
            full_text = self.clova_ocr(file_path, "jpg")
            print("📂 img full_text:", full_text)
            return full_text
        
        elif file_path.endswith(".hwp"):
            pdf = self.convert_hwp_to_pdf(file_path)
            with pdfplumber.open(pdf) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
            print("📂 hwp full_text:", full_text)
            return full_text
        
        return "오류"
        
    def clova_ocr(file_path, fmt):
        request_json = {
            'images': [{'format': fmt, 'name': 'demo'}],
            'requestId': str(uuid.uuid4()),
            'version': 'V1',
            'timestamp': int(round(time.time() * 1000))
        }
        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [('file', open(file_path, 'rb'))]
        headers = {'X-OCR-SECRET': NAVER_CLOVA_OCR_API_KEY}
        response = requests.post(NAVER_CLOUD_CLOVA_OCR_API_URL, headers=headers, data=payload, files=files)
        
        for field in response.json()['images'][0]['fields']:
            full_text += field['inferText']
        
        return full_text

    def convert_hwp_to_pdf(self, hwp_path):

        # pdf 저장 경로 설정
        output_dir = os.path.dirname(hwp_path)
        pdf_path = hwp_path.replace(".hwp", ".pdf")

        try:
            # libreoffice를 통해 hwp → pdf 변환 시도
            result = subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", hwp_path, "--outdir", output_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20
            )

            if result.returncode != 0:
                print(f"[libreoffice 오류] stdout: {result.stdout.decode()}, stderr: {result.stderr.decode()}")
                return ""

            if not os.path.exists(pdf_path):
                print(f"[❌ 변환 실패] PDF가 생성되지 않았습니다: {pdf_path}")
                return ""

            print(f"✅ HWP → PDF 변환 완료: {pdf_path}")
            return pdf_path

        except Exception as e:
            print(f"[예외 발생] HWP → PDF 변환 실패: {e}")
            return ""

        

    def extract_structured_data(self, text):
        prompt = (
            "아래 텍스트는 정부 지원사업 공고문에서 추출된 실제 내용입니다. "
            "이 내용을 기반으로 허구 없이 정확하게 요약해줘. 추가적인 추론이나 가정은 하지 말고, 원문 기반으로만 작성해줘.\n\n"
            "📌 아래 항목들을 정확히 JSON 형식으로 추출해줘\n"
            "- 직원수 : 무관, 1~4인, 5인 이상 (중 선택, 복수 선택 가능)\n"
            "- 매출규모: 무관, 1억 이하, 1~5억, 5~10억, 10~30억, 30억 이상 (중 선택, 복수 선택 가능)\n"
            "- 공고내용: 최소 450자 이상, 원문 기반 요약\n\n"
        ) + text

        llm = ChatOpenAI(
            temperature=0,
            model_name='gpt-4o-mini',
            openai_api_key=OPEN_AI_API_KEY,
        )
        try:
            response = llm.invoke(prompt)
            content = getattr(response, "content", "").strip()
            print("📦 GPT 응답:", content)
            return self.clean_json_from_response(content)
        except Exception as e:
            print(f"[GPT 오류] {e}")
            return {
                "직원수": "오류",
                "매출규모": "오류",
                "공고내용": "오류"
            }

    def clean_json_from_response(self, content: str) -> dict:
        try:
            match = re.search(r"```(?:json)?\\s*(\{.*?\})\\s*```", content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            match2 = re.search(r"(\{.*?\})", content, re.DOTALL)
            if match2:
                return json.loads(match2.group(1))
            print("⚠️ JSON 블록 추출 실패")
            return {}
        except Exception as e:
            print(f"[JSON 추출/파싱 실패] {e}")
            return {}