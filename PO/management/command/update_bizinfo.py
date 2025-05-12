from django.core.management.base import BaseCommand
from main.models import BizInfo
from PO.management.commands.utils import fetch_iframe_src  # 폴더명도 commands로 주의
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
            "searchCnt": 50,
            "pageUnit": 50,
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

                # 접수기간 파싱
                reception = item.get("reqstBeginEndDe", "")
                try:
                    reception_start, reception_end = map(
                        lambda x: datetime.strptime(x.strip(), "%Y%m%d").date(),
                        reception.split("-")
                    )
                except Exception:
                    reception_start = datetime.strptime("19000101", "%Y%m%d").date()
                    reception_end = datetime.strptime("99991231", "%Y%m%d").date()

                # 등록일 파싱
                creatPnttm = item.get("creatPnttm")
                registered_at = (
                    datetime.strptime(creatPnttm, "%Y-%m-%d %H:%M:%S").date()
                    if creatPnttm else None
                )

                # iframe src 추출
                iframe_src = fetch_iframe_src(pblanc_id, CHROME_DRIVER_PATH)

                # DB 저장
                BizInfo.objects.create(
                    pblanc_id=pblanc_id,
                    title=item.get("pblancNm"),
                    content=item.get("bsnsSumryCn"),
                    registered_at=registered_at,
                    reception_start=reception_start,
                    reception_end=reception_end,
                    institution_name=item.get("jrsdInsttNm"),
                    enroll_method=item.get("reqstMthPapersCn"),
                    target=item.get("trgetNm"),
                    field=item.get("pldirSportRealmLclasCodeNm"),
                    hashtag=item.get("hashtags"),
                    print_file_name=item.get("printFileNm"),
                    print_file_path=item.get("printFlpthNm"),
                    company_hall_path=item.get("pblancUrl"),
                    support_field=item.get("pldirSportRealmMlsfcCodeNm"),
                    application_form_name=item.get("fileNm"),
                    application_form_path=item.get("flpthNm"),
                    iframe_src=iframe_src
                )

            self.stdout.write(self.style.SUCCESS(f"{len(items)}건 처리 완료."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"실패: {e}"))
