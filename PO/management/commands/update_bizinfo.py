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
from diary.models import Attribute, AttributeValue

# 지원사업 정보 업데이트
# 화면구성 X

class Command(BaseCommand):
    help = "DB 업데이트"

    def handle(self, *args, **kwargs):
        # LibreOffice 상태 확인
        if not self.check_libreoffice_status():
            self.stderr.write(self.style.ERROR("LibreOffice가 설치되지 않았거나 실행할 수 없습니다."))
            return
            
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
            response = requests.get(url, params=params, timeout=60)
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
            
            # diary 추천 지원사업 자동 업데이트
            self.update_diary_recommendations()

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))

    

    def sanitize_filename(self, name):
        return re.sub(r"[^\w가-힣._]+", "_", name).strip("_")

    def download_file(self, url, file_name):
        response = requests.get(url, stream=True, timeout=60)
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

    def check_libreoffice_status(self):
        """LibreOffice 설치 상태와 버전을 확인합니다."""
        try:
            result = subprocess.run([
                "libreoffice", "--version"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            
            if result.returncode == 0:
                version = result.stdout.decode().strip()
                print(f"✅ LibreOffice 설치 확인: {version}")
                return True
            else:
                print(f"❌ LibreOffice 실행 실패: {result.stderr.decode()}")
                return False
        except Exception as e:
            print(f"❌ LibreOffice 확인 실패: {e}")
            return False

    def convert_hwp_to_pdf(self, hwp_path):
        output_dir = os.path.dirname(hwp_path)
        try:
            # 파일 크기 확인
            file_size = os.path.getsize(hwp_path)
            print(f"📄 HWP 파일 크기: {file_size / (1024*1024):.2f} MB")
            
            # 파일 크기에 따른 timeout 조정
            if file_size > 50 * 1024 * 1024:  # 50MB 이상
                timeout = 1800  # 30분
                print("⏰ 대용량 파일 감지, timeout을 30분으로 설정")
            elif file_size > 10 * 1024 * 1024:  # 10MB 이상
                timeout = 900   # 15분
                print("⏰ 중간 크기 파일 감지, timeout을 15분으로 설정")
            else:
                timeout = 600   # 10분 (기본값)
                print("⏰ 기본 timeout 10분 설정")
            
            # LibreOffice 프로세스 시작 전 메모리 상태 확인
            print("🖥️ LibreOffice 변환 시작...")
            
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "pdf:writer_pdf_Export",
                hwp_path,
                "--outdir", output_dir
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)

            print("🖥️ libreoffice stdout:", result.stdout.decode())
            if result.stderr:
                print("🖥️ libreoffice stderr:", result.stderr.decode())

            basename = os.path.splitext(os.path.basename(hwp_path))[0] + ".pdf"
            converted_pdf = os.path.join(output_dir, basename)

            if os.path.exists(converted_pdf):
                pdf_size = os.path.getsize(converted_pdf)
                print(f"✅ 변환 성공: {pdf_size / (1024*1024):.2f} MB")
                return converted_pdf
            else:
                print(f"[❌ 변환 실패] {converted_pdf} 파일이 존재하지 않습니다.")
                return ""
                
        except subprocess.TimeoutExpired:
            print(f"[⏰ Timeout 발생] {timeout}초 초과로 변환 실패")
            # LibreOffice 프로세스 강제 종료
            try:
                subprocess.run(["pkill", "-f", "libreoffice"], timeout=10)
                print("🔄 LibreOffice 프로세스 강제 종료 완료")
            except:
                print("⚠️ LibreOffice 프로세스 종료 실패")
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
        from datetime import time as dt_time  # time 모듈과 구분하기 위해 별칭 사용
        today_midnight = datetime.combine(date.today(), dt_time.min)  # ✅ dt_time.min 사용

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
                
                # sales_for_year 변환 시 에러 처리 추가
                try:
                    sales = int(cust_user.sales_for_year.replace(",", ""))
                except (ValueError, AttributeError):
                    # 숫자가 아닌 값이 저장된 경우 기본값 설정
                    print(f"⚠️ 사용자 {cust_user.id}의 sales_for_year 값이 숫자가 아닙니다: {cust_user.sales_for_year}")
                    sales = 0  # 기본값으로 0 설정
                
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

    def update_diary_recommendations(self):
        """
        모든 diary 행의 데이터를 조회하여 각 행마다 해당하는 공고를 지원사업 속성에 자동으로 추가
        """
        from diary.models import User, Row, Attribute, AttributeValue, AttributeType
        
        print("=== diary 추천 지원사업 자동 업데이트 시작 ===")
        
        # 모든 사용자 조회
        users = User.objects.all()
        total_updated = 0
        
        for user in users:
            print(f"사용자 {user.id} ({user.name}) 처리 중...")
            
            # 사용자의 모든 행 조회
            rows = Row.objects.filter(user=user)
            
            for row in rows:
                try:
                    # 행의 속성 값들 가져오기
                    biz_region = self._get_attribute_value(user, row, '지역')
                    biz_region_detail = self._get_attribute_value(user, row, '상세지역')
                    biz_industry = self._get_attribute_value(user, row, '업종')
                    biz_revenue = self._get_attribute_value(user, row, '매출')
                    biz_business_months = self._get_attribute_value(user, row, '개업년월')
                    biz_employees = self._get_attribute_value(user, row, '직원수')
                    
                    # 매출액 카테고리 분류
                    if biz_revenue:
                        revenue_num = self._parse_number(biz_revenue, 0)
                        if revenue_num == 0:
                            biz_revenue = "매출 없음"
                        elif revenue_num <= 100000000:
                            biz_revenue = "1억 이하"
                        elif revenue_num <= 500000000:
                            biz_revenue = "1~5억"
                        elif revenue_num <= 1000000000:
                            biz_revenue = "5~10억"
                        elif revenue_num <= 3000000000:
                            biz_revenue = "10~30억"
                        else:
                            biz_revenue = "30억 이상"
                    else:
                        biz_revenue = "무관"
                    
                    # 업력 계산
                    if biz_business_months:
                        months = self._calculate_business_months(biz_business_months)
                        if months == 0:
                            biz_business_months = "사업자 등록 전"
                        elif months < 36:
                            biz_business_months = "3년 미만"
                        else:
                            biz_business_months = "3년 이상"
                    else:
                        biz_business_months = "무관"
                    
                    # 직원수 카테고리
                    if biz_employees:
                        emp_num = self._parse_number(biz_employees, 0)
                        if emp_num == 0:
                            biz_employees = "직원 없음"
                        elif emp_num <= 4:
                            biz_employees = "1~4인"
                        else:
                            biz_employees = "5인 이상"
                        
                        # 업종별 직원수 분류
                        if biz_employees in ["1~4인", "5~9인"] and biz_industry in ["광업", "제조업", "건설업", "운수업"]:
                            biz_employees = "소상공인"
                        elif biz_employees == "1~4인":
                            biz_employees = "소상공인"
                        elif biz_employees in ["10인 이상", "5~9인"]:
                            biz_employees = "중소기업"
                    else:
                        biz_employees = "무관"
                    
                    # 업종이 없으면 무관으로 설정
                    if not biz_industry:
                        biz_industry = "무관"
                    
                    print(f"  행 {row.id}: 지역={biz_region}, 업종={biz_industry}, 매출={biz_revenue}, 업력={biz_business_months}, 직원수={biz_employees}")
                    
                    # BizInfo에서 해당하는 공고 조회
                    if biz_region:
                        # 상세지역이 정확히 포함된 데이터만 검색
                        data_with_detail = BizInfo.objects.filter(
                            (Q(region__contains=biz_region) | Q(region__contains="전국") | Q(hashtag__contains=biz_region)) &
                            (Q(possible_industry__contains=biz_industry) | Q(possible_industry__contains='무관')) &
                            (Q(revenue__contains=biz_revenue) | Q(revenue__contains='무관')) &
                            (Q(business_period__contains=biz_business_months) | Q(business_period__contains='무관')) &
                            (Q(target__contains=biz_employees) | Q(target__contains='무관')) &
                            (
                                # 상세지역이 포함된 경우만
                                Q(noti_summary__contains=biz_region_detail) | 
                                Q(hashtag__contains=biz_region_detail) | 
                                Q(content__contains=biz_region_detail) | 
                                Q(title__contains=biz_region_detail) |
                                Q(region__contains=biz_region_detail)
                            )
                        )
                        
                        # 상세지역이 포함된 데이터가 10개 미만인 경우, 포함되지 않은 데이터도 추가
                        if data_with_detail.count() < 10:
                            needed_count = 10 - data_with_detail.count()
                            additional_data = BizInfo.objects.filter(
                                (Q(region__contains=biz_region) | Q(region__contains="전국") | Q(hashtag__contains=biz_region)) &
                                (Q(possible_industry__contains=biz_industry) | Q(possible_industry__contains='무관')) &
                                (Q(revenue__contains=biz_revenue) | Q(revenue__contains='무관')) &
                                (Q(business_period__contains=biz_business_months) | Q(business_period__contains='무관')) &
                                (Q(target__contains=biz_employees) | Q(target__contains='무관'))
                            ).exclude(
                                # detail_region이 포함된 데이터 제외
                                Q(noti_summary__contains=biz_region_detail) | 
                                Q(hashtag__contains=biz_region_detail) | 
                                Q(content__contains=biz_region_detail) | 
                                Q(title__contains=biz_region_detail) |
                                Q(region__contains=biz_region_detail)
                            )[:needed_count]
                            
                            # 두 결과를 합치고 중복 제거
                            combined_data = list(data_with_detail) + list(additional_data)
                            # pblanc_id 기준으로 중복 제거
                            seen_ids = set()
                            unique_data = []
                            for item in combined_data:
                                if item.pblanc_id not in seen_ids:
                                    seen_ids.add(item.pblanc_id)
                                    unique_data.append(item)
                            
                            final_data = unique_data[:10]
                        else:
                            final_data = list(data_with_detail[:10])
                    else:
                        # 지역이 없는 경우 기본 조건으로만 검색
                        final_data = list(BizInfo.objects.filter(
                            (Q(possible_industry__contains=biz_industry) | Q(possible_industry__contains='무관')) &
                            (Q(revenue__contains=biz_revenue) | Q(revenue__contains='무관')) &
                            (Q(business_period__contains=biz_business_months) | Q(business_period__contains='무관')) &
                            (Q(target__contains=biz_employees) | Q(target__contains='무관'))
                        )[:10])
                    
                    # pblanc_id 목록 생성
                    pblanc_ids = [biz.pblanc_id for biz in final_data]
                    pblanc_ids_str = ','.join(pblanc_ids)

                    print(f"    추천된 공고 수: {len(final_data)}개")
                    print(f"    pblanc_ids: {pblanc_ids_str}")

                    # 지원사업 속성 찾기 (없으면 생성)
                    try:
                        recommend_attr = Attribute.objects.get(name='지원사업', user=user)
                    except Attribute.DoesNotExist:
                        # recommend_biz 타입의 AttributeType 가져오기 또는 생성
                        recommend_biz_type, _ = AttributeType.objects.get_or_create(name='recommend_biz')
                        recommend_attr = Attribute.objects.create(
                            name='지원사업',
                            attributeType=recommend_biz_type,
                            user=user
                        )
                        print(f"    새로운 '지원사업' 속성 생성: {recommend_attr.id}")

                    # 기존 값 가져오기
                    existing_value = None
                    try:
                        attr_value = AttributeValue.objects.get(attribute=recommend_attr, row=row)
                        existing_value = attr_value.value
                    except AttributeValue.DoesNotExist:
                        pass

                    # dict 형태로 데이터 구성
                    support_data = {
                        'pblanc_ids': pblanc_ids,  # 항상 전체 추천 공고 ID 저장
                        '알림': []
                    }

                    # 기존 값이 있으면 기존 pblanc_ids와 비교하여 새로 추가된 것들 찾기
                    if existing_value:
                        try:
                            if isinstance(existing_value, str):
                                # 기존에 문자열로 저장된 경우 JSON으로 파싱 시도
                                import json
                                existing_data = json.loads(existing_value)
                            else:
                                existing_data = existing_value
                            
                            if isinstance(existing_data, dict) and 'pblanc_ids' in existing_data:
                                existing_ids = existing_data.get('pblanc_ids', [])
                                if isinstance(existing_ids, str):
                                    existing_ids = [id.strip() for id in existing_ids.split(',') if id.strip()]
                                
                                # 새로 추가된 공고 ID들 찾기
                                new_ids = [id for id in pblanc_ids if id not in existing_ids]
                                if new_ids:
                                    support_data['알림'] = new_ids  # 새로 추가된 것들만 알림에
                                    print(f"    새로 추가된 공고: {new_ids}")
                            else:
                                # 기존 데이터가 잘못된 형태인 경우, 모든 공고를 알림으로 설정
                                support_data['알림'] = pblanc_ids
                                print(f"    기존 데이터 형태 오류, 모든 공고를 알림으로 설정: {pblanc_ids}")
                        except Exception as e:
                            print(f"    기존 값 파싱 오류: {e}")
                            # 기존 값이 잘못된 형태인 경우, 모든 공고를 알림으로 설정
                            support_data['알림'] = pblanc_ids
                            print(f"    파싱 오류로 모든 공고를 알림으로 설정: {pblanc_ids}")
                    else:
                        # 첫 번째 실행인 경우, 모든 공고를 알림으로 설정
                        if len(pblanc_ids) > 0:
                            support_data['알림'] = pblanc_ids
                            print(f"    첫 번째 실행 - 모든 공고를 알림으로 설정: {pblanc_ids}")

                    print(f"    최종 support_data: {support_data}")
                    
                    # AttributeValue 업데이트 또는 생성
                    try:
                        attr_value = AttributeValue.objects.get(attribute=recommend_attr, row=row)
                        attr_value.value = support_data
                        attr_value.save()
                        print(f"    기존 AttributeValue 업데이트: {attr_value.id}")
                    except AttributeValue.DoesNotExist:
                        new_attr_value = AttributeValue.objects.create(
                            attribute=recommend_attr,
                            row=row,
                            value=support_data
                        )
                        print(f"    새로운 AttributeValue 생성: {new_attr_value.id}")
                    
                    total_updated += 1
                    
                except Exception as e:
                    print(f"    행 {row.id} 처리 중 오류 발생: {e}")
                    continue
        
        print(f"=== diary 추천 지원사업 자동 업데이트 완료 ===")
        print(f"총 {total_updated}개 행이 업데이트되었습니다.")
        return total_updated
    
    def _get_attribute_value(self, user, row, attribute_name):
        """속성 값을 가져오는 헬퍼 함수"""
        try:
            attribute = Attribute.objects.get(user=user, name=attribute_name)
            attr_value = AttributeValue.objects.filter(row=row, attribute=attribute).first()
            return attr_value.value if attr_value else None
        except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
            return None
    
    def _parse_number(self, value, default=0):
        """문자열이나 숫자를 정수로 변환하는 헬퍼 함수"""
        if value is None:
            return default
        
        if isinstance(value, (int, float)):
            return int(value)
        
        if isinstance(value, str):
            # 숫자가 아닌 문자 제거 후 변환
            numbers_only = re.sub(r'[^\d.]', '', value)
            try:
                return int(float(numbers_only)) if numbers_only else default
            except ValueError:
                return default
        
        return default
    
    def _calculate_business_months(self, opening_date_str):
        """개업년월로부터 업력(개월수) 계산하는 헬퍼 함수"""
        if not opening_date_str:
            return 12  # 기본값
        
        try:
            # 다양한 날짜 형식 처리
            if isinstance(opening_date_str, str):
                # YYYY-MM-DD 형식
                if '-' in opening_date_str and len(opening_date_str) >= 7:
                    opening_date = datetime.strptime(opening_date_str[:7], '%Y-%m')
                # YYYY년 MM월 형식
                elif '년' in opening_date_str and '월' in opening_date_str:
                    # 예: "2023년 5월"
                    match = re.search(r'(\d{4})년\s*(\d{1,2})월', opening_date_str)
                    if match:
                        year, month = int(match.group(1)), int(match.group(2))
                        opening_date = datetime(year, month, 1)
                    else:
                        return 12
                else:
                    return 12
            
            # 현재 날짜와의 차이 계산
            now = datetime.now()
            months_diff = (now.year - opening_date.year) * 12 + (now.month - opening_date.month)
            return max(1, months_diff)  # 최소 1개월
            
        except (ValueError, AttributeError):
            return 12  # 파싱 실패 시 기본값

