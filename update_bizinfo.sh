#!/bin/bash
# 가상환경 활성화
source /home/ubuntu/PO_Web/venv/bin/activate

# 작업 디렉토리 이동
cd /home/ubuntu/PO_Web

# 명령 실행
/home/ubuntu/PO_Web/venv/bin/python manage.py update_bizinfo
