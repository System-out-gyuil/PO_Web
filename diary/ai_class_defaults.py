"""AI 클래스/폼 관련 기본 텍스트 정의."""


def get_class_form_default_texts():
    """신청 폼에서 사용하는 기본 텍스트 사전."""
    return {
        'form.title': '법인영업 원데이 클래스',
        'form.date': '일자 : 2025년 9월 16일(화요일) 15시 ~ 17시',
        'form.location': '장소 : 구로디지털단지역 인근 (자세한 주소는 추후 문자 안내), 주차가능',
        'form.capacity': '인원 : 선착순 10명',
        'form.bank': '기업은행 : 074-118859-04-015(주식회사 피오코퍼레이션)',
        'form.fee': '강의료 : 5만원',
        'form.notice': '신청서 접수 후 입금완료시, 클래스 참여 확정됩니다.',
        'form.label_name': '참석자 성함을 알려주세요',
        'form.placeholder_name': '이름을 입력해주세요',
        'form.label_phone': '참석자 연락처를 알려주세요',
        'form.placeholder_phone': '연락처를 입력해주세요. (예: 01012341234, 010-1234-1234, 010 1234 1234)',
        'form.phone_description': '연락처로 강의 관련 안내사항을 전달드립니다.',
        'form.label_desired_date': '희망 수강 날짜를 선택해주세요',
        'form.placeholder_desired_date': '예: 9월 16일 15시 클래스',
        'form.desired_date_description': '가능하신 날짜/시간을 적어주시면 일정 조율 시 참고합니다.',
        'form.button_text': '클래스 신청하기',
    }


def get_class_form_default_descriptions():
    """관리자 페이지에 표시할 기본 설명 사전."""
    return {
        'form.title': '상단 타이틀 텍스트',
        'form.date': '일자 안내 문구',
        'form.location': '장소 안내 문구',
        'form.capacity': '정원 안내 문구',
        'form.bank': '입금 계좌 문구',
        'form.fee': '강의료 안내 문구',
        'form.notice': '입금 안내/유의사항',
        'form.label_name': '이름 입력 라벨',
        'form.placeholder_name': '이름 입력 placeholder',
        'form.label_phone': '연락처 입력 라벨',
        'form.placeholder_phone': '연락처 입력 placeholder',
        'form.phone_description': '연락처 부가 설명',
        'form.label_desired_date': '희망 날짜 입력 라벨',
        'form.placeholder_desired_date': '희망 날짜 placeholder',
        'form.desired_date_description': '희망 날짜 부가 설명',
        'form.button_text': '제출 버튼 문구',
    }

