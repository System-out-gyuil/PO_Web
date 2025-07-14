# view_select 필터링 문제 해결 요약

## 문제 상황
- `view_select` 필드가 boolean에서 dict 형태로 변경됨
- 기존 코드에서 `view_select=True` 필터링으로 인해 데이터가 화면에 나타나지 않음
- 상태별로 다른 속성을 표시해야 하는 요구사항

## 해결 방법

### 1. 헬퍼 함수 추가 (diary/views.py)
```python
def filter_attributes_by_status(queryset, status_id='all'):
    """상태 ID에 따라 속성들을 필터링하는 함수"""
    filtered_attrs = []
    for attr in queryset:
        if isinstance(attr.view_select, dict):
            if status_id == 'all':
                if attr.view_select.get("0", False):
                    filtered_attrs.append(attr)
            else:
                if attr.view_select.get(str(status_id), False):
                    filtered_attrs.append(attr)
        elif isinstance(attr.view_select, bool) and attr.view_select:
            filtered_attrs.append(attr)
    return filtered_attrs
```

### 2. diary_list 함수 수정
- URL 파라미터에서 `status_id` 가져오기
- `filter_attributes_by_status` 함수 사용하여 상태별 속성 필터링

### 3. entry_table_partial 함수 수정
- 동일하게 상태별 필터링 로직 적용

### 4. get_dropdown_attributes 함수 수정
- 드롭다운 속성도 상태별 필터링 적용

### 5. JavaScript 수정 (templates/diary/diary_list.html)
- `selectStatusTab` 함수를 페이지 새로고침 방식으로 변경
- URL 파라미터로 `status_id` 전달
- 페이지 로드 시 현재 상태 탭 활성화

## 작동 방식

1. 사용자가 상태 탭 클릭
2. JavaScript에서 URL에 `status_id` 파라미터 추가하여 페이지 새로고침
3. 서버에서 `status_id` 파라미터 확인
4. 해당 상태에 맞는 속성들만 필터링하여 화면에 표시
5. 행 데이터도 해당 상태에 맞는 속성들만 표시

## view_select 데이터 구조

```json
{
  "0": true,     // 전체 탭에서 표시
  "23": true,    // 접수대기 상태에서 표시
  "25": false,   // 심사중 상태에서 숨김
  "36": true,    // 발표완료 상태에서 표시
  // ... 기타 상태 ID들
}
```

## 호환성
- 기존 boolean 형태의 `view_select`와도 호환
- 점진적 마이그레이션 가능

## 테스트 방법
1. 다이어리 목록 페이지 접속
2. 상태 탭 클릭하여 속성 필터링 확인
3. 각 상태별로 다른 속성들이 표시되는지 확인 