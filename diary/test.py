import math

class PolicyFundRecommender:
    def __init__(self):
        """정책자금 추천 시스템 초기화"""
        self.version = "2.1"
        
    def round_up_to_50m_unit_always(self, amount):
        """5천만원 단위로 무조건 상향 조정"""
        if amount <= 0:
            return 0
        unit = 50_000_000
        return ((int(amount) + unit - 1) // unit) * unit

    def calculate_kibo_max_limit(self, annual_revenue):
        """기보 최대 한도 계산"""
        revenue_based_limit = annual_revenue * 0.30
        minimum_limit = 100_000_000  # 1억원
        return max(revenue_based_limit, minimum_limit)

    def calculate_kibo(self, company_data):
        """기보 자금 계산 (증액 우선 원칙)"""
        # 데이터 추출 및 검증
        is_manufacturing_it = company_data.get('is_manufacturing_it', False)
        credit_score = company_data.get('credit_score', 0)
        career_years = company_data.get('career_years', 0)
        annual_revenue = company_data.get('annual_revenue', 0)
        existing_kibo_debt = company_data.get('existing_debt_kibo', 0)
        
        # 타입 안전성 확보
        try:
            credit_score = int(credit_score)
            career_years = int(career_years)
            annual_revenue = int(annual_revenue)
            existing_kibo_debt = int(existing_kibo_debt)
        except (ValueError, TypeError):
            return {
                'fund_name': '기보_일반보증',
                'limit': 0,
                'eligible': False,
                'reason': '데이터 타입 오류'
            }
        
        # 자격 요건 검토
        if not is_manufacturing_it:
            return {
                'fund_name': '기보_일반보증',
                'limit': 0,
                'eligible': False,
                'reason': '제조업/IT 아님'
            }
        
        credit_ok = (credit_score >= 800) or (career_years >= 15)
        if not credit_ok:
            return {
                'fund_name': '기보_일반보증',
                'limit': 0,
                'eligible': False,
                'reason': '신용점수 부족 & 경력 부족'
            }
        
        if career_years < 3:
            return {
                'fund_name': '기보_일반보증',
                'limit': 0,
                'eligible': False,
                'reason': '유관경력 3년 미만'
            }

        # 기보 최대 한도 계산
        max_kibo_limit = self.calculate_kibo_max_limit(annual_revenue)
        additional_limit = max_kibo_limit - existing_kibo_debt
        final_limit = self.round_up_to_50m_unit_always(additional_limit)
        
        # 자금 유형 결정
        is_existing_user = existing_kibo_debt > 0
        fund_type = '기보_증액' if is_existing_user else '기보_일반보증'
        
        return {
            'fund_name': fund_type,
            'limit': int(final_limit),
            'max_total_limit': int(max_kibo_limit),
            'existing_debt': int(existing_kibo_debt),
            'eligible': final_limit > 0
        }

    def calculate_shinbo(self, company_data):
        """신보 자금 계산 (기보 우선 후 차순위)"""
        # 데이터 추출
        company_age_months = company_data.get('company_age_months', 0)
        credit_score = company_data.get('credit_score', 0)
        annual_revenue = company_data.get('annual_revenue', 0)
        existing_debt_shinbo = company_data.get('existing_debt_shinbo', 0)
        is_manufacturing_it = company_data.get('is_manufacturing_it', False)
        
        # 타입 안전성 확보
        try:
            company_age_months = int(company_age_months)
            credit_score = int(credit_score)
            annual_revenue = int(annual_revenue)
            existing_debt_shinbo = int(existing_debt_shinbo)
        except (ValueError, TypeError):
            return {
                'fund_name': '신보',
                'limit': 0,
                'eligible': False,
                'reason': '데이터 타입 오류'
            }
        
        # 제조업/IT는 기보 우선 원칙
        if is_manufacturing_it:
            kibo_result = self.calculate_kibo(company_data)
            if kibo_result['eligible']:
                return {
                    'fund_name': '신보',
                    'limit': 0,
                    'eligible': False,
                    'reason': '제조업/IT는 기보 우선'
                }

        # 신보 자격 요건 검토
        if company_age_months < 3:
            return {
                'fund_name': '신보',
                'limit': 0,
                'eligible': False,
                'reason': '업력 3개월 미만'
            }
        
        if credit_score < 850:
            return {
                'fund_name': '신보',
                'limit': 0,
                'eligible': False,
                'reason': '신용점수 850점 미만'
            }

        # 한도 계산
        if annual_revenue >= 1_000_000_000 or credit_score >= 900:
            rate = 0.15
        else:
            rate = 0.12

        calculated_limit = (annual_revenue * rate) - existing_debt_shinbo
        final_limit = self.round_up_to_50m_unit_always(calculated_limit)

        return {
            'fund_name': '신보',
            'limit': int(final_limit),
            'eligible': final_limit > 0
        }

    def calculate_jungjincg_youth(self, company_data):
        """중진공 청년창업 자금"""
        # 데이터 추출 및 검증
        is_manufacturing_it = company_data.get('is_manufacturing_it', False)
        age = company_data.get('age', 0)
        company_age_months = company_data.get('company_age_months', 0)
        credit_score = company_data.get('credit_score', 0)
        career_years = company_data.get('career_years', 0)

        try:
            age = int(age)
            company_age_months = int(company_age_months)
            credit_score = int(credit_score)
            career_years = int(career_years)
        except (ValueError, TypeError):
            return {
                'fund_name': '중진공_청년창업',
                'limit': 0,
                'eligible': False,
                'reason': '데이터 타입 오류'
            }

        # 자격 요건 검토
        if not is_manufacturing_it:
            return {
                'fund_name': '중진공_청년창업',
                'limit': 0,
                'eligible': False,
                'reason': '제조업/IT 아님'
            }
        
        if age >= 40:
            return {
                'fund_name': '중진공_청년창업',
                'limit': 0,
                'eligible': False,
                'reason': '40세 이상'
            }
        
        company_age_ok = (company_age_months == 0) or (company_age_months <= 36)
        if not company_age_ok:
            return {
                'fund_name': '중진공_청년창업',
                'limit': 0,
                'eligible': False,
                'reason': '업력 3년 초과'
            }
        
        if credit_score < 800:
            return {
                'fund_name': '중진공_청년창업',
                'limit': 0,
                'eligible': False,
                'reason': '신용점수 800점 미만'
            }
        
        if career_years < 3:
            return {
                'fund_name': '중진공_청년창업',
                'limit': 0,
                'eligible': False,
                'reason': '유관경력 3년 미만'
            }
        
        return {
            'fund_name': '중진공_청년창업',
            'limit': 100_000_000,
            'eligible': True
        }

    def calculate_sojingong_innovation(self, company_data):
        """소진공 혁신성장 자금 (강화된 검증)"""
        # 데이터 추출
        employees = company_data.get('employees', 0)
        annual_revenue = company_data.get('annual_revenue', 0)
        credit_score = company_data.get('credit_score', 0)
        is_special_industry = company_data.get('is_special_employee_industry', False)

        # 타입 안전성 확보
        try:
            employees = int(employees)
            annual_revenue = int(annual_revenue)
            credit_score = int(credit_score)
            is_special_industry = bool(is_special_industry)
        except (ValueError, TypeError):
            return {
                'fund_name': '소진공_혁신성장',
                'limit': 0,
                'eligible': False,
                'reason': '데이터 타입 오류'
            }

        # 1. 직원수 조건 검토
        if is_special_industry:  # 제조업/건설업/운수업
            if employees >= 10:
                return {
                    'fund_name': '소진공_혁신성장',
                    'limit': 0,
                    'eligible': False,
                    'reason': f'직원수 초과 (특수업종 기준 10명, 현재: {employees}명)'
                }
        else:  # 일반 업종
            if employees >= 5:
                return {
                    'fund_name': '소진공_혁신성장',
                    'limit': 0,
                    'eligible': False,
                    'reason': f'직원수 초과 (일반업종 기준 5명, 현재: {employees}명)'
                }
        
        # 2. 매출 조건 검토 (핵심!)
        if annual_revenue < 200_000_000:
            return {
                'fund_name': '소진공_혁신성장',
                'limit': 0,
                'eligible': False,
                'reason': f'매출 부족 (필요: 2억원 이상, 현재: {annual_revenue:,}원)'
            }
        
        # 3. 신용점수 조건 검토
        if credit_score < 750:
            return {
                'fund_name': '소진공_혁신성장',
                'limit': 0,
                'eligible': False,
                'reason': f'신용점수 부족 (필요: 750점 이상, 현재: {credit_score}점)'
            }
        
        # 모든 조건 통과 시 한도 계산
        if annual_revenue >= 300_000_000 and credit_score >= 800:
            final_limit = 70_000_000
        else:
            final_limit = 50_000_000
        
        return {
            'fund_name': '소진공_혁신성장',
            'limit': int(final_limit),
            'eligible': True
        }

    def calculate_sojingong_low_credit(self, company_data):
        """소진공 저신용 자금"""
        # 데이터 추출
        employees = company_data.get('employees', 0)
        credit_score = company_data.get('credit_score', 0)
        is_special_industry = company_data.get('is_special_employee_industry', False)

        # 타입 안전성 확보
        try:
            employees = int(employees)
            credit_score = int(credit_score)
            is_special_industry = bool(is_special_industry)
        except (ValueError, TypeError):
            return {
                'fund_name': '소진공_저신용',
                'limit': 0,
                'eligible': False,
                'reason': '데이터 타입 오류'
            }

        # 직원수 조건 검토
        if is_special_industry:  # 제조업/건설업/운수업
            if employees >= 10:
                return {
                    'fund_name': '소진공_저신용',
                    'limit': 0,
                    'eligible': False,
                    'reason': f'직원수 초과 (특수업종 기준 10명, 현재: {employees}명)'
                }
        else:  # 일반 업종
            if employees >= 5:
                return {
                    'fund_name': '소진공_저신용',
                    'limit': 0,
                    'eligible': False,
                    'reason': f'직원수 초과 (일반업종 기준 5명, 현재: {employees}명)'
                }

        # 신용점수 조건 검토
        if credit_score > 839:
            return {
                'fund_name': '소진공_저신용',
                'limit': 0,
                'eligible': False,
                'reason': f'신용점수 초과 (839점 이하만 가능, 현재: {credit_score}점)'
            }
        
        return {
            'fund_name': '소진공_저신용',
            'limit': 30_000_000,
            'eligible': True
        }

    def calculate_shinbojaedan(self, company_data):
        """신용보증재단 자금"""
        # 데이터 추출
        credit_score = company_data.get('credit_score', 0)
        annual_revenue = company_data.get('annual_revenue', 0)

        # 타입 안전성 확보
        try:
            credit_score = int(credit_score)
            annual_revenue = int(annual_revenue)
        except (ValueError, TypeError):
            return {
                'fund_name': '신용보증재단',
                'limit': 0,
                'eligible': False,
                'reason': '데이터 타입 오류'
            }

        # 신용점수별 기본한도
        if credit_score >= 900:
            base_limit = 50_000_000
        elif credit_score >= 850:
            base_limit = 30_000_000
        elif credit_score >= 800:
            base_limit = 25_000_000
        elif credit_score >= 750:
            base_limit = 20_000_000
        elif credit_score >= 700:
            base_limit = 15_000_000
        else:
            base_limit = 10_000_000

        final_limit = base_limit

        # 매출 연동 우대 적용
        if annual_revenue >= 1_500_000_000:
            final_limit = 50_000_000
        elif annual_revenue >= 1_000_000_000 and credit_score >= 850:
            final_limit = 50_000_000
        elif annual_revenue >= 1_000_000_000:
            return {
                'fund_name': '신용보증재단',
                'limit': '상담필요',
                'special_note': '3천~5천만원',
                'eligible': True
            }

        return {
            'fund_name': '신용보증재단',
            'limit': int(final_limit),
            'eligible': final_limit > 0
        }

    def recommend_funds(self, company_data):
        """전체 자금 추천 (한도 크기순 정렬 + 단순 넘버링)"""
        eligible_funds = []
        
        # 1. 주력 보증기관: 기보 vs 신보 (배타적 관계)
        kibo_result = self.calculate_kibo(company_data)
        
        # 제조업/IT 절대 우선 + 기보 증액 우선 원칙
        if company_data.get('is_manufacturing_it', False) and kibo_result['eligible']:
            eligible_funds.append(kibo_result)
        else:
            shinbo_result = self.calculate_shinbo(company_data)
            if shinbo_result['eligible']:
                eligible_funds.append(shinbo_result)
            
        # 2. 중진공 청년창업 (기보와 중복 가능)
        jungjin_result = self.calculate_jungjincg_youth(company_data)
        if jungjin_result['eligible']:
            eligible_funds.append(jungjin_result)

        # 3. 소진공 자금 (모든 자금과 중복 가능)
        sojin_innovation = self.calculate_sojingong_innovation(company_data)
        sojin_low_credit = self.calculate_sojingong_low_credit(company_data)

        if sojin_innovation['eligible']:
            eligible_funds.append(sojin_innovation)
        elif sojin_low_credit['eligible']:
            eligible_funds.append(sojin_low_credit)

        # 4. 신용보증재단 (기보/신보와 중복 가능)
        jaedan_result = self.calculate_shinbojaedan(company_data)
        if jaedan_result['eligible']:
            eligible_funds.append(jaedan_result)

        # 핵심 변경: 한도 큰 순서로 정렬 (내림차순)
        def get_sort_key(fund):
            limit = fund.get('limit', 0)
            # '상담필요'인 경우 4천만원으로 처리하여 적절한 위치에 정렬
            if limit == '상담필요':
                return 40_000_000
            return limit if isinstance(limit, int) else 0
        
        eligible_funds.sort(key=get_sort_key, reverse=True)
        
        # 단순 넘버링 (가능자금1, 가능자금2, ...)
        final_recommendations = []
        for i, fund in enumerate(eligible_funds, 1):
            fund['fund_label'] = f'가능자금{i}'
            final_recommendations.append(fund)
        
        return final_recommendations

    def get_total_funding_amount(self, recommendations):
        """총 조달 가능 금액 계산"""
        total = 0
        for rec in recommendations:
            limit = rec.get('limit', 0)
            if isinstance(limit, int):
                total += limit
            elif limit == '상담필요':
                total += 40_000_000  # 상담필요는 4천만원으로 계산
        return total


# 사용 예시 및 테스트
def test_system():
    """시스템 테스트 함수"""
    recommender = PolicyFundRecommender()
    
    # 테스트 케이스 1: 고매출 제조업 (기보 증액)
    test_case1 = {
        'annual_revenue': 4_500_000_000,    # 45억
        'existing_debt_kibo': 150_000_000,  # 기존 1.5억
        'existing_debt_shinbo': 0,
        'credit_score': 890,
        'is_manufacturing_it': True,
        'career_years': 18,
        'age': 45,
        'employees': 25
    }
    
    print("=== 테스트 케이스 1: 고매출 제조업 ===")
    results1 = recommender.recommend_funds(test_case1)
    for result in results1:
        limit_str = f"{result['limit']:,}원" if isinstance(result['limit'], int) else result['limit']
        print(f"{result['fund_label']}: {result['fund_name']} - {limit_str}")
    
    total1 = recommender.get_total_funding_amount(results1)
    print(f"총 조달 가능: {total1:,}원\n")
    
    # 테스트 케이스 2: 매출 0원 서비스업
    test_case2 = {
        'annual_revenue': 0,
        'existing_debt_kibo': 0,
        'existing_debt_shinbo': 0,
        'credit_score': 826,
        'is_manufacturing_it': False,
        'employees': 0,
        'is_special_employee_industry': False,
        'company_age_months': 1,
        'age': 35,
        'career_years': 5
    }
    
    print("=== 테스트 케이스 2: 매출 0원 서비스업 ===")
    results2 = recommender.recommend_funds(test_case2)
    for result in results2:
        limit_str = f"{result['limit']:,}원" if isinstance(result['limit'], int) else result['limit']
        print(f"{result['fund_label']}: {result['fund_name']} - {limit_str}")
    
    total2 = recommender.get_total_funding_amount(results2)
    print(f"총 조달 가능: {total2:,}원")


if __name__ == "__main__":
    test_system()
