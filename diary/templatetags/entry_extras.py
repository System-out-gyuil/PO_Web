from django import template
register = template.Library()

@register.filter
def get_field(entry, field):
    # 기본 필드 우선, 없으면 extra에서
    if hasattr(entry, field):
        val = getattr(entry, field)
        return val if val is not None else ''
    return entry.extra.get(field, '')

# 딕셔너리용 get_item 필터 (values|get_item:attr.name)
@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key, '')
    except Exception:
        return ''

@register.filter
def to_rgba(hex_color, alpha='0.18'):
    """HEX(#RRGGBB) -> rgba(r,g,b,a) 변환"""
    if not hex_color:
        return ''
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r},{g},{b},{alpha})'
    except Exception:
        return ''

@register.filter
def get_item_id(entry, attr_name):
    try:
        from diary.models import CustomAttribute, AttributeValue
        attr = CustomAttribute.objects.get(name=attr_name, user=entry.user)
        attr_value = AttributeValue.objects.filter(entry=entry, attribute=attr).first()
        return str(attr_value.value) if attr_value else ''
    except Exception:
        return ''

@register.filter
def get_option_by_id(options, id):
    try:
        for opt in options:
            if str(opt.id) == str(id):
                return opt
        return None
    except Exception:
        return None

@register.filter
def split(value, delimiter=','):
    """문자열을 구분자로 나누어 리스트로 반환"""
    if not value:
        return []
    return str(value).split(delimiter)

@register.filter
def to_korean_currency(value):
    """숫자를 한국어 통화 단위로 변환 (백만 단위 기준)"""
    if not value:
        return '0원'
    
    try:
        # 문자열인 경우 숫자만 추출
        if isinstance(value, str):
            num = int(''.join(filter(str.isdigit, value)))
        else:
            num = int(value)
        
        if num == 0:
            return '0원'
        
        result = ''
        remaining = num
        
        # 백만 단위 이상인지 확인
        is_over_baekman = remaining >= 1000000
        
        # 억 단위 처리
        if remaining >= 100000000:
            eok = remaining // 100000000
            result += str(eok) + '억'
            remaining = remaining % 100000000
        
        # 천만 단위 처리 (천으로 표시)
        if remaining >= 10000000:
            cheon = remaining // 10000000
            result += ' ' + str(cheon) + '천'
            remaining = remaining % 10000000
        
        # 백만 단위 처리
        if remaining >= 1000000:
            baek = remaining // 1000000
            result += ' ' + str(baek) + '백'
            remaining = remaining % 1000000
        
        # 천만이나 백만 단위가 있으면 '만원'으로 끝냄
        if '천' in result or '백' in result:
            return result + '만원'
        # 억 단위만 있으면 '원'으로 끝냄
        elif result and '억' in result:
            return result + '원'
        # 백만 단위 이상이면 '만원'으로 끝냄
        elif is_over_baekman:
            return result + '만원'
        
        # 백만 단위 이하일 때는 만 단위까지 표시
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
        
    except (ValueError, TypeError):
        return str(value)

@register.filter
def to_korean_currency_limited(value):
    """숫자를 한국어 통화 단위로 변환 (백만 단위까지만 표시)"""
    if not value:
        return '0원'
    
    try:
        # 문자열인 경우 숫자만 추출
        if isinstance(value, str):
            num = int(''.join(filter(str.isdigit, value)))
        else:
            num = int(value)
        
        if num == 0:
            return '0원'
        
        result = ''
        remaining = num
        
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
        
        # 백만 단위까지만 표시하므로 만 단위 이하는 제외
        # 만 단위가 남아있고 앞에 억/천/백이 없을 때만 표시
        if remaining >= 10000 and not result:
            result = str(remaining // 10000) + '만'
        
        return result + '원'
        
    except (ValueError, TypeError):
        return str(value) 