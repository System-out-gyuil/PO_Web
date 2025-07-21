import json
from datetime import datetime

def parse_korean_currency(value):
    """한국어 통화를 숫자로 변환"""
    if not value or value == '0':
        return 0
    
    # 숫자만 추출
    if isinstance(value, str):
        # 콤마 제거
        value = value.replace(',', '')
        # 숫자가 아닌 문자 제거
        value = ''.join(c for c in value if c.isdigit())
    
    try:
        return int(value) if value else 0
    except (ValueError, TypeError):
        return 0

def parse_sales_amount(eok, cheonman):
    """억과 천만 단위를 숫자로 변환"""
    try:
        eok_amount = int(eok) if eok else 0
        cheonman_amount = int(cheonman) if cheonman else 0
        
        # 총 금액 계산 (억 * 100000000 + 천만 * 10000000)
        total_amount = eok_amount * 100000000 + cheonman_amount * 10000000
        return total_amount
    except (ValueError, TypeError):
        return 0
    
def parse_business_data(value):
    """개업년월 데이터 파싱"""
    if not value:
        return {}
    
    # 이미 JSON 형태인 경우
    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    
    # 일반 문자열인 경우 (날짜 형식)
    if isinstance(value, str):
        return {'opening_date': value}
    
    # 딕셔너리인 경우
    if isinstance(value, dict):
        return value
    
    return {}

def calculate_business_years(opening_date_str, years_ago=None):
    """개업년수 계산"""
    if years_ago:
        try:
            return int(years_ago)
        except (ValueError, TypeError):
            pass
    
    if not opening_date_str:
        return None
    
    try:
        opening_date = datetime.strptime(opening_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        years = current_date.year - opening_date.year
        if current_date.month < opening_date.month or (current_date.month == opening_date.month and current_date.day < opening_date.day):
            years -= 1
        return max(0, years)
    except (ValueError, TypeError):
        return None
    
def formatToKoreanCurrency(amount):
    """숫자를 한국어 통화 단위로 변환 (to_korean_currency 필터와 동일한 포맷)"""
    if not amount or amount == 0:
        return '0원'
    
    amount = int(amount)
    if amount == 0:
        return '0원'
    
    result = ''
    remaining = amount
    
    # 억 단위 처리
    if remaining >= 100000000:
        eok = remaining // 100000000
        result += str(eok) + '억'
        remaining = remaining % 100000000
    
    # 천만 단위 처리 (천으로 표시)
    if remaining >= 10000000:
        cheon = remaining // 10000000
        if result:
            result += ' '
        result += str(cheon) + '천'
        remaining = remaining % 10000000
    
    # 백만 단위 처리
    if remaining >= 1000000:
        baek = remaining // 1000000
        if result:
            result += ' '
        result += str(baek) + '백'
        remaining = remaining % 1000000
    
    # 만 단위가 남아있으면 추가 (단, 앞에 억/천/백이 없을 때만)
    if remaining >= 10000:
        if not result:  # 앞에 억/천/백이 없을 때만
            result = str(remaining // 10000) + '만'
        else:
            # 앞에 억/천/백이 있을 때는 만 단위가 0이 아닐 때만 추가
            if remaining // 10000 > 0:
                result += str(remaining // 10000) + '만'
        remaining = remaining % 10000
    
    # 10,000 미만의 값은 그대로 표시
    if remaining > 0 and remaining < 10000:
        if result:
            result += str(remaining)
        else:
            result = str(remaining)
    
    return result + '원'