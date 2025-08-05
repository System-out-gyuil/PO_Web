import math
from datetime import date, datetime

class PolicyFundRecommender:
    def __init__(self):
        """정책자금 추천 시스템 초기화"""
        self.version = "2.2"
        
    def round_up_to_50m_unit_always(self, amount):
        """5천만원 단위로 무조건 상향 조정 (기보 제외 모든 자금)"""
        if amount <= 0:
            return 0
        unit = 50_000_000
        return ((int(amount) + unit - 1) // unit) * unit

    def calculate_kibo_max_limit(self, annual_revenue):
        """기보 최대 한도 계산 (20% 기준으로 변경)"""
        revenue_based_limit = annual_revenue * 0.20  # 30% → 20%로 변경
        minimum_limit = 100_000_000  # 1억원
        return max(revenue_based_limit, minimum_limit)

    def ensure_kibo_minimum_100m(self, calculated_limit):
        """기보 최소 1억원 보장 함수 (핵심 추가)"""
        if calculated_limit > 0 and calculated_limit < 100_000_000:
            return 100_000_000  # 1억원 미만이면 1억원으로 보정
        return calculated_limit

    def calculate_company_age_months(self, opening_date_str):
        """개업일로부터 업력(개월) 계산"""
        try:
            if isinstance(opening_date_str, str):
                # 다양한 날짜 형식 지원
                if '년' in opening_date_str:
                    opening_date = datetime.strptime(opening_date_str, '%Y년%m월%d일').date()
                else:
                    opening_date = datetime.strptime(opening_date_str, '%Y-%m-%d').date()
            elif isinstance(opening_date_str, date):
                opening_date = opening_date_str
            else:
                return 0
            
            today = date.today()
            months = (today.year - opening_date.year) * 12 + (today.month - opening_date.month)
            return max(0, months)
        except:
            return 0

    def calculate_kibo(self, company_data):
        """기보 자금 계산 (수정된 20% 기준 + 최소 1억원 보장)"""
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

        # 기보 최대 한도 계산 (20% 기준)
        max_kibo_limit = self.calculate_kibo_max_limit(annual_revenue)
        additional_limit = max_kibo_limit - existing_kibo_debt
        
        # 5천만원 단위 상향 조정 (기존 로직 유지)
        limit_after_rounding = self.round_up_to_50m_unit_always(additional_limit)
        
        # 핵심 추가: 최소 1억원 보장
        final_limit = self.ensure_kibo_minimum_100m(limit_after_rounding)
        
        # 자금 유형 결정
        is_existing_user = existing_kibo_debt > 0
        fund_type = '기보_증액' if is_existing_user else '기보_일반보증'
        
        return {
            'fund_name': fund_type,
            'limit': int(final_limit),
            'max_total_limit': int(max_kibo_limit),
            'existing_debt': int(existing_kibo_debt),
            'eligible': final_limit > 0,
            'calculation_detail': f'매출 {annual_revenue:,}원 × 20% = {annual_revenue * 0.20:,.0f}원, 최소 1억원 보장 적용'
        }

    def calculate_shinbo(self, company_data):
        """신보 자금 계산 (기보 우선 후 차순위)"""
        # 데이터 추출
        company_age_months = company_data.get('company_age_months', 0)
        credit_score = company_data.get('credit_score', 0)
        annual_revenue = company_data.get('annual_revenue', 0)
        existing_debt_shinbo = company_data.get('existing_debt_shinbo', 0)
        is_manufacturing_it = company_data.get('is_manufacturing_it', False)
        
        # 개업일 정보가 있으면 업력 자동 계산
        opening_date = company_data.get('opening_date')
        if opening_date and company_age_months == 0:
            company_age_months = self.calculate_company_age_months(opening_date)
        
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
        """중진공 청년창업 자금 (금리 2.5% 정보 추가)"""
        # 데이터 추출 및 검증
        is_manufacturing_it = company_data.get('is_manufacturing_it', False)
        age = company_data.get('age', 0)
        company_age_months = company_data.get('company_age_months', 0)
        credit_score = company_data.get('credit_score', 0)
        career_years = company_data.get('career_years', 0)
        
        # 개업일 정보가 있으면 업력 자동 계산
        opening_date = company_data.get('opening_date')
        if opening_date and company_age_months == 0:
            company_age_months = self.calculate_company_age_months(opening_date)

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
            'eligible': True,
            'interest_rate': '연 2.5%',  # 금리 정보 추가
            'special_benefit': '청년창업 우대금리'
        }

    def calculate_sojingong_innovation(self, company_data):
        """소진공 혁신성장 자금 (기존 로직 유지)"""
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
        """소진공 저신용 자금 (기존 로직 유지)"""
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
        """신용보증재단 자금 (기대출 반영)"""
        # 데이터 추출
        credit_score = company_data.get('credit_score', 0)
        annual_revenue = company_data.get('annual_revenue', 0)
        existing_debt_jaedan = company_data.get('existing_debt_jaedan', 0)  # 신규 추가

        # 타입 안전성 확보
        try:
            credit_score = int(credit_score)
            annual_revenue = int(annual_revenue)
            existing_debt_jaedan = int(existing_debt_jaedan)
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

        # 핵심 추가: 기존 재단 대출 차감
        final_limit = final_limit - existing_debt_jaedan

        return {
            'fund_name': '신용보증재단',
            'limit': int(max(0, final_limit)),
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

        # 한도 큰 순서로 정렬 (내림차순)
        def get_sort_key(fund):
            limit = fund.get('limit', 0)
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
                total += 40_000_000
        return total


# 대표님 사례 테스트 함수
def test_user_case():
    """대표님 제시 사례 테스트"""
    recommender = PolicyFundRecommender()
    
    # 매출 2.3억, 신용969점, 제조업, 재단 5천만원 기대출, 2024.1.1 개업, 40세 미만
    test_case = {
        'annual_revenue': 230_000_000,      # 2.3억
        'credit_score': 969,
        'is_manufacturing_it': True,
        'existing_debt_kibo': 0,
        'existing_debt_shinbo': 0,
        'existing_debt_jaedan': 50_000_000,  # 재단 5천만원 기대출
        'opening_date': '2024년1월1일',
        'age': 35,                          # 40세 미만 가정
        'career_years': 5,                  # 기보/중진공 조건 충족 가정
        'employees': 3
    }
    
    print("=== 대표님 사례 테스트 결과 ===")
    print(f"매출: {test_case['annual_revenue']:,}원")
    print(f"신용점수: {test_case['credit_score']}점")
    print(f"업종: 제조업")
    print(f"재단 기대출: {test_case['existing_debt_jaedan']:,}원")
    print()
    
    results = recommender.recommend_funds(test_case)
    
    for result in results:
        limit_str = f"{result['limit']:,}원" if isinstance(result['limit'], int) else result['limit']
        print(f"{result['fund_label']}: {result['fund_name']} - {limit_str}")
        
        # 중진공 금리 정보 출력
        if 'interest_rate' in result:
            print(f"  → 금리: {result['interest_rate']}")
        
        # 기보 계산 상세 출력
        if 'calculation_detail' in result:
            print(f"  → 계산: {result['calculation_detail']}")
    
    print()
    total = recommender.get_total_funding_amount(results)
    print(f"총 조달 가능: {total:,}원")


if __name__ == "__main__":
    test_user_case()
