import json
from datetime import datetime, timedelta
from .models import Attribute, AttributeValue, User

def apply_dependent_transformation(source_value, new_row):
    """종속적 데이터 변환을 적용하는 함수"""
    if not source_value.attribute:
        return source_value.value
    
    attribute_name = source_value.attribute.name
    original_value = source_value.value
    
    # 종속성 설정이 있는지 확인
    if hasattr(source_value.attribute, 'dependent_attributes') and source_value.attribute.dependent_attributes:
        try:
            dependent_config = json.loads(source_value.attribute.dependent_attributes)
        except (json.JSONDecodeError, TypeError):
            dependent_config = {}
    else:
        dependent_config = {}
    
    # 기본 변환 규칙 적용
    transformed_value = original_value
    
    # 1. 날짜 관련 변환 (예: 개업일 → 개업일 + 1년)
    if '개업일' in attribute_name or '설립일' in attribute_name:
        if original_value:
            try:
                # 날짜 파싱 및 1년 후로 설정
                date_obj = datetime.strptime(original_value, '%Y-%m-%d')
                new_date = date_obj + timedelta(days=365)
                transformed_value = new_date.strftime('%Y-%m-%d')
            except:
                pass
    
    # 2. 매출 관련 변환 (예: 매출 * 1.1)
    elif '매출' in attribute_name:
        if original_value:
            try:
                # 한국어 통화 파싱
                from .views import parse_korean_currency, formatToKoreanCurrency
                numeric_value = parse_korean_currency(original_value)
                if numeric_value > 0:
                    # 10% 증가
                    increased_value = int(numeric_value * 1.1)
                    transformed_value = formatToKoreanCurrency(increased_value)
            except:
                pass
    
    # 3. 연령 관련 변환 (예: 연령 + 1)
    elif '연령' in attribute_name or '나이' in attribute_name:
        if original_value:
            try:
                age = int(original_value)
                transformed_value = str(age + 1)
            except:
                pass
    
    # 4. 사업기간 관련 변환 (예: 사업기간 + 1년)
    elif '사업기간' in attribute_name or '운영기간' in attribute_name:
        if original_value:
            try:
                # "X년 Y개월" 형식 파싱
                if '년' in original_value and '개월' in original_value:
                    years = int(original_value.split('년')[0])
                    months = int(original_value.split('년')[1].split('개월')[0])
                    new_years = years + 1
                    transformed_value = f"{new_years}년 {months}개월"
                elif '년' in original_value:
                    years = int(original_value.split('년')[0])
                    transformed_value = f"{years + 1}년"
                elif '개월' in original_value:
                    months = int(original_value.split('개월')[0])
                    new_years = months // 12 + 1
                    new_months = months % 12
                    if new_months == 0:
                        transformed_value = f"{new_years}년"
                    else:
                        transformed_value = f"{new_years}년 {new_months}개월"
            except:
                pass
    
    # 5. 순번 관련 변환 (예: 순번 + 1)
    elif '순번' in attribute_name or '번호' in attribute_name:
        if original_value:
            try:
                number = int(original_value)
                transformed_value = str(number + 1)
            except:
                pass
    
    # 6. 금액 관련 변환 (예: 대출금액 * 1.05)
    elif any(keyword in attribute_name for keyword in ['대출', '금액', '원금', '채무']):
        if original_value:
            try:
                from .views import parse_korean_currency, formatToKoreanCurrency
                numeric_value = parse_korean_currency(original_value)
                if numeric_value > 0:
                    # 5% 증가
                    increased_value = int(numeric_value * 1.05)
                    transformed_value = formatToKoreanCurrency(increased_value)
            except:
                pass
    
    # 7. 퍼센트 관련 변환 (예: 이자율 + 0.5%)
    elif '이자율' in attribute_name or '수익률' in attribute_name:
        if original_value:
            try:
                # 퍼센트 값 파싱
                if '%' in original_value:
                    rate = float(original_value.replace('%', ''))
                    new_rate = rate + 0.5
                    transformed_value = f"{new_rate:.1f}%"
                else:
                    rate = float(original_value)
                    new_rate = rate + 0.5
                    transformed_value = f"{new_rate:.1f}%"
            except:
                pass
    
    # 8. 수량 관련 변환 (예: 직원수 + 1)
    elif '직원수' in attribute_name or '인원' in attribute_name:
        if original_value:
            try:
                count = int(original_value)
                transformed_value = str(count + 1)
            except:
                pass
    
    # 9. 드롭다운 값 변환 (종속성 설정에 따라)
    if dependent_config and 'dropdown_mapping' in dependent_config:
        dropdown_mapping = dependent_config['dropdown_mapping']
        if attribute_name in dropdown_mapping:
            mapping = dropdown_mapping[attribute_name]
            if original_value in mapping:
                transformed_value = mapping[original_value]
    
    return transformed_value

def get_dependency_config(attribute):
    """속성의 종속성 설정을 가져오는 함수"""
    if hasattr(attribute, 'dependent_attributes') and attribute.dependent_attributes:
        try:
            return json.loads(attribute.dependent_attributes)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}

def set_dependency_config(attribute, config):
    """속성의 종속성 설정을 저장하는 함수"""
    attribute.dependent_attributes = json.dumps(config, ensure_ascii=False)
    attribute.save() 