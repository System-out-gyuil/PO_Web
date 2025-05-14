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
from pdf2image import convert_from_path
import mimetypes

class Command(BaseCommand):
    help = "BizInfo API 호출 및 DB 업데이트"

    def handle(self, *args, **kwargs):
        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 100,
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
                file_name = item.get("printFileNm")
                text, structured_data = "", {}
                if file_url:
                    try:
                        file_path = self.download_file(file_url, file_name)
                        text = self.extract_text(file_path)
                        print("★★★★★", text, "★★★★★")
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
                    employee_count=employee_count,
                    revenue=revenue
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))

    def detect_file_extension(self, content_type):
        if "pdf" in content_type:
            return ".pdf"
        elif "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        elif "png" in content_type:
            return ".png"
        elif "hwp" in content_type:
            return ".hwp"
        return ".pdf"

    def download_file(self, url, file_name):
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        extension = self.detect_file_extension(content_type)

        # 확장자 보정
        if not os.path.splitext(file_name)[-1]:
            file_name += extension
        else:
            base, _ = os.path.splitext(file_name)
            file_name = base + extension

        # 저장 경로: PO/files/ (현재 스크립트 기준으로 상위 경로)
        current_dir = os.path.dirname(os.path.abspath(__file__))  # /PO/management/commands/
        save_dir = os.path.join(current_dir, "..", "..", "files")
        save_dir = os.path.abspath(save_dir)
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, file_name)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        if extension == ".pdf":
            with open(save_path, "rb") as f:
                if f.read(5) != b"%PDF-":
                    raise ValueError(f"📛 유효하지 않은 PDF: {url}")

        print(f"📥 저장 완료 → {save_path}")
        return save_path


    def extract_text(self, file_path):
        print("★★★★★", file_path, "★★★★★")

        if file_path.endswith(".pdf"):
            try:
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    if text.strip():
                        return text
                print("⚠️ pdfplumber 실패 → OCR 시도")
                images = convert_from_path(file_path)
                text = ""
                for img in images:
                    tmp_img_path = f"/tmp/{uuid.uuid4()}.png"
                    img.save(tmp_img_path, "PNG")
                    text += self.ocr_image(tmp_img_path) + "\n"
                    os.remove(tmp_img_path)
                return text
            except Exception as e:
                print(f"[PDF 추출 실패] {e}")
                return ""
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
            "아래 텍스트는 정부 지원사업 공고문에서 추출된 실제 내용입니다. "
            "이 내용을 기반으로 허구 없이 정확하게 요약해줘. 추가적인 추론이나 가정은 하지 말고, 원문 기반으로만 작성해줘.\n\n"
            "📌 아래 항목들을 정확히 JSON 형식으로 추출해줘:\n"
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
            print("📦 GPT 원응답:", response)
            content = getattr(response, "content", "").strip()
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