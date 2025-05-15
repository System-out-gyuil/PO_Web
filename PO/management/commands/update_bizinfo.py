import os
import re
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
from PIL import Image
import subprocess
import warnings
warnings.filterwarnings("ignore")  # 경고 무시

class Command(BaseCommand):
    help = "BizInfo API 호출 및 DB 업데이트"

    def handle(self, *args, **kwargs):
        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 200,
            "pageUnit": 20,
            "pageIndex": 7
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            items = response.json().get("jsonArray", [])

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
                registered_at = datetime.strptime(creatPnttm, "%Y-%m-%d %H:%M:%S").date() if creatPnttm else None
                iframe_src = fetch_iframe_src(pblanc_id, CHROME_DRIVER_PATH)

                file_url = item.get("printFlpthNm")
                raw_file_name = item.get("printFileNm") or "default.pdf"
                file_name = self.sanitize_filename(raw_file_name)
                text, structured_data = "", {}
                if file_url:
                    try:
                        file_path = self.download_file(file_url, file_name)
                        text, extra_path = self.extract_text(file_path)
                        structured_data = self.extract_structured_data(text)
                        print("\n📄 structured_data:", structured_data)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        if extra_path and os.path.exists(extra_path):
                            os.remove(extra_path)
                    except Exception as e:
                        self.stderr.write(f"파일 처리 실패: {file_url} - {e}")

                BizInfo.objects.create(
                    pblanc_id=pblanc_id,
                    title=item.get("pblancNm"),
                    content=item.get("bsnsSumryCn"),
                    registered_at=registered_at,
                    reception_start=reception_start,
                    reception_end=reception_end,
                    institution_name=item.get("jrsdInsttNm"),
                    enroll_method=item.get("reqstMthPapersCn") or "신청 방법은 공고를 참고해주세요.",
                    target=item.get("trgetNm"),
                    field=item.get("pldirSportRealmLclasCodeNm"),
                    hashtag=item.get("hashtags"),
                    print_file_name=raw_file_name,
                    print_file_path=item.get("printFlpthNm"),
                    company_hall_path=item.get("pblancUrl"),
                    support_field=item.get("pldirSportRealmMlsfcCodeNm"),
                    application_form_name=item.get("fileNm") or "",
                    application_form_path=item.get("flpthNm") or "",
                    iframe_src=iframe_src,
                    employee_count=structured_data.get("직원수"),
                    revenue=structured_data.get("매출규모"),
                    noti_summary=structured_data.get("공고내용"),
                    business_period=structured_data.get("사업기간(업력)"),
                    region=structured_data.get("지역"),
                    possible_industry=structured_data.get("가능업종"),
                    export_performance=structured_data.get("수출실적여부")
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))

    def sanitize_filename(self, name):
        return re.sub(r"[^\w가-힣._]+", "_", name).strip("_")

    def download_file(self, url, file_name):
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "files"))
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file_name)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("==========================================================\n 📂 save_path:", save_path)
        return save_path

    def is_text_pdf(self, file_path):
        try:

            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:2]:
                    if page.extract_text():
                        return True
            return False
        except:
            return False

    def extract_text(self, file_path):
        full_text = ""
        extra_path = None

        if file_path.endswith(".pdf"):
            if self.is_text_pdf(file_path):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                return full_text.strip(), None
            else:
                return self.clova_ocr(file_path, "pdf"), None

        elif file_path.endswith((".jpg", ".jpeg", ".png")):
            return self.clova_ocr(file_path, "jpg"), None

        elif file_path.endswith(".hwp"):
            pdf_path = self.convert_hwp_to_pdf(file_path)
            if os.path.exists(pdf_path):
                extra_path = pdf_path
                extracted_text, _ = self.extract_text(pdf_path)
                return extracted_text, extra_path
            else:
                return "오류", None

        return full_text.strip() or "오류", None

    def clova_ocr(self, file_path, fmt):
        request_json = {
            'images': [{'format': fmt, 'name': 'demo'}],
            'requestId': str(uuid.uuid4()),
            'version': 'V1',
            'timestamp': int(time.time() * 1000)
        }
        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [('file', open(file_path, 'rb'))]
        headers = {'X-OCR-SECRET': NAVER_CLOVA_OCR_API_KEY}
        response = requests.post(NAVER_CLOUD_CLOVA_OCR_API_URL, headers=headers, data=payload, files=files)

        full_text = ""
        for field in response.json()['images'][0].get('fields', []):
            full_text += field['inferText'] + " "
        return full_text.strip()

    def convert_hwp_to_pdf(self, hwp_path):
        output_dir = os.path.dirname(hwp_path)
        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "pdf:writer_pdf_Export",
                hwp_path,
                "--outdir", output_dir
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

            print("🖥️ libreoffice stdout:", result.stdout.decode())

            basename = os.path.splitext(os.path.basename(hwp_path))[0] + ".pdf"
            converted_pdf = os.path.join(output_dir, basename)

            if os.path.exists(converted_pdf):
                return converted_pdf
            else:
                print(f"[❌ 변환 실패] {converted_pdf} 파일이 존재하지 않습니다.")
                return ""
        except Exception as e:
            print(f"[예외 발생] HWP → PDF 변환 실패: {e}")
            return ""

    def extract_structured_data(self, text):
        prompt = (
                "아래 텍스트는 정부 지원사업 공고문에서 추출된 실제 내용입니다.\n"
                "이 내용을 기반으로 **원문에 명시된 내용만으로 엄격히 판단하여**, **절대로 추측이나 가정을 하지 마세요.**\n"
                "※ 빈 값 없이 모든 항목을 채워야 하며, '무관'은 절대 사용하지 마십시오.\n"
                "※ 모든 선택지는 반드시 제공된 항목 중에서만 고르고, 원문에 명확히 언급되지 않은 항목은 포함하지 마세요.\n"
                "※ 원문에 기준이 명확하지 않을 경우, '보수적으로 실제 선정 가능성이 높은' 항목만 선택하십시오.\n\n"
                "응답 형식 (반드시 JSON, 빈 값 허용 불가):\n"
                "{\n"
                "  \"지역\": [\"전국\" 또는 [\"서울\",\"경기\",\"인천\",\"강원\",\"경북\",\"경남\",\"부산\",\"대구\",\"대전\",\"광주\",\"울산\",\"세종\",\"충북\",\"충남\",\"전북\",\"전남\",\"제주\"] 중 원문 근거로 복수 선택],\n"
                "  \"직원수\": [\"직원 없음\", \"1~4인\",\"5인 이상\" 중 실제 선정 가능성이 높은 범위를 모두 선택],\n"
                "  \"사업기간(업력)\": [\"사업자 등록 전\",\"1년 이하\",\"1~3년\",\"3~7년\",\"7년 이상\" 중 지원 가능성이 높은 구간을 복수 선택,\n"
                "  \"매출규모\": [\"1억 이하\",\"1~5억\",\"5~10억\",\"10~30억\",\"30억 이상\" 중 지원 가능성이 높은 구간을 복수 선택],\n"
                "  \"가능업종\": [\"제조업\",\"서비스업\",\"요식업\",\"IT\",\"도소매\",\"건설업\",\"무역업\",\"운수업\",\"농수산업\",\"미디어\" 중 원문에서 명확히 지원 대상에 해당하는 업종 복수 선택],\n"
                "  \"수출실적여부\": [\"수출 기업\",\"수출 희망\", \"수출 없음\" 중 원문에서 실제 언급된 것만 선택],\n"
                "  \"공고내용\": \"지원 목적, 대상, 기간, 방법, 자부담, 선정 절차, 지원 한도 및 제한 사항 등을 종합하여 450자 이상으로 정밀하게 요약한 문장\"\n"
                "}\n\n"
                "필수 준수사항:\n"
                "- 모든 키에 반드시 하나 이상의 값을 채워야 하며, 빈 배열 또는 누락은 허용되지 않습니다.\n"
                "- 제공된 선택지 외의 항목은 절대 포함하지 마십시오.\n"
                "- 원문에 직접 근거한 내용만 사용하고, 절대로 추측이나 가정을 하지 마십시오.\n"
                "- 원문에 없는 조건은 '보수적'으로 판단하여 실제 선정 가능성이 높은 기준을 선택하십시오.\n"
            ) + text


        llm = ChatOpenAI(temperature=0, model_name='gpt-4o-mini', openai_api_key=OPEN_AI_API_KEY)
        try:
            response = llm.invoke(prompt)
            return self.clean_json_from_response(getattr(response, "content", "").strip())
        except Exception as e:
            print(f"[GPT 오류] {e}")
            return {"직원수": "오류", "매출규모": "오류", "공고내용": "오류"}

    def clean_json_from_response(self, content: str) -> dict:
        try:
            match = re.search(r"```(?:json)?\\s*(\{.*?\})\\s*```", content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            match2 = re.search(r"(\{.*?\})", content, re.DOTALL)
            if match2:
                return json.loads(match2.group(1))
            print("⚠️ JSON 블록 추출 실패")
            print("📄 원본 content:", content)
            return {}
        except Exception as e:
            print(f"[JSON 파싱 오류] {e}")
            return {}
