#!/bin/bash

# 가상환경 활성화
source /home/ubuntu/PO_Web/venv/bin/activate

# 작업 디렉토리 이동
cd /home/ubuntu/PO_Web

# 명령 실행
echo "[`date '+%Y-%m-%d %H:%M:%S'`] 🚀 toss_payments_auto 시작" >> /home/ubuntu/toss_payments_auto.log
python manage.py toss_payments_auto >> /home/ubuntu/toss_payments_auto.log 2>&1
echo "[`date '+%Y-%m-%d %H:%M:%S'`] ✅ toss_payments_auto 완료" >> /home/ubuntu/toss_payments_auto.log