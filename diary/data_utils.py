import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def parse_korean_currency(value):
    """한국어 통화 형식을 숫자로 변환"""
    if not value:
        return 0
    
    # 숫자만 추출
    numeric_value = re.sub(r'[^\d]', '', str(value))
    
    if not numeric_value:
        return 0
    
    # 단위 처리
    if '억' in str(value):
        return int(numeric_value) * 100000000
    elif '천만' in str(value):
        return int(numeric_value) * 10000000
    elif '만' in str(value):
        return int(numeric_value) * 10000
    elif '천' in str(value):
        return int(numeric_value) * 1000
    else:
        return int(numeric_value)

def parse_sales_amount(value):
    """매출액 파싱"""
    if not value:
        return 0
    
    # 숫자만 추출
    numeric_value = re.sub(r'[^\d]', '', str(value))
    
    if not numeric_value:
        return 0
    
    # 단위 처리
    if '억' in str(value):
        return int(numeric_value) * 100000000
    elif '천만' in str(value):
        return int(numeric_value) * 10000000
    elif '만' in str(value):
        return int(numeric_value) * 10000
    elif '천' in str(value):
        return int(numeric_value) * 1000
    else:
        return int(numeric_value)

def parse_business_data(value):
    """사업자 정보 파싱"""
    if not value:
        return None
    
    try:
        # JSON 형태로 파싱 시도
        import json
        data = json.loads(value)
        return data
    except (json.JSONDecodeError, TypeError):
        # 일반 텍스트인 경우 기본 구조로 변환
        return {
            'opening_date': value,
            'years_ago': None
        }

def calculate_business_years(opening_date, years_ago):
    """사업 연수 계산"""
    if not opening_date:
        return None
    
    try:
        if isinstance(opening_date, str):
            # 날짜 문자열 파싱
            if len(opening_date) == 8:  # YYYYMMDD 형식
                opening_date = datetime.strptime(opening_date, '%Y%m%d').date()
            elif len(opening_date) == 6:  # YYYYMM 형식
                opening_date = datetime.strptime(opening_date, '%Y%m').date()
            else:
                return None
        
        if isinstance(opening_date, date):
            today = date.today()
            years = relativedelta(today, opening_date).years
            return years
        
        return None
    except (ValueError, TypeError):
        return None

def formatToKoreanCurrency(amount):
    """숫자를 한국어 통화 형식으로 변환"""
    if not amount or amount == 0:
        return "0원"
    
    if amount >= 100000000:  # 1억 이상
        return f"{amount // 100000000}억원"
    elif amount >= 10000:  # 1만 이상
        return f"{amount // 10000}만원"
    elif amount >= 1000:  # 1천 이상
        return f"{amount // 1000}천원"
    else:
        return f"{amount}원"

# 캐싱을 위한 유틸리티 함수들
def create_dropdown_cache(attributes):
    """드롭다운 속성들의 옵션을 캐시로 생성"""
    cache = {}
    for attr in attributes:
        if attr.attributeType and attr.attributeType.name == 'dropdown':
            cache[attr.id] = {
                dropdown_attr.id: {
                    'id': dropdown_attr.id,
                    'option': dropdown_attr.option,
                    'color': dropdown_attr.color,
                    'order': dropdown_attr.order
                }
                for dropdown_attr in attr.dropdown_attributes.all()
            }
    return cache

def get_dropdown_option_from_cache(cache, attr_id, value_id):
    """캐시에서 드롭다운 옵션 가져오기"""
    if attr_id in cache and value_id in cache[attr_id]:
        return cache[attr_id][value_id]
    return None

def create_row_values_cache(rows):
    """행들의 속성값을 캐시로 생성"""
    cache = {}
    for row in rows:
        cache[row.id] = {
            attr_value.attribute.name: attr_value.value 
            for attr_value in row.values.all() 
            if attr_value.attribute
        }
    return cache

def optimize_session_data_parsing(session_data):
    """세션 데이터 파싱 최적화"""
    optimized = {}
    for key, default_value in session_data.items():
        try:
            session_value = session_data.get(key, default_value)
            if isinstance(session_value, str):
                import json
                optimized[key] = json.loads(session_value)
            else:
                optimized[key] = session_value
        except (json.JSONDecodeError, TypeError):
            optimized[key] = default_value
    return optimized