# 사용 기간 만료 알림 시스템

## 개요
사용자의 `use_date`가 2일 남았을 때 자동으로 SMS를 발송하는 시스템입니다.

## 기능
- 사용자의 `use_date`가 현재 시간으로부터 2일 후에 만료되는 경우를 감지
- 해당 사용자에게 자동으로 SMS 발송
- 발송 결과 로그 기록

## 사용법

### 1. 수동 실행
```bash
# Windows
send_expiry_notifications.bat

# Linux/Mac
./send_expiry_notifications.sh

# 또는 직접 Django 명령어 실행
python manage.py send_expiry_notifications
```

### 2. 자동 실행 (Cron Job)

#### Windows (Task Scheduler)
1. Windows 검색에서 "작업 스케줄러" 검색
2. "작업 만들기" 클릭
3. 트리거에서 "매일" 선택
4. 동작에서 `send_expiry_notifications.bat` 파일 경로 지정
5. 원하는 시간 설정 (예: 매일 오전 9시)

#### Linux/Mac (Cron)
```bash
# crontab 편집
crontab -e

# 매일 오전 9시에 실행
0 9 * * * /path/to/your/project/send_expiry_notifications.sh

# 또는 매시간 실행
0 * * * * /path/to/your/project/send_expiry_notifications.sh
```

## 설정

### SMS 템플릿
`diary/solapi.py`에서 `use_date_over` 타입의 템플릿 ID를 설정해야 합니다:
```python
elif send_type == "use_date_over":
    template_id = "KA01TP250828021917148PFOr7NEneMJ"
```

### API 키 설정
`config.py` 파일에 다음 설정이 필요합니다:
```python
SOLAPI_API_KEY = "your_api_key"
SOLAPI_SECRET_KEY = "your_secret_key"
SEND_NUMBER = "your_sender_number"
```

## 로그
명령어 실행 시 다음과 같은 로그가 출력됩니다:
- 총 알림 대상 사용자 수
- 각 사용자별 발송 성공/실패 여부
- 최종 발송 결과 요약

## 주의사항
- 사용자는 `activate=True` 상태여야 함
- 사용자는 `phone_number`가 설정되어 있어야 함
- SMS 발송 실패 시 로그에 오류 내용이 기록됨
- 2일 전후 1시간 범위 내의 사용자에게 발송됨
