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

class Command(BaseCommand):
    help = "BizInfo API 호출 및 DB 업데이트"

    def handle(self, *args, **kwargs):
        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 100,
            "pageUnit": 20,
            "pageIndex": 3
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
                        text = self.extract_text(file_path)
                        structured_data = self.extract_structured_data(text)
                        print("\n📂 structured_data:", structured_data)
                        os.remove(file_path)
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
        print("📂 save_path:", save_path)
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
        if file_path.endswith(".pdf"):
            if self.is_text_pdf(file_path):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
            else:
                return self.clova_ocr(file_path, "pdf")

        elif file_path.endswith(('.jpg', '.jpeg', '.png')):
            return self.clova_ocr(file_path, "jpg")

        elif file_path.endswith(".hwp"):
            pdf_path = self.convert_hwp_to_pdf(file_path)
            return self.extract_text(pdf_path)

        return full_text.strip() or "오류"

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

            print("📦 libreoffice stdout:", result.stdout.decode())
            print("📛 libreoffice stderr:", result.stderr.decode())

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
        # prompt = (
        #     "아래 텍스트는 정부 지원사업 공고문에서 추출된 실제 내용입니다. "
        #     "이 내용을 기반으로 허구 없이 정확하게 요약해줘. 추가적인 추론이나 가정은 하지 말고, 원문 기반으로만 작성해줘.\n\n"
        #     "※ 매우 중요: 선택 가능한 모든 기준에서 복수 선택이 가능하며, 해당하는 모든 항목을 반드시 포함해야 합니다.\n"
        #     "예를 들어, 사업기간이 3년 이상이면 '3~7년', '7년 이상'을 모두 선택하고, 매출규모가 1억 이상 10억 이하라면 '1~5억', '5~10억'을 모두 포함해야 합니다. 직원수가 1인 이상이라면 '1~4인', '5인 이상' 중 해당하는 모든 항목을 반드시 포함해야 합니다.\n\n"
        #     "만약 모든 항목이 포함된다면 \'무관\' 하나만 넣어줘"
        #     "가능한 예시 중 실제로 선정될 수 있는 정확하고 엄격한 기준으로 선택해줘"
        #     "아래 항목들을 정확히 JSON 형식으로 추출해줘\n"
        #     "- 지역\n"
        #     "- 직원수 : 무관, 1~4인, 5인 이상 (복수 선택 가능, 만약 모두 해당하면 무관)\n"
        #     "- 사업기간(업력): 무관, 예비 창업, 1년 이하, 1~3년, 3~7년, 7년 이상 (해당되는 모든 항목을 복수 선택, 예: 업력이 3년 이상이면 '3~7년', '7년 이상'을 반드시 모두 포함)\n"
        #     "- 매출규모: 무관, 1억 이하, 1~5억, 5~10억, 10~30억, 30억 이상 (해당되는 모든 항목을 복수 선택, 예: 매출이 1억 이상 10억 이하라면 '1~5억', '5~10억'을 반드시 모두 포함)\n"
        #     "- 가능업종: 제조업, 서비스업, 요식업, IT, 도소매, 건설업, 무역업, 운수업, 농수산업, 미디어 (해당되는 모든 항목을 복수 선택)\n"
        #     "- 수출실적여부: 무관, 수출기업, 수출 희망 중 하나 이상 선택 (해당되는 모든 항목을 복수 선택)\n"
        #     "- 공고내용: 최소 450자 이상, 원문 기반 요약\n\n"
        # ) + text
        prompt = (

                "아래 텍스트는 정부 지원사업 공고문에서 추출된 실제 내용입니다. 이 내용을 기반으로 허구 없이 정확하게 요약해줘. 추가적인 추론이나 가정은 하지 말고, 원문에 직접 명시된 내용을 엄격하게 기준으로 작성해줘."

                "※ 매우 중요: 아래 기준들은 실제 공고문에서 명확하게 요구하거나 명시된 조건에 맞춰 정확하고 엄격하게 선정해야 합니다. 각 기준은 해당되는 모든 항목을 복수로 선택할 수 있으며, 원문에서 명시적으로 해당 조건이 나타나지 않으면 아래 방법을 따르세요."

                "1) 원문에서 조건이 명시적으로 나타난 경우:"
                "- 사업기간(업력)이 '최소', '이상' 등으로 표현되면 모든 가능한 범위를 선택 (예: '업력 3년 이상'이면 '3~7년', '7년 이상' 모두 선택)."
                "- 매출규모가 '최소', '이상', '이하' 등으로 표현되었으면 해당 범위 내 모든 매출 구간을 복수 선택."
                "- 직원수가 '이상' 등으로 표현되면 해당되는 모든 직원 수 범위를 선택."

                "2) 원문에서 명확한 기준이 나타나지 않은 경우:"
                "- 지원내용의 난이도, 지원 규모, 모집 기업 수 등을 종합적으로 판단하여 실제로 선정 가능성이 높은 엄격한 기준만 선택."

                "※ 모든 업체가 지원 가능하면 '무관'만 선택합니다."

                "아래 항목들을 정확히 JSON 형식으로 추출해줘:"

                "- 지역: 원문에서 지원 가능 지역을 정확히 선택하고, 제한이 없으면 '무관'."
                "- 직원수: 무관, 1~4인, 5인 이상 중 실제로 선정될 가능성이 높은 엄격한 기준만 선택."
                "- 사업기간(업력): 무관, 예비 창업, 1년 이하, 1~3년, 3~7년, 7년 이상 중 실제로 선정될 가능성이 높은 엄격한 기준만 선택."
                "- 매출규모: 무관, 1억 이하, 1~5억, 5~10억, 10~30억, 30억 이상 중 실제로 선정될 가능성이 높은 엄격한 기준만 선택."
                "- 가능업종: 제조업, 서비스업, 요식업, IT, 도소매, 건설업, 무역업, 운수업, 농수산업, 미디어 중 실제로 선정될 가능성이 높은 엄격한 기준만 선택 (모든 업종 가능 시 '무관')."
                "- 수출실적여부: 무관, 수출기업, 수출 희망 중 실제로 선정될 가능성이 높은 엄격한 기준만 선택."
                "- 공고내용: 반드시 최소 450자 이상으로 원문을 정확히 요약하고, 원문의 주요 선정기준, 지원내용, 지원규모, 신청방법 등을 빠짐없이 상세히 포함합니다"
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
