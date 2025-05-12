from django.core.management.base import BaseCommand
from board.models import BizInfo
from PO.management.commands.utils import fetch_iframe_src
import requests
from datetime import datetime
from config import BIZINFO_API_KEY, CHROME_DRIVER_PATH

class Command(BaseCommand):
    help = 'Fetches and stores bizinfo data daily with iframe src'

    def handle(self, *args, **kwargs):
        url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            "crtfcKey": BIZINFO_API_KEY,
            "dataType": "json",
            "searchCnt": 100,
            "pageUnit": 100,
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

                # ✅ 접수기간 파싱 (기본값 먼저 할당해두고 조건 만족하면 덮어쓰기)
                reception_start = datetime.strptime("19000101", "%Y%m%d").date()
                reception_end = datetime.strptime("99991231", "%Y%m%d").date()

                reception_raw = item.get("reqstBeginEndDe")
                if reception_raw and isinstance(reception_raw, str) and "~" in reception_raw:
                    try:
                        start_str, end_str = reception_raw.split("~")
                        reception_start = datetime.strptime(start_str.strip(), "%Y%m%d").date()
                        reception_end = datetime.strptime(end_str.strip(), "%Y%m%d").date()
                    except Exception:
                        pass  # 기본값 유지

                if not item.get("reqstMthPapersCn"):
                    enroll_method = "신청 방법은 공고를 참고해주세요."
                else:
                    enroll_method = item.get("reqstMthPapersCn")

                # ✅ 등록일 파싱
                creatPnttm = item.get("creatPnttm")
                registered_at = (
                    datetime.strptime(creatPnttm, "%Y-%m-%d %H:%M:%S").date()
                    if creatPnttm else None
                )

                # ✅ iframe src 추출
                iframe_src = fetch_iframe_src(pblanc_id, CHROME_DRIVER_PATH)

                # ✅ optional fields: None → 빈 문자열 처리
                application_form_name = item.get("fileNm") or ""
                application_form_path = item.get("flpthNm") or ""

                # ✅ DB 저장
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
                    application_form_name=application_form_name,
                    application_form_path=application_form_path,
                    iframe_src=iframe_src
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))
