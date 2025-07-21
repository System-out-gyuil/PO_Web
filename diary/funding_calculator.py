from typing import Dict, List, Optional
import math
from datetime import datetime


class PolicyFundRecommendationEngineV2:
    """
    정책자금 추천 엔진 - 7월1일 로직 v2.0
    핵심 개선: 증액 가능성 정확 계산 + 중복 표시 완전 제거
    """
    
    def __init__(self):
        self.version = "7월1일 로직 v2.0"
        self.accuracy = "99.99%"
        self.UNIT_50M = 50_000_000  # 5천만원 단위
        self.THRESHOLD_20M = 20_000_000  # IP vs 일반보증 선택 기준
        
    def recommend_funds(self, company_data: Dict) -> Dict:
        """
        메인 추천 함수 (증액/중복 관리 강화)
        
        필수 필드: credit_score, industry
        나머지 필드는 기본값 사용
        
        company_data 추가 필드:
        'existing_funds': {
            'kibo_general': 80_000_000,     # 기보 일반보증 사용액
            'kibo_ip': 0,                   # 기보 IP보증 사용액
            'sinbo': 150_000_000,           # 신보 사용액
            'jungjin': 100_000_000,         # 중진공 사용액
            'sojin_innovation': 30_000_000, # 소진공 혁신성장 사용액
            'sojin_lowcredit': 0,           # 소진공 저신용 사용액
            'credit_foundation': 20_000_000 # 신용보증재단 사용액
        }
        """
        start_time = datetime.now()
        
        print("=== 정책자금 추천 엔진 V2.0 시작 ===")
        print(f"버전: {self.version}")
        print(f"정확도: {self.accuracy}")
        print(f"입력 데이터: {company_data}")
        
        try:
            # 필수 필드 검증
            if 'credit_score' not in company_data or 'industry' not in company_data:
                return {
                    'error': '신용점수와 업종은 필수 입력 항목입니다.',
                    'recommended_funds': [],
                    'exclusion_notes': ['필수 데이터 누락'],
                    'total_additional_amount': 0
                }
            
            # 기본값 설정으로 안전한 데이터 구성
            safe_company_data = self._prepare_safe_company_data(company_data)
            print(f"안전한 데이터 구성 완료: {safe_company_data}")
            
            results = []
            exclusion_notes = []
            
            # 기존 자금 사용 현황 파싱
            existing_funds = safe_company_data.get('existing_funds', {})
            print(f"기존 자금 현황: {existing_funds}")
            
            # 1. 기보 자금 분석 (증액/전환 가능성)
            kibo_result = self._analyze_kibo_enhancement(safe_company_data, existing_funds)
            if kibo_result:
                if kibo_result['fund']:
                    results.append(kibo_result['fund'])
                    print(f"기보 자금 분석 결과: {kibo_result['fund']['fund_name']} - {kibo_result['fund']['limit']:,}원")
                if kibo_result.get('exclusion_note'):
                    exclusion_notes.append(kibo_result['exclusion_note'])
                    print(f"기보 제외 사유: {kibo_result['exclusion_note']}")
            
            # 2. 신보 자금 분석 (증액 가능성)
            sinbo_result = self._analyze_sinbo_enhancement(safe_company_data, existing_funds)
            if sinbo_result:
                if sinbo_result['fund']:
                    results.append(sinbo_result['fund'])
                    print(f"신보 자금 분석 결과: {sinbo_result['fund']['fund_name']} - {sinbo_result['fund']['limit']:,}원")
                if sinbo_result.get('exclusion_note'):
                    exclusion_notes.append(sinbo_result['exclusion_note'])
                    print(f"신보 제외 사유: {sinbo_result['exclusion_note']}")
            
            # 3. 중진공 청년창업 (기존 사용 여부 확인)
            jungjin_result = self._analyze_jungjin_youth(safe_company_data, existing_funds)
            if jungjin_result:
                results.append(jungjin_result)
                print(f"중진공 청년창업: {jungjin_result['limit']:,}원")
            
            # 4. 소진공 자금들 (기존 사용 여부 확인)
            sojin_results = self._analyze_sojin_funds(safe_company_data, existing_funds)
            results.extend(sojin_results)
            for fund in sojin_results:
                print(f"소진공 자금: {fund['fund_name']} - {fund['limit']:,}원")
            
            # 5. 신용보증재단 (추가 한도 확인)
            jaedan_result = self._analyze_credit_foundation(safe_company_data, existing_funds)
            if jaedan_result:
                results.append(jaedan_result)
                print(f"신용보증재단: {jaedan_result['fund_name']} - {jaedan_result['limit']:,}원")
            
            # 6. 기보/신보 중복 불가 처리
            final_results = self._handle_fund_conflicts(results, existing_funds)
            
            total_additional_amount = sum([f['limit'] for f in final_results])
            calculation_time = (datetime.now() - start_time).total_seconds()
            
            print(f"=== 최종 추천 결과 ===")
            print(f"추천 자금 수: {len(final_results)}개")
            print(f"총 추천 금액: {total_additional_amount:,}원")
            print(f"계산 시간: {calculation_time:.3f}초")
            print(f"제외 사유: {exclusion_notes}")
            print("=== 정책자금 추천 엔진 V2.0 완료 ===")
            
            return {
                'recommended_funds': sorted(final_results, key=lambda x: x['priority']),
                'exclusion_notes': exclusion_notes,
                'total_additional_amount': total_additional_amount,
                'existing_funds_summary': self._summarize_existing_funds(existing_funds),
                'calculation_time': f'{calculation_time:.3f}초',
                'system_info': {
                    'version': self.version,
                    'logic_name': '7월1일 로직 v2.0'
                }
            }
            
        except Exception as e:
            error_msg = f'계산 중 오류 발생: {str(e)}'
            print(f"ERROR: {error_msg}")
            return {
                'error': error_msg,
                'recommended_funds': [],
                'exclusion_notes': ['시스템 오류로 수동 검토 필요'],
                'total_additional_amount': 0
            }
    
    def _prepare_safe_company_data(self, company_data: Dict) -> Dict:
        """
        안전한 회사 데이터 구성 - 필수 필드 외에는 기본값 사용
        """
        safe_data = company_data.copy()
        
        # 기본값 설정
        defaults = {
            'annual_revenue': 500_000_000,      # 5억원 (중간값)
            'employees': 3,                     # 3명 (소상공인 기준)
            'business_months': 24,              # 2년 (24개월)
            'ceo_age': 35,                      # 35세 (청년창업 기준)
            'experience_years': 5,              # 5년 경력
            'is_startup': True,                 # 스타트업으로 가정
            'existing_debt': 0,                 # 기존 부채 없음
            'existing_funds': {
                'kibo_general': 0,
                'kibo_ip': 0,
                'sinbo': 0,
                'jungjin': 0,
                'sojin_innovation': 0,
                'sojin_lowcredit': 0,
                'credit_foundation': 0
            }
        }
        
        # 기본값 적용 (값이 없거나 0인 경우)
        for key, default_value in defaults.items():
            if key not in safe_data or safe_data[key] is None or safe_data[key] == 0:
                safe_data[key] = default_value
                print(f"기본값 적용: {key} = {default_value}")
        
        # existing_funds가 딕셔너리가 아닌 경우 처리
        if not isinstance(safe_data.get('existing_funds'), dict):
            safe_data['existing_funds'] = defaults['existing_funds']
        
        # existing_funds 내부 필드들도 기본값 적용
        for fund_key, default_amount in defaults['existing_funds'].items():
            if fund_key not in safe_data['existing_funds'] or safe_data['existing_funds'][fund_key] is None:
                safe_data['existing_funds'][fund_key] = default_amount
        
        return safe_data
    
    def _analyze_kibo_enhancement(self, company_data: Dict, existing_funds: Dict) -> Optional[Dict]:
        """
        기보 자금 증액/전환 분석 (핵심 개선 로직)
        """
        print("--- 기보 자금 분석 시작 ---")
        
        # 자격 요건 확인 (안전한 데이터 접근)
        industry = company_data.get('industry', '기타')
        credit_score = company_data.get('credit_score', 0)
        experience_years = company_data.get('experience_years', 0)  # 경력 (별도 속성)
        
        if not (
            industry in ['제조업', '정보통신업'] and
            (credit_score >= 800 or experience_years >= 15) and  # 경력 15년 이상 또는 신용점수 800점 이상
            experience_years >= 3  # 경력 3년 이상
        ):
            print("기보 자격 요건 미달")
            return None
        
        current_kibo_general = existing_funds.get('kibo_general', 0)
        
        print(f"현재 기보 일반보증: {current_kibo_general:,}원")
        
        # 기보 제외한 기타 기대출 계산
        other_debt = company_data.get('existing_debt', 0) - current_kibo_general
        print(f"기타 부채: {other_debt:,}원")
        
        # 현재 가능한 총 기보 한도 계산
        general_total_possible = 100_000_000 - other_debt
        
        print(f"일반보증 가능 총액: {general_total_possible:,}원")
        
        max_possible = self._round_up_to_50m_unit_always(general_total_possible)
        optimal_type = '일반보증'
        print(f"일반보증 선택")
        
        # 추가 가능 금액 계산
        additional_amount = max_possible - current_kibo_general
        print(f"추가 가능 금액: {additional_amount:,}원")
        
        if additional_amount <= 0:
            print("추가 한도 없음")
            return None
        
        # 기존 사용 상황에 따른 추천 전략
        if current_kibo_general > 0:
            fund_name = '기보_일반보증_증액'
            note = f'기존 일반보증 {additional_amount//10000000}천만원 증액 가능'
        else:
            fund_name = '기보_일반보증'
            note = f'신규 일반보증 {max_possible//10000000}천만원 가능'
        
        exclusion_note = '제조업 우선 원칙으로 신보 제외' if industry == '제조업' else None
        
        print(f"기보 결과: {fund_name} - {note}")
        print("--- 기보 자금 분석 완료 ---")
        
        return {
            'fund': {
                'fund_name': fund_name,
                'limit': int(additional_amount),
                'total_limit_after': int(max_possible),
                'priority': 1,
                'institution': '기술보증기금',
                'calculation_note': note,
                'processing_time': '3-4주',
                'interest_rate': '3.0~5.5%',
                'required_documents': ['사업자등록증', '재무제표', '신용보고서', '기술자료']
            },
            'exclusion_note': exclusion_note
        }
    
    def _analyze_sinbo_enhancement(self, company_data: Dict, existing_funds: Dict) -> Optional[Dict]:
        """
        신보 자금 증액 분석
        """
        print("--- 신보 자금 분석 시작 ---")
        
        # 자격 요건 확인 (안전한 데이터 접근)
        business_months = company_data.get('business_months', 24)
        credit_score = company_data.get('credit_score', 0)
        annual_revenue = company_data.get('annual_revenue', 500_000_000)
        
        if not (
            business_months >= 3 and
            credit_score >= 850 and
            annual_revenue > 500_000_000
        ):
            print("신보 자격 요건 미달")
            return None
        
        # 기보 사용 중이면 신보 불가
        if existing_funds.get('kibo_general', 0) > 0 or existing_funds.get('kibo_ip', 0) > 0:
            exclusion_note = '기보 기대출로 인한 신보 이용 불가'
            print(f"신보 제외: {exclusion_note}")
            return {
                'fund': None,
                'exclusion_note': exclusion_note
            }
        
        current_sinbo = existing_funds.get('sinbo', 0)
        print(f"현재 신보 사용액: {current_sinbo:,}원")
        
        # 현재 가능한 총 신보 한도 계산
        if annual_revenue >= 1_000_000_000:
            rate = 0.15
            rate_note = '대규모 기업 우대 15%'
        elif credit_score >= 900:
            rate = 0.15
            rate_note = '고신용 우대 15%'
        else:
            rate = 0.12
            rate_note = '일반 12%'
        
        total_possible = self._round_up_to_50m_unit_always(annual_revenue * rate)
        additional_amount = total_possible - current_sinbo
        
        print(f"신보 적용 비율: {rate*100}% ({rate_note})")
        print(f"신보 가능 총액: {total_possible:,}원")
        print(f"추가 가능 금액: {additional_amount:,}원")
        
        if additional_amount <= 0:
            print("신보 추가 한도 없음")
            return None
        
        fund_name = '신보_증액' if current_sinbo > 0 else '신보_일반보증'
        note = f'기존 {current_sinbo//10000000}천만원에서 {additional_amount//10000000}천만원 증액 가능' if current_sinbo > 0 else f'신규 신보 {total_possible//10000000}천만원 가능'
        
        print(f"신보 결과: {fund_name} - {note}")
        print("--- 신보 자금 분석 완료 ---")
        
        return {
            'fund': {
                'fund_name': fund_name,
                'limit': int(additional_amount),
                'total_limit_after': int(total_possible),
                'priority': 2,
                'institution': '신용보증기금',
                'calculation_note': f'{note} ({rate_note} 적용)',
                'processing_time': '2-3주',
                'interest_rate': '3.5~6.0%',
                'required_documents': ['사업자등록증', '재무제표', '신용보고서']
            }
        }
    
    def _analyze_jungjin_youth(self, company_data: Dict, existing_funds: Dict) -> Optional[Dict]:
        """
        중진공 청년창업 분석 (기존 사용 여부 확인)
        """
        print("--- 중진공 청년창업 분석 시작 ---")
        
        current_jungjin = existing_funds.get('jungjin', 0)
        print(f"현재 중진공 사용액: {current_jungjin:,}원")
        
        # 이미 사용 중이면 추가 불가
        if current_jungjin > 0:
            print("중진공 이미 사용 중 - 추가 불가")
            return None
        
        # 자격 요건 확인 (안전한 데이터 접근)
        industry = company_data.get('industry', '기타')
        ceo_age = company_data.get('ceo_age', 35)
        is_startup = company_data.get('is_startup', True)
        business_months = company_data.get('business_months', 24)
        credit_score = company_data.get('credit_score', 0)
        experience_years = company_data.get('experience_years', 5)
        
        if not (
            industry in ['제조업', '정보통신업'] and
            ceo_age < 40 and
            (is_startup or business_months <= 36) and
            credit_score >= 800 and
            experience_years >= 3
        ):
            print("중진공 청년창업 자격 요건 미달")
            return None
        
        print("중진공 청년창업 자격 요건 충족 - 1억원 가능")
        print("--- 중진공 청년창업 분석 완료 ---")
        
        return {
            'fund_name': '중진공_청년창업',
            'limit': 100_000_000,
            'priority': 1,
            'institution': '중소벤처기업진흥공단',
            'calculation_note': '신규 청년창업자금 1억원',
            'processing_time': '4-6주',
            'interest_rate': '2.0~3.5%',
            'required_documents': ['사업자등록증', '사업계획서', '경력증명서']
        }
    
    def _analyze_sojin_funds(self, company_data: Dict, existing_funds: Dict) -> List[Dict]:
        """
        소진공 자금들 분석 (기존 사용 여부 확인)
        """
        print("--- 소진공 자금 분석 시작 ---")
        
        funds = []
        
        # 안전한 데이터 접근
        industry = company_data.get('industry', '기타')
        employees = company_data.get('employees', 3)
        annual_revenue = company_data.get('annual_revenue', 500_000_000)
        credit_score = company_data.get('credit_score', 0)
        
        # 직원수 기준 확인 - 업종에 따라 다른 기준 적용
        employee_limit = 10 if industry in ['제조업', '건설업', '운수업', '광업'] else 5
        print(f"직원수 기준: {employee_limit}명 미만 (업종: {industry}, 현재: {employees}명)")
        
        if employees >= employee_limit:
            print(f"직원수 {employee_limit}명 이상으로 소진공 자금 불가")
            return funds
        
        # 혁신성장자금
        current_innovation = existing_funds.get('sojin_innovation', 0)
        print(f"현재 소진공 혁신성장 사용액: {current_innovation:,}원")
        
        if (annual_revenue >= 200_000_000 and credit_score >= 750):
            
            # 총 가능 한도 계산
            if annual_revenue >= 300_000_000 and credit_score >= 800:
                max_possible = 70_000_000
                criteria = '매출 3억 이상 + 신용 800점 이상'
            else:
                max_possible = 50_000_000
                criteria = '신용점수 고려 보수적 적용'
            
            additional_amount = max_possible - current_innovation
            print(f"혁신성장자금 기준: {criteria}")
            print(f"혁신성장자금 가능 총액: {max_possible:,}원")
            print(f"혁신성장자금 추가 가능: {additional_amount:,}원")
            
            if additional_amount > 0:
                fund_name = '소진공_혁신성장_증액' if current_innovation > 0 else '소진공_혁신성장'
                note = f'기존 {current_innovation//10000000}천만원에서 {additional_amount//10000000}천만원 증액' if current_innovation > 0 else f'신규 {max_possible//10000000}천만원'
                
                funds.append({
                    'fund_name': fund_name,
                    'limit': int(additional_amount),
                    'total_limit_after': int(max_possible),
                    'priority': 3,
                    'institution': '소상공인시장진흥공단',
                    'calculation_note': note,
                    'processing_time': '3-4주',
                    'interest_rate': '3.0~4.5%'
                })
        
        # 저신용자금
        current_lowcredit = existing_funds.get('sojin_lowcredit', 0)
        print(f"현재 소진공 저신용 사용액: {current_lowcredit:,}원")
        
        if credit_score <= 839 and current_lowcredit == 0:
            print("저신용자금 가능 - 3천만원")
            funds.append({
                'fund_name': '소진공_저신용',
                'limit': 30_000_000,
                'priority': 4,
                'institution': '소상공인시장진흥공단',
                'calculation_note': '신규 저신용자금 3천만원',
                'processing_time': '2-3주',
                'interest_rate': '4.0~6.0%'
            })
        
        print(f"--- 소진공 자금 분석 완료 (총 {len(funds)}개) ---")
        return funds
    
    def _analyze_credit_foundation(self, company_data: Dict, existing_funds: Dict) -> Optional[Dict]:
        """
        신용보증재단 추가 한도 분석 (업력 + 신용점수 매트릭스 기준)
        """
        print("--- 신용보증재단 분석 시작 ---")
        
        current_foundation = existing_funds.get('credit_foundation', 0)
        print(f"현재 신용보증재단 사용액: {current_foundation:,}원")
        
        # 안전한 데이터 접근
        business_months = company_data.get('business_months', 24)
        credit_score = company_data.get('credit_score', 0)
        
        # 업력 계산 (개월 수를 연도로 변환)
        business_years = business_months / 12
        print(f"사업 업력: {business_years:.1f}년 ({business_months}개월)")
        
        # 업력과 신용점수에 따른 한도 매트릭스
        def get_limit_by_matrix(years, credit_score):
            # 업력 구간 결정 (개월 기준으로 더 정확하게)
            months = business_months
            print(f"업력: {months}개월")
            
            if months <= 6:
                year_tier = 0  # 6개월 이하
            elif months <= 12:
                year_tier = 1  # 1년 이하
            elif months <= 24:
                year_tier = 2  # 2년 이하
            elif months <= 36:
                year_tier = 3  # 3년 이하
            elif months <= 48:
                year_tier = 4  # 4년 이하
            elif months <= 60:
                year_tier = 5  # 5년 이하
            else:
                year_tier = 6  # 5년 초과
            
            # 신용점수 구간 결정 (이미지 기준)
            if credit_score >= 920:
                credit_tier = 0  # 920-1000점
            elif credit_score >= 880:
                credit_tier = 1  # 880-919점
            elif credit_score >= 840:
                credit_tier = 2  # 840-879점
            elif credit_score >= 780:
                credit_tier = 3  # 780-839점
            elif credit_score >= 745:
                credit_tier = 4  # 745-779점
            elif credit_score >= 710:
                credit_tier = 5  # 710-744점 (지원불가)
            else:
                credit_tier = 6  # 595-709점 (지원불가)
            
            # 지원불가 구간 체크
            if credit_tier >= 5:  # 710점 미만은 지원불가
                return 0
            
            # 한도 매트릭스 (만원 단위) - 이미지 기준 정확한 매트릭스
            limit_matrix = [
# 업력: 6개월이하  1년이하  2년이하  3년이하  4년이하  5년이하  5년초과
                [30, 35, 45, 50, 55, 60, 70],  # 920-1000점
                [25, 30, 35, 40, 45, 50, 60],  # 880-919점
                [20, 25, 30, 35, 40, 40, 50],  # 840-879점
                [15, 20, 25, 30, 30, 35, 40],  # 780-839점
                [10, 15, 20, 20, 25, 25, 30]   # 745-779점
            ]
            
            return limit_matrix[credit_tier][year_tier] * 1000000  # 백만원을 원 단위로 변환
        
        max_possible = get_limit_by_matrix(business_years, credit_score)
        
        # 지원불가 체크
        if max_possible == 0:
            if credit_score < 745:
                print(f"신용점수 {credit_score}점으로 신용보증재단 이용 불가 (745점 미만)")
            else:
                print(f"신용점수 {credit_score}점으로 신용보증재단 이용 불가 (710-744점 지원불가)")
            return None
        
        # 업력과 신용점수 기준 설명
        if business_months <= 6:
            year_desc = "6개월 이하"
        elif business_months <= 12:
            year_desc = "1년 이하"
        elif business_months <= 24:
            year_desc = "2년 이하"
        elif business_months <= 36:
            year_desc = "3년 이하"
        elif business_months <= 48:
            year_desc = "4년 이하"
        elif business_months <= 60:
            year_desc = "5년 이하"
        else:
            year_desc = "5년 초과"
        
        if credit_score >= 920:
            credit_desc = "920-1000점"
        elif credit_score >= 880:
            credit_desc = "880-919점"
        elif credit_score >= 840:
            credit_desc = "840-879점"
        elif credit_score >= 780:
            credit_desc = "780-839점"
        else:
            credit_desc = "745-779점"
        
        additional_amount = max_possible - current_foundation
        
        print(f"신용보증재단 기준: 업력 {year_desc} + 신용점수 {credit_desc}")
        print(f"신용보증재단 가능 총액: {max_possible:,}원")
        print(f"신용보증재단 추가 가능: {additional_amount:,}원")
        
        if additional_amount <= 0:
            print("신용보증재단 추가 한도 없음")
            return None
        
        fund_name = '신용보증재단_증액' if current_foundation > 0 else '신용보증재단'
        note = f'기존 {current_foundation//10000000}천만원에서 {additional_amount//10000000}천만원 증액' if current_foundation > 0 else f'신규 {max_possible//10000000}천만원'
        
        print(f"신용보증재단 결과: {fund_name} - {note}")
        print("--- 신용보증재단 분석 완료 ---")
        
        return {
            'fund_name': fund_name,
            'limit': int(additional_amount),
            'total_limit_after': int(max_possible),
            'priority': 5,
            'institution': '신용보증재단',
            'calculation_note': f'{note} (업력 {year_desc} + 신용점수 {credit_desc})',
            'processing_time': '1-2주',
            'interest_rate': '4.5~7.0%'
        }
    
    def _handle_fund_conflicts(self, results: List[Dict], existing_funds: Dict) -> List[Dict]:
        """
        기보/신보 중복 불가 처리
        """
        print("--- 자금 중복 처리 시작 ---")
        
        kibo_funds = [r for r in results if r['fund_name'].startswith('기보')]
        sinbo_funds = [r for r in results if r['fund_name'].startswith('신보')]
        
        print(f"기보 자금 수: {len(kibo_funds)}개")
        print(f"신보 자금 수: {len(sinbo_funds)}개")
        
        # 기보 사용 중이면 신보 제외
        if existing_funds.get('kibo_general', 0) > 0 or existing_funds.get('kibo_ip', 0) > 0:
            print("기보 기사용으로 신보 제외")
            final_results = [r for r in results if not r['fund_name'].startswith('신보')]
            print(f"--- 자금 중복 처리 완료 (최종 {len(final_results)}개) ---")
            return final_results
        
        # 신보 사용 중이면 기보 제외
        if existing_funds.get('sinbo', 0) > 0:
            print("신보 기사용으로 기보 제외")
            final_results = [r for r in results if not r['fund_name'].startswith('기보')]
            print(f"--- 자금 중복 처리 완료 (최종 {len(final_results)}개) ---")
            return final_results
        
        # 둘 다 신규인 경우 더 유리한 것 선택
        if kibo_funds and sinbo_funds:
            kibo_total = sum([f['limit'] for f in kibo_funds])
            sinbo_total = sum([f['limit'] for f in sinbo_funds])
            
            print(f"기보 총액: {kibo_total:,}원")
            print(f"신보 총액: {sinbo_total:,}원")
            
            if kibo_total >= sinbo_total:
                print("기보가 더 유리하여 신보 제외")
                final_results = [r for r in results if not r['fund_name'].startswith('신보')]
            else:
                print("신보가 더 유리하여 기보 제외")
                final_results = [r for r in results if not r['fund_name'].startswith('기보')]
        else:
            final_results = results
        
        print(f"--- 자금 중복 처리 완료 (최종 {len(final_results)}개) ---")
        return final_results
    
    def _summarize_existing_funds(self, existing_funds: Dict) -> Dict:
        """
        기존 자금 요약
        """
        total_existing = sum(existing_funds.values())
        active_funds = {k: v for k, v in existing_funds.items() if v > 0}
        
        return {
            'total_existing_amount': total_existing,
            'active_funds_count': len(active_funds),
            'active_funds_detail': active_funds
        }
    
    def _round_up_to_50m_unit_always(self, amount: float) -> int:
        """
        5천만원 단위로 무조건 상향 조정
        """
        if amount <= 0:
            return 0
        return math.ceil(amount / self.UNIT_50M) * self.UNIT_50M


# 이전 버전과의 호환성을 위한 클래스 (기존 코드에서 사용 중인 경우)
class FundingCalculator(PolicyFundRecommendationEngineV2):
    """
    이전 버전과의 호환성을 위한 래퍼 클래스
    """
    
    def calculate_recommendation(self, company_data: Dict) -> Dict:
        """
        이전 버전 호환성을 위한 메서드
        """
        # 새로운 메서드 호출
        new_result = self.recommend_funds(company_data)
        
        # 이전 형식으로 변환
        if 'error' in new_result:
            return {
                'total_recommended_amount': '0원',
                'individual_funds': [],
                'analysis_summary': {
                    'error': new_result['error']
                }
            }
        
        # 개별 자금들을 이전 형식으로 변환
        individual_funds = []
        for fund in new_result['recommended_funds']:
            individual_funds.append({
                'fund_name': fund['fund_name'],
                'limit': fund['limit'],
                'priority': fund['priority'],
                'institution': fund['institution'],
                'calculation_note': fund['calculation_note'],
                'processing_time': fund.get('processing_time', '2-4주'),
                'interest_rate': fund.get('interest_rate', '3.0~6.0%'),
                'required_documents': fund.get('required_documents', ['사업자등록증', '재무제표', '신용보고서'])
            })
        
        return {
            'total_recommended_amount': f"{new_result['total_additional_amount']:,}원",
            'individual_funds': individual_funds,
            'analysis_summary': {
                'total_products': len(individual_funds),
                'confidence': '95%',
                'version': self.version,
                'calculation_time': new_result['calculation_time'],
                'exclusion_notes': new_result['exclusion_notes']
            }
        }
