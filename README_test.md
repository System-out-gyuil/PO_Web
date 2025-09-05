# 정책자금 추천 엔진 테스트 가이드

## 📋 개요

`funding_calculator.py`의 로직을 검증하기 위한 종합 테스트 시스템입니다.

## 🚀 사용 방법

### 1. 기본 테스트 실행

```bash
python test_funding_calculator.py
```

### 2. 간단한 실행

```bash
python run_test.py
```

### 3. 결과 확인

```bash
# 콘솔에서 결과 보기
python view_test_results.py

# HTML 리포트 생성
python create_readable_report.py
```

## 📁 파일 구조

```
├── test_funding_calculator.py    # 메인 테스트 스크립트
├── run_test.py                   # 간단한 실행 스크립트
├── view_test_results.py          # JSON 결과 뷰어
├── create_readable_report.py     # HTML 리포트 생성
├── test_results.json            # 테스트 결과 (JSON)
├── test_results.html            # 테스트 결과 (HTML)
└── README_test.md               # 이 파일
```

## 🧪 테스트 케이스

### 그룹 A: 제조업/IT 기보 중심 (1-10번)

- 기보 최소 1억원 보장 테스트
- 기보 20% 기준 적용
- 기보 증액 우선 원칙
- 청년 제조업 창업 복합 자금
- IT기업 기보 대상업종 확인
- 저신용 제조업 경력 보완
- 예비창업 제조업 매출 0원
- 대형 제조업 기보 한도 최대 활용
- 기보 자격 미달 경력 부족
- 기보 기대출 초과 신보 전환 방지

### 그룹 B: 서비스업 신보 중심 (11-18번)

- 고매출 서비스업 신보 15% 요율
- 중간 서비스업 신보 12% 요율
- 신보 기대출 보유 증액 케이스
- 신보 자격 미달 신용점수 부족
- 신보 자격 미달 업력 부족
- 건설업 특수업종 직원수 기준
- 운수업 특수업종 + 소진공
- 대표님 제시 사례 전문과학및기술서비스업

### 그룹 C: 소진공 특화 (19-25번)

- 소진공 혁신성장 고한도 매출 3억 이상
- 소진공 혁신성장 일반한도
- 소진공 저신용 케이스
- 소진공 직원수 초과 일반업종
- 소진공 매출 부족 케이스
- 혁신성장 vs 저신용 선택 로직
- 특수업종 직원수 경계 테스트

### 그룹 D: 경계값 및 특수 케이스 (26-30번)

- 매출 0원 서비스업 예비창업
- 신용보증재단 상담필요 케이스
- 복합 기대출 보유 케이스
- 신용점수 850점 경계 케이스
- 모든 조건 만족 최대 복합 자금

## 📊 결과 분석

### JSON 구조

```json
{
  "test_id": "TEST_001",
  "status": "PASS|FAIL|ERROR",
  "description": "테스트 설명",
  "test_focus": "테스트 포커스",
  "input_conditions": {
    "original_data": {
      /* 원본 입력 데이터 */
    },
    "converted_data": {
      /* 변환된 데이터 */
    }
  },
  "results": {
    "expected": [
      /* 예상 결과 */
    ],
    "actual": [
      /* 실제 결과 */
    ],
    "total_amount": 0,
    "funds_count": 0
  },
  "comparison": {
    "is_match": true,
    "only_expected": [
      /* 예상에만 있음 */
    ],
    "only_actual": [
      /* 실제에만 있음 */
    ]
  }
}
```

### HTML 리포트 특징

- 📊 시각적 요약 대시보드
- 🔍 상세한 테스트 케이스별 분석
- 📋 입력 조건과 결과 비교
- 🎨 색상으로 구분된 상태 표시
- 📱 반응형 디자인

## 🛠️ 커스터마이징

### 새로운 테스트 케이스 추가

`test_funding_calculator.py`의 `test_samples` 리스트에 새로운 케이스 추가:

```python
{
    'id': 'TEST_031',
    'description': '새로운 테스트 케이스',
    'data': {
        'annual_revenue': 500_000_000,
        'credit_score': 850,
        # ... 기타 데이터
    },
    'expected_results': ['예상 결과 1', '예상 결과 2'],
    'test_focus': '테스트 포커스 설명'
}
```

### 데이터 변환 로직 수정

`convert_test_data_to_calculator_format()` 함수에서 변환 로직 수정

## 🔧 문제 해결

### 일반적인 문제

1. **모듈을 찾을 수 없음**: `diary.funding_calculator` 모듈 경로 확인
2. **JSON 파일 없음**: 먼저 `test_funding_calculator.py` 실행
3. **브라우저 열기 실패**: `test_results.html` 파일을 수동으로 열기

### 디버깅

- 콘솔 출력에서 상세한 로그 확인
- `view_test_results.py`로 특정 테스트 케이스 분석
- HTML 리포트에서 시각적 분석

## 📈 성능 최적화

- 대량 테스트 시 `test_results.json` 파일 크기 주의
- HTML 리포트는 브라우저에서 열어야 최적 성능
- 메모리 사용량은 테스트 케이스 수에 비례

## 🤝 기여하기

1. 새로운 테스트 케이스 추가
2. 기존 테스트 케이스 수정
3. 리포트 스타일 개선
4. 버그 리포트 및 수정

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. Python 버전 (3.7+ 권장)
2. 필요한 모듈 설치 여부
3. 파일 경로 및 권한
4. 콘솔 오류 메시지
