#!/usr/bin/env python
"""
view_select 필터링 문제 해결 스크립트

기존 boolean 방식에서 dict 방식으로 변경된 view_select 필드에 맞춰
diary/views.py 파일의 필터링 로직을 수정합니다.
"""

import os
import re

def fix_view_select_filtering():
    """view_select 필터링 로직을 수정하는 함수"""
    
    views_file_path = 'diary/views.py'
    
    # 파일 읽기
    with open(views_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 헬퍼 함수 추가 (파일 맨 위에 import 문 다음에)
    helper_function = '''
# 상태별 view_select 필터링을 위한 헬퍼 함수
def filter_attributes_by_status(queryset, status_id='all'):
    """
    상태 ID에 따라 속성들을 필터링하는 함수
    
    Args:
        queryset: Attribute 쿼리셋
        status_id: 상태 ID ('all' 또는 특정 dropdown attribute ID)
    
    Returns:
        필터링된 속성 리스트
    """
    filtered_attrs = []
    for attr in queryset:
        if isinstance(attr.view_select, dict):
            # dict 형태인 경우
            if status_id == 'all':
                # 전체 탭인 경우: "0" 키 확인
                if attr.view_select.get("0", False):
                    filtered_attrs.append(attr)
            else:
                # 특정 상태 탭인 경우: 해당 상태 ID 확인
                if attr.view_select.get(str(status_id), False):
                    filtered_attrs.append(attr)
        elif isinstance(attr.view_select, bool) and attr.view_select:
            # 기존 boolean 형태와의 호환성 (모든 상태에서 표시)
            filtered_attrs.append(attr)
    return filtered_attrs

'''
    
    # import 문 다음에 헬퍼 함수 삽입
    import_pattern = r'(logger = logging\.getLogger\(__name__\)\n)'
    content = re.sub(import_pattern, r'\1' + helper_function, content)
    
    # diary_list 함수의 속성 필터링 부분 수정
    diary_list_old = r'''def diary_list\(request\):
    user = User\.objects\.get\(id=1\)
    
    # detail 필터링 추가: 기본적으로 detail=False인 속성만 표시
    show_detail = request\.GET\.get\('detail', '0'\) == '1'  # detail=1이면 상세 속성도 표시
    
    # 속성 필터링: detail 값과 view_select 값에 따라 필터링
    if show_detail:
        attributes = Attribute\.objects\.filter\(view_select=True\)\.order_by\('sort_order', 'id'\)  # view_select=True인 속성만 표시
        user_attributes = Attribute\.objects\.filter\(user=user, view_select=True\)\.order_by\('sort_order', 'id'\)  # view_select=True인 속성만 표시
    else:
        attributes = Attribute\.objects\.filter\(detail=False, view_select=True\)\.order_by\('sort_order', 'id'\)  # detail=False이고 view_select=True인 속성만 표시
        user_attributes = Attribute\.objects\.filter\(user=user, detail=False, view_select=True\)\.order_by\('sort_order', 'id'\)  # detail=False이고 view_select=True인 속성만 표시'''
    
    diary_list_new = '''def diary_list(request):
    user = User.objects.get(id=1)
    
    # 현재 선택된 상태 ID 가져오기 (URL 파라미터 또는 기본값)
    current_status_id = request.GET.get('status_id', 'all')  # 'all'은 전체 탭
    
    # detail 필터링 추가: 기본적으로 detail=False인 속성만 표시
    show_detail = request.GET.get('detail', '0') == '1'  # detail=1이면 상세 속성도 표시
    
    # 속성 필터링: detail 값과 view_select 값에 따라 필터링
    if show_detail:
        base_attributes = Attribute.objects.filter(user=user).order_by('sort_order', 'id')
    else:
        base_attributes = Attribute.objects.filter(user=user, detail=False).order_by('sort_order', 'id')
    
    # 상태별 view_select 필터링 적용
    user_attributes = filter_attributes_by_status(base_attributes, current_status_id)
    attributes = user_attributes'''
    
    content = re.sub(diary_list_old, diary_list_new, content, flags=re.DOTALL)
    
    # entry_table_partial 함수 수정
    entry_table_old = r'''def entry_table_partial\(request\):
    user = User\.objects\.get\(id=1\)
    # 항상 detail=False, view_select=True만 표시 \(쿼리 최적화\)
    attributes = Attribute\.objects\.filter\(user=user, detail=False, view_select=True\)\.select_related\('attributeType'\)\.order_by\('sort_order', 'id'\)
    user_attributes = attributes'''
    
    entry_table_new = '''def entry_table_partial(request):
    user = User.objects.get(id=1)
    
    # 현재 선택된 상태 ID 가져오기
    current_status_id = request.GET.get('status_id', 'all')
    
    # detail=False인 속성들 가져오기
    base_attributes = Attribute.objects.filter(user=user, detail=False).select_related('attributeType').order_by('sort_order', 'id')
    
    # 상태별 view_select 필터링 적용
    attributes = filter_attributes_by_status(base_attributes, current_status_id)
    user_attributes = attributes'''
    
    content = re.sub(entry_table_old, entry_table_new, content, flags=re.DOTALL)
    
    # get_dropdown_attributes 함수 수정
    dropdown_old = r'''dropdown_attributes = Attribute\.objects\.filter\(
            user=user, 
            attributeType__name='dropdown',
            detail=False,
            view_select=True
        \)\.order_by\('-assential', 'name'\)'''
    
    dropdown_new = '''# 모든 dropdown 속성 가져오기
        base_dropdown_attributes = Attribute.objects.filter(
            user=user, 
            attributeType__name='dropdown',
            detail=False
        ).order_by('-assential', 'name')
        
        # 상태별 필터링 적용
        current_status_id = request.GET.get('status_id', 'all')
        dropdown_attributes = filter_attributes_by_status(base_dropdown_attributes, current_status_id)'''
    
    content = re.sub(dropdown_old, dropdown_new, content)
    
    # 파일에 쓰기
    with open(views_file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("view_select 필터링 로직이 성공적으로 수정되었습니다.")
    print("수정된 내용:")
    print("1. filter_attributes_by_status 헬퍼 함수 추가")
    print("2. diary_list 함수의 속성 필터링 로직 수정")
    print("3. entry_table_partial 함수 수정")
    print("4. get_dropdown_attributes 함수 수정")

if __name__ == "__main__":
    fix_view_select_filtering() 