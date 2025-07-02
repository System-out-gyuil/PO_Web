import math
from typing import Dict, Optional, List


class FundingCalculator:
    """추천자금 계산기"""
    
    # 상수 정의
    UNIT_50M = 50_000_000  # 5천만원 단위
    THRESHOLD_20M = 20_000_000  # 2천만원 기준
    
    def __init__(self):
        pass
    
    def calculate_recommendation(self, company_data: Dict) -> Dict:
        """
        주요 계산 함수 - 기업 데이터를 받아서 추천 결과 반환
        """
        print("=== 추천자금 계산 시작 ===")
        print(f"입력 데이터: {company_data}")
        
        # 추천 결과 리스트
        recommendations = []
        
        # 1. 주요 자금 (기보 vs 신보 중 하나만)
        primary_fund = self._determine_primary_fund(company_data)
        if primary_fund:
            recommendations.append(primary_fund['fund'])
            print(f"주요 자금 선택: {primary_fund['fund']['fund_name']} - {primary_fund.get('exclusion_note', '')}")
        
        # 2. 중진공 청년창업자금
        jungjin_fund = self._calculate_jungjin_youth_startup(company_data)
        if jungjin_fund:
            recommendations.append(jungjin_fund)
            print(f"중진공 청년창업자금 가능: {jungjin_fund['limit']:,}원")
        
        # 3. 소진공 자금들
        sojin_funds = self._calculate_sojin_funds(company_data)
        recommendations.extend(sojin_funds)
        for fund in sojin_funds:
            print(f"소진공 자금: {fund['fund_name']} - {fund['limit']:,}원")
        
        # 4. 신용보증재단
        foundation_fund = self._calculate_credit_guarantee_foundation(company_data)
        if foundation_fund:
            recommendations.append(foundation_fund)
            print(f"신용보증재단: {foundation_fund['limit']:,}원")
        
        # 총 추천 금액 계산
        total_amount = sum(fund['limit'] for fund in recommendations)
        
        result = {
            'total_recommended_amount': f"{total_amount:,}원",
            'individual_funds': recommendations,
            'analysis_summary': self._create_analysis_summary(company_data, recommendations)
        }
        
        print(f"총 추천 금액: {total_amount:,}원")
        print("=== 추천자금 계산 완료 ===")
        
        return result
    
    def _round_up_to_50m_unit_always(self, amount: float) -> int:
        """
        5천만원 단위로 무조건 상향 조정 (핵심 함수)
        예: 4억 6천만원 → 5억원, 1억 2천만원 → 1억 5천만원
        """
        if amount <= 0:
            return 0
        return math.ceil(amount / self.UNIT_50M) * self.UNIT_50M
    
    def _determine_primary_fund(self, company_data: Dict) -> Optional[Dict]:
        """
        기보 vs 신보 우선순위 결정 (제조업 절대 우선 원칙)
        """
        if company_data['industry'] == '제조업':
            # 제조업은 무조건 기보 우선 검토
            kibo_fund = self._calculate_kibo_fund(company_data)
            if kibo_fund:
                return {
                    'fund': kibo_fund,
                    'exclusion_note': '제조업 우선 원칙으로 신보 제외'
                }
            else:
                # 기보 불가능한 제조업은 신보 검토
                sinbo_fund = self._calculate_sinbo_fund(company_data)
                if sinbo_fund:
                    return {
                        'fund': sinbo_fund,
                        'exclusion_note': '기보 조건 미달로 신보 선택'
                    }
        else:
            # 비제조업은 기보 vs 신보 비교 후 선택
            kibo_fund = self._calculate_kibo_fund(company_data)
            sinbo_fund = self._calculate_sinbo_fund(company_data)
            
            if kibo_fund and sinbo_fund:
                if kibo_fund['limit'] >= sinbo_fund['limit']:
                    return {
                        'fund': kibo_fund,
                        'exclusion_note': '기보가 더 유리하여 신보 제외'
                    }
                else:
                    return {
                        'fund': sinbo_fund,
                        'exclusion_note': '신보가 더 유리하여 기보 제외'
                    }
            elif kibo_fund:
                return {'fund': kibo_fund}
            elif sinbo_fund:
                return {'fund': sinbo_fund}
        
        return None
    
    def _calculate_kibo_fund(self, company_data: Dict) -> Optional[Dict]:
        """
        기보 자금 계산 (5천만원 단위 완전 적용)
        """
        # 자격 요건: 제조업/IT + (신용800+ OR 경력15년+) + 유관경력3년+
        if not (
            company_data['industry'] in ['제조업', 'IT'] and
            (company_data['credit_score'] >= 800 or 
             company_data.get('experience_years', 0) >= 15) and
            company_data.get('experience_years', 0) >= 3
        ):
            return None
        
        existing_debt = company_data.get('existing_debt', 0)
        
        # IP보증 vs 일반보증 계산
        ip_raw = (company_data['annual_revenue'] * 0.30) - existing_debt
        general_raw = 100_000_000 - existing_debt  # 기본 1억원
        
        # 핵심: 2천만원 기준으로 선택 (대표님 피드백 반영)
        if ip_raw > general_raw and (ip_raw - general_raw) > self.THRESHOLD_20M:
            calculated_limit = ip_raw
            fund_type = 'IP보증'
            selection_reason = f'IP보증이 일반보증보다 {(ip_raw - general_raw)//10000000}천만원 유리'
        else:
            calculated_limit = general_raw
            fund_type = '일반보증'
            if ip_raw > general_raw:
                selection_reason = f'IP보증 차이 {(ip_raw - general_raw)//10000000}천만원으로 일반보증 선택 (특허비용 고려)'
            else:
                selection_reason = '일반보증이 더 유리'
        
        if calculated_limit <= 0:
            return None
        
        # 핵심: 5천만원 단위로 무조건 상향 조정
        final_limit = self._round_up_to_50m_unit_always(calculated_limit)
        
        return {
            'fund_name': f'기보_{fund_type}',
            'limit': int(final_limit),
            'priority': 1,
            'institution': '기술보증기금',
            'calculation_note': selection_reason,
            'processing_time': '3-4주',
            'interest_rate': '3.0~5.5%',
            'required_documents': ['사업자등록증', '재무제표', '신용보고서', '기술자료']
        }
    
    def _calculate_sinbo_fund(self, company_data: Dict) -> Optional[Dict]:
        """
        신보 자금 계산 (5천만원 단위 적용)
        """
        # 자격 요건: 업력 3개월+ AND 신용 850점+ AND 매출 5억+
        if not (
            company_data['business_months'] >= 3 and
            company_data['credit_score'] >= 850 and
            company_data['annual_revenue'] > 500_000_000
        ):
            return None
        
        # 한도 계산
        if company_data['annual_revenue'] >= 1_000_000_000:  # 10억 이상
            rate = 0.15
            rate_note = '대규모 기업 우대 15%'
        elif company_data['credit_score'] >= 900:
            rate = 0.15
            rate_note = '고신용 우대 15%'
        else:
            rate = 0.12
            rate_note = '일반 12%'
        
        total_possible = company_data['annual_revenue'] * rate
        existing_sinbo = company_data.get('existing_sinbo_debt', 0)
        additional_raw = total_possible - existing_sinbo
        
        if additional_raw <= 0:
            return None
        
        # 5천만원 단위로 상향 조정
        final_limit = self._round_up_to_50m_unit_always(additional_raw)
        
        fund_type = '증액' if existing_sinbo > 0 else '일반보증'
        
        return {
            'fund_name': f'신보_{fund_type}',
            'limit': int(final_limit),
            'priority': 2,
            'institution': '신용보증기금',
            'calculation_note': f'{rate_note} 적용',
            'processing_time': '2-3주',
            'interest_rate': '3.5~6.0%',
            'required_documents': ['사업자등록증', '재무제표', '신용보고서']
        }
    
    def _calculate_jungjin_youth_startup(self, company_data: Dict) -> Optional[Dict]:
        """
        중진공 청년창업자금 계산
        """
        # 자격 요건 확인
        if not (
            company_data['industry'] in ['제조업', 'IT'] and
            company_data['ceo_age'] < 40 and
            (company_data.get('is_startup') or company_data['business_months'] <= 36) and
            company_data['credit_score'] >= 800 and
            company_data.get('experience_years', 0) >= 3
        ):
            return None
        
        return {
            'fund_name': '중진공_청년창업',
            'limit': 100_000_000,  # 고정 1억원
            'priority': 1,
            'institution': '중소벤처기업진흥공단',
            'calculation_note': '청년창업자금 고정 한도',
            'processing_time': '4-6주',
            'interest_rate': '2.0~3.5%',
            'required_documents': ['사업자등록증', '사업계획서', '경력증명서']
        }
    
    def _calculate_sojin_funds(self, company_data: Dict) -> List[Dict]:
        """
        소진공 자금들 계산
        """
        funds = []
        
        # 직원수 기준 확인
        employee_limit = 10 if company_data['industry'] in ['제조업', '건설업', '운수업', '광업'] else 5
        
        if company_data['employees'] >= employee_limit:
            return funds
        
        # 혁신성장자금
        if (company_data['annual_revenue'] >= 200_000_000 and 
            company_data['credit_score'] >= 750):
            
            # 한도 결정 (대표님 피드백 반영)
            if company_data['annual_revenue'] >= 300_000_000 and company_data['credit_score'] >= 800:
                limit = 70_000_000  # 7천만원
                note = '매출 3억 이상 + 신용 800점 이상'
            else:
                limit = 50_000_000  # 5천만원
                note = '신용점수 고려 보수적 적용'
            
            funds.append({
                'fund_name': '소진공_혁신성장',
                'limit': limit,
                'priority': 3,
                'institution': '소상공인시장진흥공단',
                'calculation_note': note,
                'processing_time': '3-4주',
                'interest_rate': '3.0~4.5%'
            })
        
        # 저신용자금
        if company_data['credit_score'] <= 839:
            funds.append({
                'fund_name': '소진공_저신용',
                'limit': 30_000_000,  # 고정 3천만원
                'priority': 4,
                'institution': '소상공인시장진흥공단',
                'calculation_note': '저신용자금 고정 한도',
                'processing_time': '2-3주',
                'interest_rate': '4.0~6.0%'
            })
        
        return funds
    
    def _calculate_credit_guarantee_foundation(self, company_data: Dict) -> Optional[Dict]:
        """
        신용보증재단 계산 (매출 연동 우대)
        """
        if company_data['annual_revenue'] <= 0:
            return None
        
        # 매출 우대 적용 (핵심 로직)
        if company_data['annual_revenue'] >= 1_500_000_000:  # 15억 이상
            final_limit = 50_000_000  # 무조건 5천만원
            note = '고매출 우대 (15억 이상)'
            display = '5천만원'
        elif company_data['annual_revenue'] >= 1_000_000_000:  # 10억 이상
            if company_data['credit_score'] >= 850:
                final_limit = 50_000_000
                note = '고매출 + 고신용 우대'
                display = '5천만원'
            else:
                final_limit = 40_000_000  # 평균값으로 설정
                note = '고매출 우대 (3천~5천만원 범위)'
                display = '3천~5천만원'
        else:
            # 신용점수별 기본 한도
            credit_limits = {
                900: 50_000_000, 850: 30_000_000, 800: 25_000_000,
                750: 20_000_000, 700: 15_000_000
            }
            final_limit = 10_000_000  # 기본값
            for threshold in sorted(credit_limits.keys(), reverse=True):
                if company_data['credit_score'] >= threshold:
                    final_limit = credit_limits[threshold]
                    break
            note = f'신용점수 {company_data["credit_score"]}점 기준'
            display = f'{final_limit//10_000_000}천만원'
        
        return {
            'fund_name': '신용보증재단',
            'limit': int(final_limit),
            'limit_display': display,
            'priority': 5,
            'institution': '신용보증재단',
            'calculation_note': note,
            'processing_time': '1-2주',
            'interest_rate': '4.5~7.0%'
        }
    
    def _create_analysis_summary(self, company_data: Dict, recommendations: List[Dict]) -> Dict:
        """
        분석 요약 생성
        """
        return {
            'sales_score': self._evaluate_sales_score(company_data['annual_revenue']),
            'credit_score': self._evaluate_credit_score(company_data['credit_score']),
            'business_stability': self._evaluate_business_stability(company_data),
            'debt_ratio': self._evaluate_debt_ratio(company_data),
            'total_products': len(recommendations),
            'confidence': '85%' if len(recommendations) >= 2 else '70%'
        }
    
    def _evaluate_sales_score(self, revenue: int) -> str:
        """매출 평가"""
        if revenue >= 1_000_000_000:
            return '우수'
        elif revenue >= 500_000_000:
            return '양호'
        elif revenue >= 200_000_000:
            return '보통'
        else:
            return '개선필요'
    
    def _evaluate_credit_score(self, credit: int) -> str:
        """신용 평가"""
        if credit >= 900:
            return '최우수'
        elif credit >= 850:
            return '우수'
        elif credit >= 800:
            return '양호'
        elif credit >= 750:
            return '보통'
        else:
            return '개선필요'
    
    def _evaluate_business_stability(self, company_data: Dict) -> str:
        """사업 안정성 평가"""
        months = company_data['business_months']
        if months >= 36:
            return '안정적'
        elif months >= 12:
            return '양호'
        else:
            return '신규'
    
    def _evaluate_debt_ratio(self, company_data: Dict) -> str:
        """부채 비율 평가"""
        total_debt = company_data.get('existing_debt', 0)
        revenue = company_data['annual_revenue']
        
        if revenue > 0:
            ratio = total_debt / revenue
            if ratio < 0.3:
                return '우수'
            elif ratio < 0.5:
                return '양호'
            elif ratio < 0.7:
                return '보통'
            else:
                return '높음'
        else:
            return '판단불가' 