# Attribute ID 변경 스크립트

Attribute 테이블의 ID를 변경할 때 FK로 참조하는 모든 테이블들의 ID도 함께 변경하는 Django 스크립트입니다.

## 📋 지원하는 테이블

다음 테이블들의 FK 참조를 자동으로 업데이트합니다:

- **AttributeValue** - `attribute_id` FK
- **DropdownAttribute** - `attribute_id` FK  
- **CalendarSettings** - `settings` JSON 필드 내 attribute_id 참조
- **KanbanSettings** - `settings` JSON 필드 내 attribute_id 참조

## 🚀 사용법

### 1. 대화형 실행 (권장)

```bash
python run_attribute_update.py
```

실행 후 프롬프트에 따라:
1. 사용자 ID 입력
2. 작업 선택 (단일 변경 / 일괄 변경 / 목록 확인)
3. 변경할 ID 입력

### 2. 직접 스크립트 실행

```python
from update_attribute_id import update_attribute_id, update_attribute_order, show_user_attributes

# 사용자 Attribute 목록 확인
show_user_attributes(user_id=1)

# 단일 Attribute ID 변경
success = update_attribute_id(old_id=16, new_id=18, user_id=1)

# 여러 Attribute 순서 일괄 변경
attribute_orders = [
    (16, 18),  # ID 16을 18로 변경
    (17, 19),  # ID 17을 19로 변경
]
success = update_attribute_order(user_id=1, attribute_orders=attribute_orders)
```

## ⚠️ 주의사항

1. **백업 필수**: 실행 전 반드시 데이터베이스 백업을 수행하세요.
2. **트랜잭션 안전**: 모든 변경사항은 트랜잭션으로 처리되어 실패 시 롤백됩니다.
3. **ID 충돌**: 새로운 ID가 이미 존재하면 변경이 실패합니다.
4. **사용자별 변경**: 특정 사용자의 Attribute만 변경하려면 `user_id`를 지정하세요.

## 🔧 스크립트 기능

### `update_attribute_id(old_id, new_id, user_id=None)`
- 단일 Attribute의 ID를 변경
- FK로 참조하는 모든 테이블 자동 업데이트
- JSON 필드 내 attribute_id 참조도 자동 변경

### `update_attribute_order(user_id, attribute_orders)`
- 여러 Attribute의 순서를 한 번에 변경
- `[(old_id1, new_id1), (old_id2, new_id2), ...]` 형태로 입력

### `show_user_attributes(user_id)`
- 특정 사용자의 Attribute 목록을 표 형태로 출력
- ID, 이름, 필수여부, 상세여부, 순서 정보 포함

## 📊 출력 예시

```
=== Attribute ID 변경 시작 ===
기존 ID: 16 -> 새로운 ID: 18
✅ 변경할 Attribute: 매출 (사용자: 홍길동)

📋 영향받는 테이블들:
  - AttributeValue: 25개 행
  - DropdownAttribute: 3개 행

🔄 ID 변경 작업 시작...
  ✅ AttributeValue: 25개 행 업데이트 완료
  ✅ DropdownAttribute: 3개 행 업데이트 완료
  ✅ CalendarSettings: 1개 행 업데이트 완료

✅ Attribute ID 변경 완료!
  기존 ID: 16 -> 새로운 ID: 18
  속성명: 매출
```

## 🛠️ 문제 해결

### 오류: "ID X인 Attribute를 찾을 수 없습니다"
- 사용자 ID가 올바른지 확인
- 해당 Attribute가 실제로 존재하는지 확인

### 오류: "새로운 ID X가 이미 존재합니다"
- 새로운 ID가 사용 가능한지 확인
- 다른 ID를 선택하거나 기존 ID를 먼저 변경

### JSON 파싱 오류
- CalendarSettings나 KanbanSettings의 JSON 데이터가 손상된 경우
- 해당 설정을 수동으로 확인하고 복구 필요

## 📝 예시 시나리오

### 시나리오 1: 단일 Attribute 순서 변경
```python
# ID 16인 "매출" 속성을 ID 18로 변경
update_attribute_id(16, 18, user_id=1)
```

### 시나리오 2: 여러 Attribute 순서 일괄 변경
```python
# 여러 속성의 순서를 한 번에 변경
attribute_orders = [
    (16, 18),  # 매출: 16 -> 18
    (17, 19),  # 기대출: 17 -> 19
    (18, 20),  # 추천자금: 18 -> 20
]
update_attribute_order(user_id=1, attribute_orders=attribute_orders)
```

### 시나리오 3: 현재 상태 확인
```python
# 사용자 1의 모든 Attribute 목록 확인
show_user_attributes(user_id=1)
```

## 🔄 실행 후 확인사항

1. **상세보기 모달**: 변경된 순서로 컬럼이 표시되는지 확인
2. **데이터 무결성**: 기존 데이터가 손실되지 않았는지 확인
3. **FK 참조**: 다른 테이블에서 올바르게 참조되는지 확인 