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