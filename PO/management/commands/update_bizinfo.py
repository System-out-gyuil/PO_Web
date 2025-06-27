import os
import re
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from board.models import BizInfo
from main.models import Industry
from PO.management.commands.utils import fetch_iframe_src
from config import BIZINFO_API_KEY, CHROME_DRIVER_PATH, OPEN_AI_API_KEY, NAVER_CLOVA_OCR_API_KEY, NAVER_CLOUD_CLOVA_OCR_API_URL, ES_API_KEY
from langchain_openai import ChatOpenAI
import pdfplumber
import uuid
import json
import time
from PIL import Image
import subprocess
import warnings
warnings.filterwarnings("ignore", category=UserWarning)  # 경고 무시
import pandas as pd
from datetime import date, time, datetime
from django.utils.timezone import make_aware
from po_admin.models import CustUser
from django.db.models import Q
from django.db.models import Max

# 지원사업 정보 업데이트
# 화면구성 X

class Command(BaseCommand):
    help = "DB 업데이트"

    def handle(self, *args, **kwargs):
        self.delete_bizinfo_by_date()

        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 200, # 조회할 전체 개수
            "pageUnit": 200, # 페이지당 개수
            "pageIndex": 1 # 페이지 번호
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

                # MySQL에 저장
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
                    employee_count=structured_data.get("직원수", "test"),
                    revenue=structured_data.get("매출규모", "test"),
                    noti_summary=structured_data.get("공고내용"),
                    business_period=structured_data.get("사업기간(업력)", "test"),
                    region=structured_data.get("지역"),
                    possible_industry=structured_data.get("가능업종"),
                    export_performance=structured_data.get("수출실적여부", "test")
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

            self.update_cust_user_product()

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
        print("===============================================================================================\n 📂 save_path:", save_path)
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
                "※ 빈 값 없이 모든 항목을 채워야 하며.\n"
                "※ 모든 선택지는 반드시 제공된 항목 중에서만 고르고, 원문에 명확히 언급되지 않은 항목은 포함하지 마세요.\n"
                "※ 원문에 기준이 명확하지 않을 경우, '보수적으로 실제 선정 가능성이 높은' 항목만 선택하십시오.\n\n"
                "응답 형식 (반드시 JSON, 빈 값 허용 불가):\n"
                "{\n"
                "  \"지역\": [\"전국\"] 또는 [\"서울\",\"경기\",\"인천\",\"강원\",\"경북\",\"경남\",\"부산\",\"대구\",\"대전\",\"광주\",\"울산\",\"세종\",\"충북\",\"충남\",\"전북\",\"전남\",\"제주\"] 중 원문 근거로 복수 선택],\n"
                "  \"직원수\": [\"직원 없음\", \"1~4인\",\"5인 이상\"] 선택지 중 실제 선정 가능성이 높은 범위를 모두 선택,\n"
                "  \"사업기간(업력)\": [\"사업자 등록 전\",\"3년 미만\",\"3년 이상\"] 선택지 중 선정 가능성이 높은 구간을 복수 선택,\n"
                "  \"매출규모\": [\"매출 없음\", \"1억 이하\",\"1~5억\",\"5~10억\",\"10~30억\",\"30억 이상\"] 선택지 중 선정 가능성이 높은 구간을 복수 선택,\n"
                "  \"수출실적여부\": [\"수출 실적 보유\", \"무관\"] 반드시 예시 중 선정 가능성이 높은 선택지를 하나 선택,\n"
                "  \"공고내용\": \"지원 목적, 대상, 기간, 방법, 자부담, 선정 절차, 지원 한도 및 제한 사항 등을 종합하여 450자 이상으로 정밀하게 요약한 문장\"\n"
                "  \"가능업종\": [\"농업, 임업 및 어업\", \"광업\", \"제조업\", \"전기, 가스, 증기 및 공기 조절 공급업\",\
                      \"수도, 하수 및 폐기물 처리, 원료 재생업\", \"건설업\", \"도매 및 소매업\", \"운수 및 창고업\", \"숙박 및 음식점업\",\
                        \"정보통신업\", \"금융 및 보험업\", \"부동산업\", \"전문, 과학 및 기술 서비스업\", \"사업시설 관리, 사업 지원 및 임대 서비스업\", \
                        \"교육서비스업\", \"보건업 및 사회복지 서비스업\", \"예술 스포츠 및 여가관련 서비스업\", \"협회 및 단체, 수리 및 기타 개인서비스업\"]\
                          선택지 중 공고내용 내 선정 가능한 업종을 명확하게 선택, 복수 선택 가능\n"
                "}\n\n"
                "필수 준수사항:\n"
                "- 모든 키에 반드시 하나 이상의 값을 채워야 하며, 빈 배열 또는 누락은 허용되지 않습니다.\n"
                "- 제공된 선택지 외의 항목은 절대 포함하지 마십시오.\n"
                "- 수출실적여부 외 다른항목에 대해 '무관' 절대 사용하지 마십시오.\n"
                "- 공고 내용을 제외한 모든 항목은 배열의 형태로 출력하시오.\n"
                "- 원문에 직접 근거한 내용만 사용하고, 절대로 추측이나 가정을 하지 마십시오.\n"
                "- 원문에 없는 조건은 '보수적'으로 판단하여 실제 선정 가능성이 높은 기준을 선택하십시오.\n"
            ) + text


        llm = ChatOpenAI(temperature=0, model_name='gpt-4o', openai_api_key=OPEN_AI_API_KEY)
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

    def delete_bizinfo_by_date(self):
        # 오늘 00:00:00 기준 datetime 객체 생성
        today_midnight = datetime.combine(date.today(), time.min)  # ✅ datetime.time.min

        # DB가 timezone-aware인 경우
        today_midnight = make_aware(today_midnight)

        deleted, _ = BizInfo.objects.filter(reception_end__lt=today_midnight).delete()
        print(f"{deleted}개의 마감된 공고가 삭제되었습니다.")
        return deleted

        
    def update_cust_user_product(self):
            cust_users = CustUser.objects.all()
            
            for cust_user in cust_users:
                
                region = cust_user.region
                big_industry = cust_user.industry
                sales = int(cust_user.sales_for_year.replace(",", ""))
                period = cust_user.start_date
                export = cust_user.export_experience
                empl = int(cust_user.employee_count)
                employees = ""

                today = datetime.today()
                year_diff = today.year - period.year
                if today.month < period.month:
                    year_diff -= 1

                if year_diff < 3:
                    period = "3년 미만"
                elif year_diff >= 3:
                    period = "3년 이상"

                if sales >= 3000000000:
                    sales = "30억 이상"
                elif sales >= 1000000000:
                    sales = "10~30억"
                elif sales >= 500000000:
                    sales = "5~10억"
                elif sales > 100000000:
                    sales = "1~5억"
                elif sales <= 100000000:
                    sales = "1억 이하"
                else:
                    sales = "매출없음"

                if empl == 0:
                    employees = "직원 없음"
                elif empl <= 4:
                    employees = "1~4인"
                elif empl <= 9:
                    employees = "5~9인"
                elif empl <= 10:
                    employees = "10인 이상"
                    

                if employees in ["1~4인", "5~9인"] and big_industry in ["광업", "제조업", "건설업", "운수업"] :
                    empl = "소상공인"
                elif employees == "1~4인":
                    empl = "소상공인"
                elif employees in ["10인 이상", "5~9인"]:
                    empl = "중소기업"

                if export == "있음":
                    export = "수출 실적 보유"
                    
                # ------------------- 지원사업 조회 -------------------
                datas = BizInfo.objects.filter(
                    (Q(region__contains=region) | Q(region__contains="전국")) &
                    Q(possible_industry__contains=big_industry) &
                    Q(revenue__contains=sales) &
                    Q(business_period__contains=period) &
                    (Q(export_performance__contains=export) | Q(export_performance__contains="무관")) &
                    Q(target__contains=empl)
                ).order_by('-registered_at')

                # ① pblanc_id를 쉼표로 이어진 문자열로 저장
                pblanc_ids = list(datas.values_list("pblanc_id", flat=True))
                cust_user.possible_product = ",".join(pblanc_ids)

                # ② 최신 registered_at 날짜 구해서 alarm 컬럼에 저장
                latest_date = datas.aggregate(latest=Max('registered_at'))['latest']  # datetime 객체
                # 또는 latest_date = datas.first().registered_at  # 이미 order_by('-registered_at') 했으므로 동일

                if latest_date:
                    # alarm이 CharField라면 문자열로 변환 (예: YYYY-MM-DD)
                    cust_user.alarm = latest_date.strftime('%Y-%m-%d')
                    # alarm이 DateTimeField/DateField라면 그대로 할당해도 됨
                else:
                    cust_user.alarm = ''  # 조회 결과가 없을 때 처리(필요 시)

                cust_user.save()

