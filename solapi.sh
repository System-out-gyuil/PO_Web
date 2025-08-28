#!/bin/bash

# 가상환경 활성화
source /home/ubuntu/PO_Web/venv/bin/activate

# 작업 디렉토리 이동
cd /home/ubuntu/PO_Web

# 명령 실행
echo "[`date '+%Y-%m-%d %H:%M:%S'`] 🚀 solapi 시작" >> /home/ubuntu/cron_solapi.log
python manage.py solapi >> /home/ubuntu/cron_solapi.log 2>&1
echo "[`date '+%Y-%m-%d %H:%M:%S'`] ✅ solapi 완료" >> /home/ubuntu/cron_solapi.log