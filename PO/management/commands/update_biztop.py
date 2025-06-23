# PO/management/commands/update_biztop.py
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import BizTop
import requests, math
from config import BIZINFO_API_KEY

# ──────────────────────────────────────────────────────────────────────────────
WEEKDAY_SCORE = 1.0      # 월~금
WEEKEND_SCORE = 0.2      # 토·일
API_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
API_PARAMS = {
    "crtfcKey": BIZINFO_API_KEY,
    "dataType": "json",
    "searchCnt": 400,
    "pageUnit": 400,
    "pageIndex": 1,
}

class Command(BaseCommand):
    help = 'BizTop 업데이트'

    def handle(self, *args, **kwargs):
        self.stdout.write("📡 BizInfo API 수집 시작…")
        items = self.fetch_api_items()
        self.stdout.write(f"✔ 총 {len(items):,}건 수신")

        # ────────────────────────────────────────────────
        # ①  최근 1주일 이내만 필터링
        one_week_ago = datetime.today().date() - timedelta(days=7)
        recent_items = []
        for it in items:
            self.stdout.write(f"creatPnttm: {type(it['creatPnttm'])}, {it['creatPnttm']}")
            try:
                reg_date = datetime.strptime(it["creatPnttm"], "%Y-%m-%d").date()
                if reg_date >= one_week_ago:
                    recent_items.append(it)
            except Exception:
                continue

        self.stdout.write(f"🆕 최근 1주일 데이터: {len(recent_items):,}건")
        if not recent_items:
            self.stderr.write("❗ 최근 일주일 내 공고가 없습니다. 종료")
            return
        # ────────────────────────────────────────────────

        # 이후 모든 로직에서 recent_items 사용
        exposure_scores = self.calc_exposure_scores(recent_items)
        max_score = max(exposure_scores.values()) if exposure_scores else 1.0
        # 보정조회수 계산
        adjusted = {}
        for it in recent_items:
            api_id = it["pblancId"]
            views  = int(it.get("inqireCo", 0))
            score  = exposure_scores.get(api_id, 1.0)
            factor = max_score / score if score else 1.0
            adjusted[api_id] = (views, views * factor)

        # Top-20 추출
        top_ids = sorted(adjusted, key=lambda k: adjusted[k][1], reverse=True)[:20]
        top_items = [it for it in recent_items if it["pblancId"] in top_ids]

        self.save_to_db(top_items)
        self.stdout.write(self.style.SUCCESS("✅ BizTop 업데이트 완료"))

    # ──────────────────────────────────────────────────────────────────────────
    def fetch_api_items(self):
        try:
            r = requests.get(API_URL, params=API_PARAMS, timeout=30)
            r.raise_for_status()
            return r.json().get("jsonArray", [])
        except Exception as e:
            self.stderr.write(f"❌ API 오류: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────────
    def calc_exposure_scores(self, items):
        """
        등록일(regDate) → 다음 주 월요일까지 날짜별 기여도 합산
        반환: {api_id: total_score, ...}
        """
        scores = {}
        for item in items:
            api_id = item["pblancId"]
            reg_str = item.get("registered_at")  # 'YYYY-MM-DD'
            try:
                reg_date = datetime.strptime(reg_str, "%Y-%m-%d").date()
            except Exception:
                continue

            # 다음 주 월요일 계산
            #   월=0 … 일=6,  지금 주가 아닌 '다음' 주 월요일 ⇒ (7 - weekday) % 7 + 7
            days_to_next_mon = ((7 - reg_date.weekday()) % 7) + 7
            next_monday = reg_date + timedelta(days=days_to_next_mon)

            # 등록일부터 (다음주 월요일 전날)까지 순회
            total = 0.0
            cur = reg_date
            while cur < next_monday:
                total += WEEKDAY_SCORE if cur.weekday() < 5 else WEEKEND_SCORE
                cur += timedelta(days=1)

            scores[api_id] = total
        return scores

    # ──────────────────────────────────────────────────────────────────────────
    @transaction.atomic
    def save_to_db(self, items):
        current_ids = []
        for item in items:                # ← top-20만 들어옴
            api_id = item["pblancId"]
            current_ids.append(api_id)

            BizTop.objects.update_or_create(
                pblanc_id=api_id,
                defaults={
                    "title": item.get("pblancNm", ""),
                    "update_date": item.get("registered_at", ""),
                },
            )

        # 이번 top-20에 포함되지 않은 기존 레코드는 삭제
        deleted, _ = BizTop.objects.exclude(pblanc_id__in=current_ids).delete()
        self.stdout.write(f"🗑️ 삭제된 레코드: {deleted}")