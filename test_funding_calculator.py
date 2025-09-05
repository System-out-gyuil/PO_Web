#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정책자금 추천 엔진 테스트 스크립트
30개 테스트 케이스를 funding_calculator.py 양식에 맞춰 변환하여 검증
"""

from diary.funding_calculator import PolicyFundRecommendationEngineV2
from datetime import datetime
import json

def convert_test_data_to_calculator_format(test_data):
    """
    테스트 데이터를 funding_calculator.py 양식으로 변환
    """
    data = test_data['data']
    
    # 업종 변환
    if data.get('is_manufacturing_it', False):
        industry = '제조업' if 'manufacturing' in str(data.get('is_manufacturing_it', False)) else '정보통신업'
    else:
        industry = '전문, 과학 및 기술 서비스업'  # 기본값
    
    # 기존 자금 사용 현황 변환
    existing_funds = {
        'kibo_general': data.get('existing_debt_kibo', 0),
        'kibo_ip': 0,  # IP보증은 별도 관리
        'sinbo': data.get('existing_debt_shinbo', 0),
        'jungjin': 0,  # 중진공은 별도 관리
        'sojin_innovation': 0,  # 소진공 혁신성장
        'sojin_lowcredit': 0,  # 소진공 저신용
        'credit_foundation': data.get('existing_debt_jaedan', 0)
    }
    
    # 개업일로부터 업력 계산
    opening_date = data.get('opening_date', '2022-01-01')
    if isinstance(opening_date, str):
        try:
            opening_dt = datetime.strptime(opening_date, '%Y-%m-%d')
            current_dt = datetime.now()
            business_months = (current_dt.year - opening_dt.year) * 12 + (current_dt.month - opening_dt.month)
        except:
            business_months = 24  # 기본값
    else:
        business_months = 24
    
    # 스타트업 여부 판단 (업력 3년 이하)
    is_startup = business_months <= 36
    
    # 변환된 데이터
    converted_data = {
        'credit_score': data.get('credit_score', 0),
        'industry': industry,
        'annual_revenue': data.get('annual_revenue', 0),
        'employees': data.get('employees', 3),
        'business_months': business_months,
        'ceo_age': data.get('age', 35),
        'experience_years': data.get('career_years', 5),
        'is_startup': is_startup,
        'existing_debt': sum(existing_funds.values()),
        'existing_funds': existing_funds
    }
    
    return converted_data

def run_single_test(test_case, calculator):
    """
    단일 테스트 케이스 실행
    """
    print(f"\n{'='*80}")
    print(f"테스트 ID: {test_case['id']}")
    print(f"설명: {test_case['description']}")
    print(f"테스트 포커스: {test_case['test_focus']}")
    print(f"{'='*80}")
    
    # 원본 데이터 표시
    print(f"\n📋 원본 테스트 데이터:")
    for key, value in test_case['data'].items():
        if isinstance(value, int) and value > 1000000:
            print(f"  {key}: {value:,}원 ({value//100000000}억원)")
        elif isinstance(value, int):
            print(f"  {key}: {value:,}")
        else:
            print(f"  {key}: {value}")
    
    # 데이터 변환
    converted_data = convert_test_data_to_calculator_format(test_case)
    print(f"\n🔄 변환된 데이터:")
    for key, value in converted_data.items():
        if key == 'existing_funds':
            print(f"  {key}:")
            for fund_key, fund_value in value.items():
                if fund_value > 0:
                    print(f"    {fund_key}: {fund_value:,}원")
        elif isinstance(value, int) and value > 1000000:
            print(f"  {key}: {value:,}원 ({value//100000000}억원)")
        elif isinstance(value, int):
            print(f"  {key}: {value:,}")
        else:
            print(f"  {key}: {value}")
    
    # 추천 실행
    result = calculator.recommend_funds(converted_data)
    
    # 결과 분석
    if 'error' in result:
        print(f"\n❌ 오류 발생: {result['error']}")
        return {
            'test_id': test_case['id'],
            'status': 'ERROR',
            'description': test_case['description'],
            'test_focus': test_case['test_focus'],
            'input_conditions': {
                'original_data': test_case['data'],
                'converted_data': converted_data
            },
            'results': {
                'expected': test_case['expected_results'],
                'actual': [],
                'total_amount': 0,
                'funds_count': 0
            },
            'comparison': {
                'is_match': False,
                'only_expected': test_case['expected_results'],
                'only_actual': []
            },
            'error': result['error']
        }
    
    # 추천된 자금들 정리
    recommended_funds = result.get('recommended_funds', [])
    actual_results = []
    
    for fund in recommended_funds:
        fund_name = fund['fund_name']
        limit = fund['limit']
        
        # 금리 정보 추가 (있는 경우)
        interest_rate = fund.get('interest_rate', '')
        if interest_rate and '2.5%' in interest_rate:
            actual_results.append(f"{fund_name} ({limit//10000000}천만원-금리{interest_rate})")
        else:
            actual_results.append(f"{fund_name} ({limit//10000000}천만원)")
    
    # 결과 비교 표시
    print(f"\n📊 결과 비교:")
    print(f"{'─'*40} 예상 결과 {'─'*40}")
    for i, expected in enumerate(test_case['expected_results'], 1):
        print(f"  {i:2d}. {expected}")
    
    print(f"{'─'*40} 실제 결과 {'─'*40}")
    for i, actual in enumerate(actual_results, 1):
        print(f"  {i:2d}. {actual}")
    
    # 결과 비교
    expected_set = set(test_case['expected_results'])
    actual_set = set(actual_results)
    
    if expected_set == actual_set:
        print(f"\n✅ 테스트 통과")
        status = 'PASS'
    else:
        print(f"\n❌ 테스트 실패")
        print(f"{'─'*40} 차이점 분석 {'─'*40}")
        only_expected = expected_set - actual_set
        only_actual = actual_set - expected_set
        
        if only_expected:
            print(f"  🔴 예상에만 있음 ({len(only_expected)}개):")
            for item in only_expected:
                print(f"    • {item}")
        
        if only_actual:
            print(f"  🔵 실제에만 있음 ({len(only_actual)}개):")
            for item in only_actual:
                print(f"    • {item}")
        
        status = 'FAIL'
    
    # 총 금액 표시
    total_amount = result.get('total_additional_amount', 0)
    print(f"\n💰 총 추천 금액: {total_amount:,}원 ({total_amount//100000000}억원)")
    
    return {
        'test_id': test_case['id'],
        'status': status,
        'description': test_case['description'],
        'test_focus': test_case['test_focus'],
        'input_conditions': {
            'original_data': test_case['data'],
            'converted_data': converted_data
        },
        'results': {
            'expected': test_case['expected_results'],
            'actual': actual_results,
            'total_amount': total_amount,
            'funds_count': len(recommended_funds)
        },
        'comparison': {
            'is_match': expected_set == actual_set,
            'only_expected': list(expected_set - actual_set) if expected_set != actual_set else [],
            'only_actual': list(actual_set - expected_set) if expected_set != actual_set else []
        }
    }

def main():
    """
    메인 테스트 실행 함수
    """
    print("정책자금 추천 엔진 테스트 시작")
    print("="*60)
    
    # 계산기 초기화
    calculator = PolicyFundRecommendationEngineV2()
    
    # 테스트 케이스 정의
    test_samples = [
        # === 그룹 A: 제조업/IT 기보 중심 (1-10번) ===
        {
            'id': 'TEST_001',
            'description': '소규모 제조업 - 기보 최소 1억원 보장 테스트',
            'data': {
                'annual_revenue': 80_000_000,       # 0.8억 (20% = 1,600만원)
                'credit_score': 820,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2022-03-15',
                'age': 42,
                'career_years': 8,
                'employees': 3,
                'is_special_employee_industry': True
            },
            'expected_results': ['기보_일반보증 (1천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '기보 최소 1억원 보장 (계산값 1,600만원 → 1억원)'
        },
        {
            'id': 'TEST_002',
            'description': '중간규모 제조업 - 기보 20% 기준 적용',
            'data': {
                'annual_revenue': 800_000_000,      # 8억 (20% = 1.6억)
                'credit_score': 850,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2020-06-10',
                'age': 38,
                'career_years': 8,
                'employees': 8,
                'is_special_employee_industry': True
            },
            'expected_results': ['기보_일반보증 (2천만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (3천만원)'],
            'test_focus': '기보 20% 계산 (8억 × 20% = 1.6억 → 2억원 상향)'
        },
        {
            'id': 'TEST_003',
            'description': '고매출 제조업 - 기보 증액 우선 원칙',
            'data': {
                'annual_revenue': 3_000_000_000,    # 30억 (20% = 6억)
                'credit_score': 880,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 200_000_000,  # 기존 2억
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2018-01-20',
                'age': 48,
                'career_years': 15,
                'employees': 25,
                'is_special_employee_industry': True
            },
            'expected_results': ['기보_일반보증_증액 (4천만원)', '신용보증재단 (5천만원)'],
            'test_focus': '기보 증액 우선 (총한도 6억 - 기대출 2억 = 4억)'
        },
        {
            'id': 'TEST_004',
            'description': '청년 제조업 창업 - 복합 자금 활용',
            'data': {
                'annual_revenue': 400_000_000,      # 4억 (20% = 8천만원)
                'credit_score': 830,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2023-03-01',
                'age': 32,
                'career_years': 6,
                'employees': 4,
                'is_special_employee_industry': True
            },
            'expected_results': ['중진공_청년창업 (1천만원)', '기보_일반보증 (1천만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '복합 자금 + 중진공 금리 2.5% 표시'
        },
        {
            'id': 'TEST_005',
            'description': 'IT기업 - 기보 대상업종 확인',
            'data': {
                'annual_revenue': 1_200_000_000,    # 12억 (20% = 2.4억)
                'credit_score': 890,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2021-09-15',
                'age': 35,
                'career_years': 8,
                'employees': 7,
                'is_special_employee_industry': False
            },
            'expected_results': ['기보_일반보증 (2천5백만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (5천만원)'],
            'test_focus': 'IT업종 기보 적용 + 20% 계산'
        },
        {
            'id': 'TEST_006',
            'description': '저신용 제조업 - 경력으로 신용 보완',
            'data': {
                'annual_revenue': 500_000_000,      # 5억
                'credit_score': 720,                # 800점 미만
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2019-05-20',
                'age': 55,
                'career_years': 25,                 # 15년 이상으로 보완
                'employees': 6,
                'is_special_employee_industry': True
            },
            'expected_results': ['기보_일반보증 (1천만원)', '신용보증재단 (1천5백만원)'],
            'test_focus': '경력 25년으로 신용점수 720점 보완'
        },
        {
            'id': 'TEST_007',
            'description': '예비창업 제조업 - 매출 0원 케이스',
            'data': {
                'annual_revenue': 0,
                'credit_score': 850,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2024-11-01',
                'age': 28,
                'career_years': 5,
                'employees': 0,
                'is_special_employee_industry': True
            },
            'expected_results': ['중진공_청년창업 (1천만원)', '기보_일반보증 (1천만원)', '소진공_저신용 (3천만원)', '신용보증재단 (3천만원)'],
            'test_focus': '매출 0원에서 기보 최소 1억원 보장'
        },
        {
            'id': 'TEST_008',
            'description': '대형 제조업 - 기보 한도 최대 활용',
            'data': {
                'annual_revenue': 5_000_000_000,    # 50억 (20% = 10억)
                'credit_score': 920,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2015-01-01',
                'age': 48,
                'career_years': 22,
                'employees': 45,
                'is_special_employee_industry': True
            },
            'expected_results': ['기보_일반보증 (10천만원)', '신용보증재단 (5천만원)'],
            'test_focus': '기보 최대 한도 (50억 × 20% = 10억원)'
        },
        {
            'id': 'TEST_009',
            'description': '기보 자격 미달 - 경력 부족',
            'data': {
                'annual_revenue': 300_000_000,
                'credit_score': 750,                # 800점 미만
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2023-08-01',
                'age': 30,
                'career_years': 2,                  # 3년 미만
                'employees': 3,
                'is_special_employee_industry': True
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단 (2천만원)'],
            'test_focus': '제조업이지만 기보 자격 미달시 다른 자금 추천'
        },
        {
            'id': 'TEST_010',
            'description': '기보 기대출 초과 - 신보 전환 방지 테스트',
            'data': {
                'annual_revenue': 300_000_000,      # 3억 (20% = 6천만원, 최소 1억)
                'credit_score': 850,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 200_000_000,  # 기대출 2억 (한도 초과)
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2021-01-01',
                'age': 40,
                'career_years': 10,
                'employees': 4,
                'is_special_employee_industry': True
            },
            'expected_results': ['신보_일반보증 (5천만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '기보 한도 초과시 신보 전환 (제조업 예외)'
        },

        # === 그룹 B: 서비스업 신보 중심 (11-18번) ===
        {
            'id': 'TEST_011',
            'description': '고매출 서비스업 - 신보 15% 요율',
            'data': {
                'annual_revenue': 2_000_000_000,    # 20억
                'credit_score': 920,                # 900점 이상
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2019-03-01',
                'age': 45,
                'career_years': 15,
                'employees': 12,
                'is_special_employee_industry': False
            },
            'expected_results': ['신보_일반보증 (30천만원)', '신용보증재단 (5천만원)'],
            'test_focus': '신보 15% 요율 (20억 × 15% = 3억)'
        },
        {
            'id': 'TEST_012',
            'description': '중간 서비스업 - 신보 12% 요율',
            'data': {
                'annual_revenue': 800_000_000,      # 8억
                'credit_score': 870,                # 900점 미만
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2021-06-15',
                'age': 38,
                'career_years': 8,
                'employees': 6,
                'is_special_employee_industry': False
            },
            'expected_results': ['신보_일반보증 (10천만원)', '신용보증재단 (3천만원)'],
            'test_focus': '신보 12% 요율 (8억 × 12% = 9,600만원 → 1억원)'
        },
        {
            'id': 'TEST_013',
            'description': '신보 기대출 보유 - 증액 케이스',
            'data': {
                'annual_revenue': 1_200_000_000,    # 12억
                'credit_score': 890,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 80_000_000, # 기존 8천만원
                'existing_debt_jaedan': 0,
                'opening_date': '2018-09-01',
                'age': 42,
                'career_years': 12,
                'employees': 8,
                'is_special_employee_industry': False
            },
            'expected_results': ['신보_증액 (10천만원)', '신용보증재단 (5천만원)'],
            'test_focus': '신보 증액 (12억×15%-8천만원=1억원)'
        },
        {
            'id': 'TEST_014',
            'description': '신보 자격 미달 - 신용점수 부족',
            'data': {
                'annual_revenue': 600_000_000,      # 6억
                'credit_score': 840,                # 850점 미만
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2020-04-01',
                'age': 35,
                'career_years': 8,
                'employees': 4,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '신보 불가시 소진공으로 전환'
        },
        {
            'id': 'TEST_015',
            'description': '신보 자격 미달 - 업력 부족',
            'data': {
                'annual_revenue': 400_000_000,      # 4억
                'credit_score': 880,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2024-10-01',       # 업력 1개월
                'age': 40,
                'career_years': 10,
                'employees': 3,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단 (3천만원)'],
            'test_focus': '신보 업력 부족시 소진공으로 전환'
        },
        {
            'id': 'TEST_016',
            'description': '건설업 - 특수업종 직원수 기준',
            'data': {
                'annual_revenue': 1_500_000_000,    # 15억
                'credit_score': 860,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2019-07-01',
                'age': 48,
                'career_years': 18,
                'employees': 8,                     # 특수업종 10명 미만
                'is_special_employee_industry': True
            },
            'expected_results': ['신보_일반보증 (22천5백만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (5천만원)'],
            'test_focus': '건설업 특수업종 직원수 기준 (10명 미만)'
        },
        {
            'id': 'TEST_017',
            'description': '운수업 - 특수업종 + 소진공',
            'data': {
                'annual_revenue': 800_000_000,      # 8억
                'credit_score': 880,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2020-02-01',
                'age': 45,
                'career_years': 15,
                'employees': 9,                     # 특수업종 10명 미만
                'is_special_employee_industry': True
            },
            'expected_results': ['신보_일반보증 (10천만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (3천만원)'],
            'test_focus': '운수업 특수업종 + 소진공 복합'
        },
        {
            'id': 'TEST_018',
            'description': '대표님 제시 사례 - 전문과학및기술서비스업',
            'data': {
                'annual_revenue': 300_000_000,      # 3억
                'credit_score': 838,                # 신보 불가
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 20_000_000, # 재단 2천만원
                'opening_date': '2022-01-01',
                'age': 42,
                'career_years': 12,
                'employees': 3,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단 (5백만원)'],
            'test_focus': '대표님 사례 검증 (재단 기대출 차감)'
        },

        # === 그룹 C: 소진공 특화 (19-25번) ===
        {
            'id': 'TEST_019',
            'description': '소진공 혁신성장 고한도 - 매출 3억 이상',
            'data': {
                'annual_revenue': 350_000_000,      # 3.5억
                'credit_score': 820,                # 800점 이상
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2021-05-01',
                'age': 35,
                'career_years': 8,
                'employees': 3,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '소진공 고한도 조건 (매출 3억 이상 + 신용 800점 이상)'
        },
        {
            'id': 'TEST_020',
            'description': '소진공 혁신성장 일반한도',
            'data': {
                'annual_revenue': 280_000_000,      # 2.8억
                'credit_score': 780,                # 800점 미만
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2020-08-01',
                'age': 40,
                'career_years': 10,
                'employees': 4,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (5천만원)', '신용보증재단 (2천만원)'],
            'test_focus': '소진공 일반한도 (조건 미달시 5천만원)'
        },
        {
            'id': 'TEST_021',
            'description': '소진공 저신용 케이스',
            'data': {
                'annual_revenue': 180_000_000,      # 1.8억 (2억 미만)
                'credit_score': 680,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2022-06-01',
                'age': 45,
                'career_years': 12,
                'employees': 2,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_저신용 (3천만원)', '신용보증재단 (1천5백만원)'],
            'test_focus': '소진공 저신용 (매출 2억 미만 + 신용 839점 이하)'
        },
        {
            'id': 'TEST_022',
            'description': '소진공 직원수 초과 - 일반업종',
            'data': {
                'annual_revenue': 400_000_000,      # 4억
                'credit_score': 800,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2019-01-01',
                'age': 42,
                'career_years': 15,
                'employees': 6,                     # 5명 초과
                'is_special_employee_industry': False
            },
            'expected_results': ['신용보증재단 (2천5백만원)'],
            'test_focus': '소진공 직원수 초과시 재단만 가능'
        },
        {
            'id': 'TEST_023',
            'description': '소진공 매출 부족 케이스',
            'data': {
                'annual_revenue': 150_000_000,      # 1.5억 (2억 미만)
                'credit_score': 800,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2021-01-01',
                'age': 35,
                'career_years': 8,
                'employees': 3,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_저신용 (3천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '소진공 혁신성장 매출 부족시 저신용으로 전환'
        },
        {
            'id': 'TEST_024',
            'description': '혁신성장 vs 저신용 선택 로직',
            'data': {
                'annual_revenue': 300_000_000,      # 3억
                'credit_score': 839,                # 저신용 경계값
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2022-01-01',
                'age': 40,
                'career_years': 8,
                'employees': 4,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '혁신성장 가능시 저신용 제외 (elif 구조)'
        },
        {
            'id': 'TEST_025',
            'description': '특수업종 직원수 경계 테스트',
            'data': {
                'annual_revenue': 500_000_000,      # 5억
                'credit_score': 800,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2020-01-01',
                'age': 45,
                'career_years': 12,
                'employees': 10,                    # 특수업종 경계값
                'is_special_employee_industry': True
            },
            'expected_results': ['신용보증재단 (2천5백만원)'],
            'test_focus': '특수업종 직원수 10명 경계값 (10명 이상시 소진공 불가)'
        },

        # === 그룹 D: 경계값 및 특수 케이스 (26-30번) ===
        {
            'id': 'TEST_026',
            'description': '매출 0원 서비스업 - 예비창업',
            'data': {
                'annual_revenue': 0,
                'credit_score': 826,
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2024-11-01',
                'age': 35,
                'career_years': 5,
                'employees': 0,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_저신용 (3천만원)', '신용보증재단 (2천5백만원)'],
            'test_focus': '매출 0원 서비스업 (소진공 혁신성장 매출 부족)'
        },
        {
            'id': 'TEST_027',
            'description': '신용보증재단 상담필요 케이스',
            'data': {
                'annual_revenue': 1_200_000_000,    # 12억 (10억 이상)
                'credit_score': 820,                # 850점 미만
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2020-01-01',
                'age': 45,
                'career_years': 15,
                'employees': 8,
                'is_special_employee_industry': False
            },
            'expected_results': ['소진공_혁신성장 (7천만원)', '신용보증재단_매출우대상담 (3천만원)'],
            'test_focus': '재단 상담필요 조건 (매출 10억 이상 + 신용 850점 미만)'
        },
        {
            'id': 'TEST_028',
            'description': '복합 기대출 보유 케이스',
            'data': {
                'annual_revenue': 1_000_000_000,    # 10억 (20% = 2억)
                'credit_score': 880,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 150_000_000,  # 기보 1.5억
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 30_000_000, # 재단 3천만원
                'opening_date': '2018-03-01',
                'age': 40,
                'career_years': 12,
                'employees': 8,
                'is_special_employee_industry': True
            },
            'expected_results': ['기보_일반보증_증액 (5천만원)', '신용보증재단 (2천만원)'],
            'test_focus': '복합 기대출 보유시 각각 차감 계산'
        },
        {
            'id': 'TEST_029',
            'description': '신용점수 850점 경계 케이스',
            'data': {
                'annual_revenue': 500_000_000,      # 5억
                'credit_score': 850,                # 정확히 850점
                'is_manufacturing_it': False,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2021-01-01',
                'age': 38,
                'career_years': 10,
                'employees': 4,
                'is_special_employee_industry': False
            },
            'expected_results': ['신보_일반보증 (5천만원)', '소진공_혁신성장 (5천만원)', '신용보증재단 (3천만원)'],
            'test_focus': '신보 신용점수 850점 경계값 (이상시 신보 가능)'
        },
        {
            'id': 'TEST_030',
            'description': '모든 조건 만족 - 최대 복합 자금',
            'data': {
                'annual_revenue': 400_000_000,      # 4억
                'credit_score': 900,
                'is_manufacturing_it': True,
                'existing_debt_kibo': 0,
                'existing_debt_shinbo': 0,
                'existing_debt_jaedan': 0,
                'opening_date': '2022-01-01',
                'age': 35,
                'career_years': 8,
                'employees': 4,
                'is_special_employee_industry': True
            },
            'expected_results': ['중진공_청년창업 (1천만원)', '기보_일반보증 (1천만원)', '소진공_혁신성장 (7천만원)', '신용보증재단 (5천만원)'],
            'test_focus': '모든 조건 만족시 최대 복합 자금 (총 3억2천만원)'
        }
    ]
    
    # 테스트 실행
    results = []
    pass_count = 0
    fail_count = 0
    error_count = 0
    
    for test_case in test_samples:
        try:
            result = run_single_test(test_case, calculator)
            results.append(result)
            
            if result['status'] == 'PASS':
                pass_count += 1
            elif result['status'] == 'FAIL':
                fail_count += 1
            elif result['status'] == 'ERROR':
                error_count += 1
                
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {test_case['id']} - {str(e)}")
            error_count += 1
            results.append({
                'test_id': test_case['id'],
                'status': 'ERROR',
                'description': test_case['description'],
                'test_focus': test_case['test_focus'],
                'input_conditions': {
                    'original_data': test_case['data'],
                    'converted_data': {}
                },
                'results': {
                    'expected': test_case['expected_results'],
                    'actual': [],
                    'total_amount': 0,
                    'funds_count': 0
                },
                'comparison': {
                    'is_match': False,
                    'only_expected': test_case['expected_results'],
                    'only_actual': []
                },
                'error': str(e)
            })
    
    # 최종 결과 리포트
    print(f"\n{'='*80}")
    print("🎯 테스트 결과 요약")
    print(f"{'='*80}")
    print(f"📊 총 테스트 수: {len(test_samples)}")
    print(f"✅ 통과: {pass_count} ({(pass_count/len(test_samples)*100):.1f}%)")
    print(f"❌ 실패: {fail_count} ({(fail_count/len(test_samples)*100):.1f}%)")
    print(f"⚠️ 오류: {error_count} ({(error_count/len(test_samples)*100):.1f}%)")
    
    # 그룹별 결과 분석
    print(f"\n{'='*80}")
    print("📈 그룹별 결과 분석")
    print(f"{'='*80}")
    
    group_a_results = [r for r in results if r['test_id'].startswith('TEST_00') and int(r['test_id'][-2:]) <= 10]
    group_b_results = [r for r in results if r['test_id'].startswith('TEST_0') and 11 <= int(r['test_id'][-2:]) <= 18]
    group_c_results = [r for r in results if r['test_id'].startswith('TEST_0') and 19 <= int(r['test_id'][-2:]) <= 25]
    group_d_results = [r for r in results if r['test_id'].startswith('TEST_0') and 26 <= int(r['test_id'][-2:]) <= 30]
    
    groups = [
        ("그룹 A: 제조업/IT 기보 중심", group_a_results),
        ("그룹 B: 서비스업 신보 중심", group_b_results),
        ("그룹 C: 소진공 특화", group_c_results),
        ("그룹 D: 경계값 및 특수 케이스", group_d_results)
    ]
    
    for group_name, group_results in groups:
        if group_results:
            group_pass = len([r for r in group_results if r['status'] == 'PASS'])
            group_total = len(group_results)
            print(f"  {group_name}: {group_pass}/{group_total} 통과 ({(group_pass/group_total*100):.1f}%)")
    
    # 실패 케이스 상세 리포트
    if fail_count > 0 or error_count > 0:
        print(f"\n{'='*80}")
        print("🔍 실패/오류 케이스 상세 분석")
        print(f"{'='*80}")
        
        for result in results:
            if result['status'] in ['FAIL', 'ERROR']:
                print(f"\n{'─'*60}")
                print(f"테스트 ID: {result['test_id']}")
                print(f"설명: {result.get('description', 'N/A')}")
                print(f"테스트 포커스: {result.get('test_focus', 'N/A')}")
                print(f"상태: {result['status']}")
                
                if 'error' in result:
                    print(f"오류: {result['error']}")
                else:
                    print(f"예상 결과:")
                    for i, expected in enumerate(result['results']['expected'], 1):
                        print(f"  {i:2d}. {expected}")
                    
                    print(f"실제 결과:")
                    for i, actual in enumerate(result['results']['actual'], 1):
                        print(f"  {i:2d}. {actual}")
                    
                    # 차이점 분석
                    expected_set = set(result['results']['expected'])
                    actual_set = set(result['results']['actual'])
                    only_expected = expected_set - actual_set
                    only_actual = actual_set - expected_set
                    
                    if only_expected:
                        print(f"🔴 예상에만 있음: {list(only_expected)}")
                    if only_actual:
                        print(f"🔵 실제에만 있음: {list(only_actual)}")
    
    # JSON 결과 저장
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("💾 상세 결과가 test_results.json에 저장되었습니다.")
    print("📁 파일 위치: test_results.json")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
