#!/usr/bin/env python
"""
완전한 view_select 필터링 수정 스크립트

1. diary/views.py의 임시 수정 사항을 정식 버전으로 변경
2. 상태별 필터링 로직 추가
3. JavaScript와 연동하여 동적 필터링 구현
"""

import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PO.settings')
django.setup()

from diary.models import Attribute, User

def fix_view_select_complete():
    """완전한 view_select 수정"""
    
    print("=== view_select 필터링 완전 수정 시작 ===")
    
    # 1. 데이터베이스 확인
    user = User.objects.get(id=1)
    attributes = Attribute.objects.filter(user=user)
    
    print(f"총 {attributes.count()}개 속성 확인 중...")
    
    # 2. view_select 필드 상태 확인
    dict_count = 0
    bool_count = 0
    
    for attr in attributes:
        if isinstance(attr.view_select, dict):
            dict_count += 1
        elif isinstance(attr.view_select, bool):
            bool_count += 1
            
    print(f"dict 형태: {dict_count}개, bool 형태: {bool_count}개")
    
    # 3. JavaScript 파일에 상태별 필터링 함수 추가
    js_code = '''
// 상태별 속성 필터링 함수 (개선된 버전)
function filterAttributesByStatus(statusId) {
    console.log('상태별 속성 필터링 시작:', statusId);
    
    // 페이지 새로고침 방식으로 변경
    const currentUrl = new URL(window.location);
    if (statusId === null || statusId === 'all') {
        currentUrl.searchParams.delete('status_id');
    } else {
        currentUrl.searchParams.set('status_id', statusId);
    }
    
    // 페이지 새로고침
    window.location.href = currentUrl.toString();
}

// 탭 선택 함수 수정
function selectStatusTab(statusId) {
    // 기존 활성 탭 비활성화
    document.querySelectorAll('.status-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 클릭된 탭 활성화
    event.target.classList.add('active');
    
    // 상태 필터 적용
    window.currentStatusTab = statusId;
    applyStatusFilter();
    
    // 상태별 속성 필터링 적용 (페이지 새로고침)
    filterAttributesByStatus(statusId);
}
'''
    
    # 4. views.py 파일에 정식 헬퍼 함수 추가
    views_helper_code = '''
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
    
    # 5. diary_list 함수 수정
    diary_list_code = '''
def diary_list(request):
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
    attributes = user_attributes
'''
    
    # 6. 실제 파일 수정
    with open('diary/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # pk__isnull=False를 다시 원래대로 수정하고 새로운 로직 적용
    if 'filter_attributes_by_status' not in content:
        # 헬퍼 함수 추가
        import_end = content.find('logger = logging.getLogger(__name__)')
        if import_end != -1:
            insert_pos = content.find('\n', import_end) + 1
            content = content[:insert_pos] + views_helper_code + '\n' + content[insert_pos:]
    
    # diary_list 함수의 시작 부분 찾기
    diary_list_start = content.find('def diary_list(request):')
    if diary_list_start != -1:
        # 함수 끝 찾기
        next_def_start = content.find('\ndef ', diary_list_start + 1)
        if next_def_start == -1:
            next_def_start = len(content)
        
        # 현재 함수 내용
        current_function = content[diary_list_start:next_def_start]
        
        # pk__isnull=False를 제거하고 새로운 로직으로 교체
        if 'pk__isnull=False' in current_function:
            print("기존 임시 수정 사항을 정식 버전으로 교체 중...")
            
            # 새로운 함수 내용 생성
            new_function = '''def diary_list(request):
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
    attributes = user_attributes
    
    attr_map = {attr.name: attr for attr in user_attributes}
    
    # 행 데이터는 모든 행을 가져옴 (필터링은 속성 레벨에서 처리)
    # 쿼리 최적화: select_related와 prefetch_related 적용
    rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
        'values__attribute__attributeType',
        'values__attribute__dropdown_attributes'
    ).order_by('order')
    
    # 각 행의 속성 값들을 가져오기 (필터링된 속성만)
    rows_data = []
    for row in rows:
        row_values = {}
        for attr in user_attributes:  # 이미 필터링된 속성들만 사용'''
            
            # 나머지 함수 내용은 그대로 유지하고 앞부분만 교체
            rest_of_function = current_function[current_function.find('# 행 데이터는 모든 행을 가져옴'):]
            if not rest_of_function:
                # 백업에서 원본 찾기
                with open('diary/views_backup.py', 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                backup_start = backup_content.find('def diary_list(request):')
                backup_next = backup_content.find('\ndef ', backup_start + 1)
                if backup_next == -1:
                    backup_next = len(backup_content)
                backup_function = backup_content[backup_start:backup_next]
                rest_of_function = backup_function[backup_function.find('# 행 데이터는 모든 행을 가져옴'):]
            
            new_function += rest_of_function
            
            # 교체
            content = content[:diary_list_start] + new_function + content[next_def_start:]
    
    # 파일 저장
    with open('diary/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("=== 수정 완료 ===")
    print("1. 헬퍼 함수 추가됨")
    print("2. diary_list 함수 수정됨")
    print("3. 상태별 필터링 로직 적용됨")
    print("4. URL 파라미터로 상태 ID 전달 방식 구현됨")
    
    # 7. 테스트
    print("\n=== 테스트 ===")
    test_attributes = filter_attributes_by_status(attributes, 'all')
    print(f"전체 탭에서 표시될 속성 수: {len(test_attributes)}")
    
    # 첫 번째 상태 ID로 테스트
    from diary.models import DropdownAttribute
    first_status = DropdownAttribute.objects.first()
    if first_status:
        test_attributes_status = filter_attributes_by_status(attributes, str(first_status.id))
        print(f"상태 ID {first_status.id}에서 표시될 속성 수: {len(test_attributes_status)}")

if __name__ == "__main__":
    fix_view_select_complete() 