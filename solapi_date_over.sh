#!/bin/bash

# 가상환경 활성화
source /home/ubuntu/PO_Web/venv/bin/activate

# 작업 디렉토리 이동
cd /home/ubuntu/PO_Web

# 명령 실행
echo "[`date '+%Y-%m-%d %H:%M:%S'`] 🚀 solapi_date_over 시작" >> /home/ubuntu/cron_solapi_date_over.log
python manage.py solapi_date_over >> /home/ubuntu/cron_solapi_date_over.log 2>&1
echo "[`date '+%Y-%m-%d %H:%M:%S'`] ✅ solapi_date_over 완료" >> /home/ubuntu/cron_solapi_date_over.log