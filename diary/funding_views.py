import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User, Row, Attribute, AttributeValue, AttributeType
from board.models import BizInfo
from django.db.models import Q
import logging
import traceback
from .cascade_handlers import sync_cascade_attributes
import re
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .funding_calculator import PolicyFundRecommendationEngineV2

logger = logging.getLogger(__name__)

@csrf_exempt
def get_funding_recommendation(request):
    """
    정책자금 추천 엔진 V2.0을 사용한 자금 추천 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        data = json.loads(request.body)
        row_id = data.get('row_id')
        
        if not row_id:
            return JsonResponse({'success': False, 'error': 'row_id가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        print("=== 정책자금 추천 엔진 V2.0 시작 ===")
        print(f"Row ID: {row_id}")
        
        # 회사 데이터 수집
        company_data = {}
        
        # 필수 필드들 (기본값 없음)
        # 업종 정보
        industry_value = _get_attribute_value(user, row, '업종')
        company_data['industry'] = industry_value if industry_value else '기타'
        
        # 연매출액 (문자열에서 숫자 추출)
        revenue_value = _get_attribute_value(user, row, '매출')  # '연매출액' -> '매출'로 수정
        company_data['annual_revenue'] = _parse_number(revenue_value, 0)
        
        # 신용점수
        credit_value = _get_attribute_value(user, row, '신용점수')
        company_data['credit_score'] = _parse_number(credit_value, 0)
        
        # 기본값이 설정되는 필드들
        # 직원수 (기본값: 1명)
        employee_value = _get_attribute_value(user, row, '직원수')
        company_data['employees'] = _parse_number(employee_value, 1)
        
        # 개업년월로부터 업력 계산 (기본값: 3년 = 36개월)
        opening_date_value = _get_attribute_value(user, row, '개업년월')
        calculated_months = _calculate_business_months(opening_date_value)
        company_data['business_months'] = calculated_months if calculated_months > 0 else 36
        
        # 기대출 정보에서 기존 부채 및 자금 사용 현황 계산 (기본값: 0)
        debt_data = _get_debt_data(user, row)
        print(f"원본 기대출 데이터: {debt_data}")
        
        # 총 기존 부채 계산 (만원 -> 원)
        total_existing_debt = sum(float(v) for v in debt_data.values() if v) * 10000
        company_data['existing_debt'] = total_existing_debt
        
        # V2.0 엔진을 위한 정확한 existing_funds 구조 생성 (만원 -> 원 변환)
        # 실제 기대출 데이터 키에 맞춰 정확한 매핑
        print(f'업종 : {company_data["industry"]} ')
        print(f'매출 : {company_data["annual_revenue"]} ')
        print(f'신용점수 : {company_data["credit_score"]} ')
        print(f'직원수 : {company_data["employees"]} ')
        print(f'업력 : {company_data["business_months"]} ')

        biz_region = _get_attribute_value(user, row, '지역')
        biz_region_detail = _get_attribute_value(user, row, '상세지역')
        biz_industry = company_data['industry']

        # 매출액 카테고리 분류
        original_revenue = company_data['annual_revenue']
        if original_revenue == 0:
            biz_revenue = "매출 없음"
        elif original_revenue <= 100000000:  # 1억 이하
            biz_revenue = "1억 이하"
        elif original_revenue <= 500000000:  # 1~5억
            biz_revenue = "1~5억"
        elif original_revenue <= 1000000000:  # 5~10억
            biz_revenue = "5~10억"
        elif original_revenue <= 3000000000:  # 10~30억
            biz_revenue = "10~30억"
        else:  # 30억 이상
            biz_revenue = "30억 이상"
        
        # 직원수 카테고리 분류
        original_employees = company_data['employees']
        if original_employees == 0:
            biz_employees = "직원 없음"
        elif original_employees <= 4:  # 1~4인
            biz_employees = "1~4인"
        else:  # 5인 이상
            biz_employees = "5인 이상"

        if biz_employees in ["1~4인", "5~9인"] and biz_industry in ["광업", "제조업", "건설업", "운수업"] :
            biz_employees = "소상공인"
        elif biz_employees == "1~4인":
            biz_employees = "소상공인"
        elif biz_employees in ["10인 이상", "5~9인"]:
            biz_employees = "중소기업"
        
        # 업력 카테고리 분류 (개월을 년으로 환산)
        original_business_months = company_data['business_months']
        business_years = original_business_months / 12
        if business_years < 3:  # 3년 미만
            biz_business_months = "3년 미만"
        else:  # 3년 이상
            biz_business_months = "3년 이상"

        print(f'지역 : {biz_region} ')
        print(f'상세지역 : {biz_region_detail} ')
        print(f'업종 : {biz_industry} ')
        print(f'매출 : {biz_revenue} ')
        print(f'규모 : {biz_employees} ')
        print(f'업력 : {biz_business_months} ')

        # region이 None이 아닐 경우에만 지역 조건 포함
        if biz_region:
            # 상세지역이 정확히 포함된 데이터만 검색
            data_with_detail = BizInfo.objects.filter(
                                            (Q(region__contains=biz_region) | Q(region__contains="전국") | Q(hashtag__contains=biz_region))\
                                           & (Q(possible_industry__contains=biz_industry) | Q(possible_industry__contains='무관')) \
                                           & (Q(revenue__contains=biz_revenue) | Q(revenue__contains='무관'))\
                                           & (Q(business_period__contains=biz_business_months) | Q(business_period__contains='무관')) \
                                           & (Q(target__contains=biz_employees) | Q(target__contains='무관'))\
                                           & (
                                               # 상세지역이 포함된 경우만
                                               Q(noti_summary__contains=biz_region_detail) | 
                                               Q(hashtag__contains=biz_region_detail) | 
                                               Q(content__contains=biz_region_detail) | 
                                               Q(title__contains=biz_region_detail) |
                                               Q(region__contains=biz_region_detail)
                                           ))
            
            # 상세지역이 포함된 데이터가 5개 미만인 경우, 포함되지 않은 데이터도 추가
            if data_with_detail.count() < 5:
                # 포함되지 않은 데이터에서 필요한 만큼 추가 (중복 제거)
                needed_count = 5 - data_with_detail.count()
                additional_data = BizInfo.objects.filter(
                                            (Q(region__contains=biz_region) | Q(region__contains="전국") | Q(hashtag__contains=biz_region))\
                                           & (Q(possible_industry__contains=biz_industry) | Q(possible_industry__contains='무관')) \
                                           & (Q(revenue__contains=biz_revenue) | Q(revenue__contains='무관'))\
                                           & (Q(business_period__contains=biz_business_months) | Q(business_period__contains='무관')) \
                                           & (Q(target__contains=biz_employees) | Q(target__contains='무관'))
                                           ).exclude(
                                               # detail_region이 포함된 데이터 제외
                                               Q(noti_summary__contains=biz_region_detail) | 
                                               Q(hashtag__contains=biz_region_detail) | 
                                               Q(content__contains=biz_region_detail) | 
                                               Q(title__contains=biz_region_detail) |
                                               Q(region__contains=biz_region_detail)
                                           ).exclude(
                                               build_detail_region_exclude_query(biz_region, biz_region_detail)
                                           )[:needed_count]
                
                # 두 데이터셋 합치기
                biz_data = list(data_with_detail) + list(additional_data)
            else:
                biz_data = data_with_detail[:5]
        else:
            # region이 None인 경우 지역 조건 제외
            biz_data = BizInfo.objects.filter(
                                            Q(possible_industry__contains=biz_industry) \
                                           & Q(revenue__contains=biz_revenue)\
                                           & Q(business_period__contains=biz_business_months) \
                                           & Q(target__contains=biz_employees)
                                           )[:5]
        
        # 공고 추천 데이터 준비
        recommended_notices = []
        pblanc_ids = []
        biz_reception = ""

        for biz in biz_data:
            print(f'biz.reception_start : {biz.reception_start}')
            print(f'biz.reception_end : {biz.reception_end}')
            
            # DateField 객체를 문자열로 변환하여 비교
            start_str = str(biz.reception_start) if biz.reception_start else '1900-01-01'
            end_str = str(biz.reception_end) if biz.reception_end else '9999-12-31'
            
            if start_str == '1900-01-01' and end_str == '9999-12-31':
                biz_reception = "상시접수"
            elif start_str == '1900-01-01' and end_str != '9999-12-31':
                biz_reception = f"{end_str} 까지 접수"
            elif start_str != '1900-01-01' and end_str == '9999-12-31':
                biz_reception = f"{start_str} 부터 자금 소진시까지 접수"
            else:
                biz_reception = f"{start_str} ~ {end_str}"
            
            print(f'biz_reception : {biz_reception}')


            print(f'biz_data : {biz.pblanc_id}')
            pblanc_ids.append(biz.pblanc_id)
            recommended_notices.append({
                'pblanc_id': biz.pblanc_id,
                'title': biz.title,
                'institution': biz.institution_name,
                'apply_period': biz_reception,
                'support_amount': biz.support_field if biz.support_field else "지원규모 미정"
            })

        existing_funds = {
            'kibo_general': 0,  # 일반보증은 별도 없음
            'kibo_ip': float(debt_data.get('tech_guarantee', 0)) * 10000,  # 기술보증기금 = 기보 IP보증
            'sinbo': float(debt_data.get('credit_guarantee', 0)) * 10000,  # 신용보증기금 = 신보
            'jungjin': float(debt_data.get('smba', 0)) * 10000,  # 중진공
            'sojin_innovation': float(debt_data.get('semas_innovation', 0)) * 10000,  # 소진공 혁신성장
            'sojin_lowcredit': float(debt_data.get('semas_lowcredit', 0)) * 10000,  # 소진공 저신용
            'credit_foundation': float(debt_data.get('credit_foundation', 0)) * 10000  # 신용 = 신용보증재단
        }
        company_data['existing_funds'] = existing_funds
        
        print("=== 매핑된 existing_funds ===")
        for key, value in existing_funds.items():
            if value > 0:
                print(f"{key}: {value:,}원")
        print("==============================")
        
        # 신보 기존 사용액 별도 계산 (하위 호환성)
        company_data['existing_sinbo_debt'] = existing_funds['sinbo']
        
        # 추가 필드들 (기본값 설정)
        # 나이 속성에서 CEO 나이 계산 (기본값: 35세)
        age_attribute_value = _get_attribute_value(user, row, '나이')
        calculated_age = _calculate_age_from_data(age_attribute_value)
        company_data['ceo_age'] = calculated_age if calculated_age > 0 else 35
        
        company_data['is_startup'] = company_data['business_months'] <= 36
        
        # 경력은 별도 속성에서 가져오기 (기본값: 5년)
        experience_value = _get_attribute_value(user, row, '경력')
        company_data['experience_years'] = _parse_number(experience_value, 5)  # 기본값 5년
        
        print("=== 수집된 회사 데이터 ===")
        for key, value in company_data.items():
            if key == 'existing_funds':
                print(f"{key}:")
                for fund_key, fund_value in value.items():
                    print(f"  {fund_key}: {fund_value:,}원")
            else:
                print(f"{key}: {value}")
        print("========================")
        
        # 새로운 정책자금 추천 엔진 V2.0 사용
        engine = PolicyFundRecommendationEngineV2()
        recommendation_result = engine.recommend_funds(company_data)
        
        print("=== 추천 엔진 결과 ===")
        print(f"결과 구조: {list(recommendation_result.keys())}")
        print("====================")
        
        # 에러 처리
        if 'error' in recommendation_result:
            return JsonResponse({
                'success': False,
                'error': recommendation_result['error'],
                'details': recommendation_result.get('exclusion_notes', [])
            })
        
        # 추천 자금들을 이전 형식과 호환되도록 변환
        individual_funds = []
        for fund in recommendation_result['recommended_funds']:
            fund_info = {
                'fund_name': fund['fund_name'],
                'limit': fund['limit'],
                'priority': fund.get('priority', 5),
                'institution': fund.get('institution', '미지정'),
                'calculation_note': fund.get('calculation_note', ''),
                'processing_time': fund.get('processing_time', '2-4주'),
                'interest_rate': fund.get('interest_rate', '3.0~6.0%'),
                'required_documents': fund.get('required_documents', ['사업자등록증', '재무제표']),
                'total_limit_after': fund.get('total_limit_after', fund['limit'])  # V2.0 추가 정보
            }
            individual_funds.append(fund_info)
        
        # 상세 자금 내역을 dict 형태로 구성
        detailed_funds_dict = {}
        for fund in individual_funds:
            detailed_funds_dict[fund['fund_name']] = fund['limit']
        
        # 총 추천 금액
        total_amount = recommendation_result['total_additional_amount']
        
        # V2.0 추가 정보 포함한 추천자금 필드 저장 데이터 구성
        recommendation_data = {
            '자금들': detailed_funds_dict,
            '총자금': total_amount,
            '상세정보': individual_funds,
            'pblanc_ids': pblanc_ids,  # 공고 ID 목록 추가
            'v2_info': {
                'version': recommendation_result['system_info']['version'],
                'calculation_time': recommendation_result['calculation_time'],
                'exclusion_notes': recommendation_result['exclusion_notes'],
                'existing_funds_summary': recommendation_result['existing_funds_summary']
            }
        }
        
        # 추천자금 필드에 상세 데이터 저장
        try:
            recommend_attribute = Attribute.objects.get(user=user, name='추천자금')
            recommend_attr_value, created = AttributeValue.objects.get_or_create(
                row=row, 
                attribute=recommend_attribute,
                defaults={'value': json.dumps(recommendation_data, ensure_ascii=False)}
            )
            if not created:
                recommend_attr_value.value = json.dumps(recommendation_data, ensure_ascii=False)
                recommend_attr_value.save()
                
            print(f"추천자금 필드 저장 완료: {'새로 생성' if created else '업데이트'}")
        except Attribute.DoesNotExist:
            print("추천자금 속성이 존재하지 않아 저장을 건너뜀")
        
        # 클라이언트에 반환할 응답 구성
        response_data = {
            'success': True,
            'total_recommended_amount': f"{total_amount:,}원",
            'individual_funds': individual_funds,
            'recommended_notices': recommended_notices,  # 공고 추천 데이터 추가
            'analysis_summary': {
                'total_products': len(individual_funds),
                'confidence': '95%',
                'version': recommendation_result['system_info']['version'],
                'logic_name': recommendation_result['system_info']['logic_name'],
                'calculation_time': recommendation_result['calculation_time'],
                'exclusion_notes': recommendation_result['exclusion_notes'],
                'existing_funds_summary': recommendation_result['existing_funds_summary']
            },
            'engine_info': {
                'version': '7월1일 로직 v2.0',
                'features': ['증액 가능성 정확 계산', '중복 표시 완전 제거', '기존 자금 현황 고려']
            }
        }
        
        print("=== 추천 완료 ===")
        print(f"총 추천 금액: {total_amount:,}원")
        print(f"추천 자금 수: {len(individual_funds)}개")
        print(f"계산 시간: {recommendation_result['calculation_time']}")
        print("================")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        error_msg = f'정책자금 추천 중 오류가 발생했습니다: {str(e)}'
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        })
    
@csrf_exempt
def update_expected_loans(request):
    """
    기대출 속성의 다중 선택 값을 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # 파라미터 검증
        row_id = request.POST.get('row_id')
        attribute = request.POST.get('attribute')
        value = request.POST.get('value', '')
        
        if not row_id or not attribute:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 기대출 속성인지 확인
        if attribute != '기대출':
            return JsonResponse({'success': False, 'error': '기대출 속성만 처리 가능합니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기 또는 생성
        try:
            expected_loans_attr = Attribute.objects.get(name='기대출', user=user)
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type, _ = AttributeType.objects.get_or_create(name='text')
            expected_loans_attr = Attribute.objects.create(
                name='기대출',
                user=user,
                attributeType=text_type
            )
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=expected_loans_attr,
            defaults={'value': value}
        )
        
        if not created:
            attr_value.value = value
            attr_value.save()
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if expected_loans_attr.cascade:
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', value)
        else:
            print(f"속성 '기대출'의 cascade 값: {expected_loans_attr.cascade} - 동기화하지 않음")
        
        return JsonResponse({
            'success': True,
            'message': '기대출 정보가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def update_loan_amount(request):
    """
    기대출 금액을 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})
    
    try:
        # 임시로 user id 1 사용 (나중에 request.user로 변경 가능)
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # JSON 데이터 파싱
        data = json.loads(request.body)
        row_id = data.get('row_id')
        loan_data_str = data.get('loan_data')
        
        if not row_id or not loan_data_str:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # Row 찾기
        row = Row.objects.get(id=row_id, user=user)
        
        # 기대출 속성 가져오기 또는 생성
        try:
            expected_loans_attr = Attribute.objects.get(name='기대출', user=user)
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type = AttributeType.objects.get_or_create(name='text')[0]
            expected_loans_attr = Attribute.objects.create(
                user=user,
                name='기대출',
                attributeType=text_type,
                assential=False
            )
        
        # 기대출 데이터를 JSON 문자열로 저장
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=expected_loans_attr,
            defaults={'value': loan_data_str}
        )
        
        if not created:
            attr_value.value = loan_data_str
            attr_value.save()
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if expected_loans_attr.cascade:
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', loan_data_str)
        else:
            print(f"속성 '기대출'의 cascade 값: {expected_loans_attr.cascade} - 동기화하지 않음")
        
        return JsonResponse({
            'success': True,
            'message': '기대출 금액이 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 금액 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 금액 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def update_debt_field(request):
    """
    기대출 필드를 업데이트하는 함수 (diary_detail.js에서 사용)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        row_id = data.get('row_id')
        debt_data = data.get('debt_data')
        
        if not row_id or not debt_data:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기 또는 생성
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type, _ = AttributeType.objects.get_or_create(name='text')
            debt_attribute = Attribute.objects.create(
                name='기대출',
                user=user,
                attributeType=text_type,
                assential=False
            )
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=debt_attribute,
            defaults={'value': json.dumps(debt_data)}
        )
        
        if not created:
            attr_value.value = json.dumps(debt_data)
            attr_value.save()
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if debt_attribute.cascade:
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', json.dumps(debt_data))
        else:
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade} - 동기화하지 않음")
        
        return JsonResponse({
            'success': True,
            'message': '기대출 정보가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 업데이트 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def get_debt_details(request, row_id):
    """
    기대출 상세 정보를 가져오는 함수
    """
    try:
        # 사용자 정보 가져오기 (고정 ID: 1)
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
            attr_value = AttributeValue.objects.filter(row=row, attribute=debt_attribute).first()
            
            # JSON 데이터 파싱
            try:
                debt_data = json.loads(attr_value.value) if attr_value and attr_value.value else {}
            except json.JSONDecodeError:
                debt_data = {}
                
        except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
            debt_data = {}
        
        return JsonResponse({
            'success': True,
            'debt_data': debt_data
        })
        
    except Exception as e:
        logger.error(f"기대출 정보 조회 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 정보 조회 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def save_debt_details(request):
    """
    기대출 상세 정보를 저장하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        row_id = data.get('row_id')
        debt_data = data.get('debt_data')
        
        if not row_id or not debt_data:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 기대출 속성 가져오기 또는 생성
        try:
            debt_attribute = Attribute.objects.get(user=user, name='기대출')
        except Attribute.DoesNotExist:
            # 기대출 속성이 없으면 생성
            text_type, _ = AttributeType.objects.get_or_create(name='text')
            debt_attribute = Attribute.objects.create(
                name='기대출',
                user=user,
                attributeType=text_type,
                assential=False
            )
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=debt_attribute,
            defaults={'value': json.dumps(debt_data)}
        )
        
        if not created:
            attr_value.value = json.dumps(debt_data)
            attr_value.save()
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if debt_attribute.cascade:
            print(f"=== Cascade 동기화 시작 (save_debt_details) ===")
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(debt_data)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '기대출', json.dumps(debt_data))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 기대출 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (save_debt_details) ===")
        else:
            print(f"속성 '기대출'의 cascade 값: {debt_attribute.cascade} - 동기화하지 않음")
        
        return JsonResponse({
            'success': True,
            'message': '기대출 정보가 성공적으로 저장되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"기대출 저장 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'기대출 저장 중 오류가 발생했습니다: {str(e)}'
        })
    
def _get_attribute_value(user, row, attribute_name):
    """속성 값을 가져오는 헬퍼 함수"""
    try:
        attribute = Attribute.objects.get(user=user, name=attribute_name)
        attr_value = AttributeValue.objects.filter(row=row, attribute=attribute).first()
        return attr_value.value if attr_value else None
    except (Attribute.DoesNotExist, AttributeValue.DoesNotExist):
        return None


def _get_debt_data(user, row):
    """기대출 데이터를 가져오는 헬퍼 함수"""
    try:
        attribute = Attribute.objects.get(user=user, name='기대출')
        attr_value = AttributeValue.objects.filter(row=row, attribute=attribute).first()
        
        if attr_value and attr_value.value:
            if isinstance(attr_value.value, dict):
                return attr_value.value
            elif isinstance(attr_value.value, str) and attr_value.value.startswith('{'):
                return json.loads(attr_value.value)
        
        return {}
    except (Attribute.DoesNotExist, AttributeValue.DoesNotExist, json.JSONDecodeError):
        return {}


def _parse_number(value, default=0):
    """문자열이나 숫자를 정수로 변환하는 헬퍼 함수"""
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return int(value)
    
    if isinstance(value, str):
        # 숫자가 아닌 문자 제거 후 변환
        numbers_only = re.sub(r'[^\d.]', '', value)
        try:
            return int(float(numbers_only)) if numbers_only else default
        except ValueError:
            return default
    
    return default


def _calculate_business_months(opening_date_str):
    """개업년월로부터 업력(개월수) 계산하는 헬퍼 함수"""
    if not opening_date_str:
        return 12  # 기본값
    
    try:
        # 다양한 날짜 형식 처리
        if isinstance(opening_date_str, str):
            # YYYY-MM-DD 형식
            if '-' in opening_date_str and len(opening_date_str) >= 7:
                opening_date = datetime.strptime(opening_date_str[:7], '%Y-%m')
            # YYYY년 MM월 형식
            elif '년' in opening_date_str and '월' in opening_date_str:
                # 예: "2023년 5월"
                match = re.search(r'(\d{4})년\s*(\d{1,2})월', opening_date_str)
                if match:
                    year, month = int(match.group(1)), int(match.group(2))
                    opening_date = datetime(year, month, 1)
                else:
                    return 12
            else:
                return 12
        
        # 현재 날짜와의 차이 계산
        now = datetime.now()
        months_diff = (now.year - opening_date.year) * 12 + (now.month - opening_date.month)
        return max(1, months_diff)  # 최소 1개월
        
    except (ValueError, AttributeError):
        return 12  # 파싱 실패 시 기본값


def _calculate_age_from_data(age_data_str):
    """나이 데이터에서 실제 나이를 계산하는 헬퍼 함수"""
    
    if not age_data_str:
        return 35  # 기본값
    
    try:
        # JSON 문자열인 경우 파싱
        if isinstance(age_data_str, str) and age_data_str.startswith('{'):
            age_data = json.loads(age_data_str)
        elif isinstance(age_data_str, dict):
            age_data = age_data_str
        else:
            return 35  # 기본값
        
        # 생년월일이 있는 경우 실제 나이 계산
        if age_data.get('birth_date'):
            birth_date_str = age_data['birth_date']
            try:
                # YY.MM.DD 형식 파싱
                if '.' in birth_date_str and len(birth_date_str) == 8:
                    year_part, month_part, day_part = birth_date_str.split('.')
                    year = int(year_part)
                    month = int(month_part)
                    day = int(day_part)
                    
                    # 2자리 연도를 4자리로 변환 (50 이상이면 19xx, 미만이면 20xx)
                    if year >= 50:
                        year += 1900
                    else:
                        year += 2000
                    
                    birth_date = datetime(year, month, day)
                    current_date = datetime.now()
                    
                    # 나이 계산
                    age = current_date.year - birth_date.year
                    if current_date.month < birth_date.month or (current_date.month == birth_date.month and current_date.day < birth_date.day):
                        age -= 1
                    
                    return max(age, 1)  # 최소 1세
                    
            except (ValueError, IndexError) as e:
                print(f"생년월일 파싱 오류: {e}")
                
        # 연령대 선택이 있는 경우
        elif age_data.get('age_range'):
            age_range = age_data['age_range']
            if age_range == 'under40':
                return 35
            elif age_range == 'over40':
                return 40
        
        return 35  # 기본값
        
    except Exception as e:
        print(f"나이 계산 오류: {e}")
        return 35  # 기본값
    
@csrf_exempt
def get_recommended_notices(request):
    """저장된 pblanc_ids를 이용해 공고 정보를 반환하는 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})
    
    try:
        data = json.loads(request.body)
        pblanc_ids = data.get('pblanc_ids', [])
        
        if not pblanc_ids:
            return JsonResponse({'success': True, 'recommended_notices': []})
        
        # pblanc_ids를 이용해 BizInfo에서 공고 정보 조회
        biz_data = BizInfo.objects.filter(pblanc_id__in=pblanc_ids)
        
        recommended_notices = []
        for biz in biz_data:
            # 접수 기간 처리
            if biz.reception_start and biz.reception_end:
                start_str = str(biz.reception_start)
                end_str = str(biz.reception_end)
                
                if start_str == "1900-01-01" and end_str == "9999-12-31":
                    apply_period = "상시접수"
                elif start_str == "1900-01-01":
                    apply_period = f"~ {end_str}"
                elif end_str == "9999-12-31":
                    apply_period = "상시접수 (지원금 소모 시 까지)"
                else:
                    apply_period = f"{start_str} ~ {end_str}"
            else:
                apply_period = "상시접수"
            
            recommended_notices.append({
                'pblanc_id': biz.pblanc_id,
                'title': biz.title,
                'institution': biz.institution_name,
                'apply_period': apply_period,
                'support_amount': biz.support_field if biz.support_field else "지원규모 미정"
            })
        
        return JsonResponse({
            'success': True,
            'recommended_notices': recommended_notices
        })
        
    except Exception as e:
        print(f"공고 정보 조회 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': '공고 정보를 조회할 수 없습니다.'
        })
    
def build_detail_region_exclude_query(region, detail_region):
        """다른 상세지역만 특정되어 있는 경우를 제외하는 쿼리 구성"""
        # regionDetails에 정의된 실제 상세지역 목록
        region_details = {
            "서울": ["강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"],
            "경기": ["수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시", "동두천시", "안산시", "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시", "용인시", "파주시", "이천시", "안성시", "김포시", "화성시", "광주시", "여주시", "양평군", "고양군", "연천군", "포천군", "가평군"],
            "인천": ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"],
            "강원": ["춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시", "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"],
            "경북": ["포항시", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시", "경산시", "군위군", "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "예천군", "봉화군", "울진군", "울릉군"],
            "경남": ["창원시", "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시", "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"],
            "부산": ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"],
            "대구": ["중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군"],
            "울산": ["중구", "남구", "동구", "북구", "울주군"],
            "대전": ["중구", "동구", "서구", "유성구", "대덕구"],
            "충북": ["청주시", "충주시", "제천시", "보은군", "옥천군", "영동군", "증평군", "진천군", "괴산군", "음성군", "단양군"],
            "충남": ["천안시", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시", "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"],
            "전북": ["전주시", "군산시", "익산시", "정읍시", "남원시", "김제시", "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"],
            "전남": ["목포시", "여수시", "순천시", "나주시", "광양시", "담양군", "곡성군", "구례군", "고흥군", "보성군", "화순군", "장흥군", "강진군", "해남군", "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"],
            "광주": ["동구", "서구", "남구", "북구", "광산구"],
            "제주": ["제주시", "서귀포시"],
            "세종": ["세종특별자치시"]
        }
        
        # 해당 지역의 상세지역 목록 가져오기
        if region in region_details:
            detail_regions = region_details[region]
            
            # detail_region을 제외한 다른 상세지역들로 쿼리 구성
            other_detail_regions = [dr for dr in detail_regions if dr != detail_region]
            
            # 다른 상세지역이 포함된 데이터를 제외하는 쿼리
            exclude_queries = []
            for other_detail in other_detail_regions:
                exclude_queries.extend([
                    Q(noti_summary__contains=other_detail),
                    Q(hashtag__contains=other_detail),
                    Q(content__contains=other_detail),
                    Q(title__contains=other_detail),
                    Q(region__contains=other_detail)
                ])
            
            # OR 조건으로 결합 (하나라도 포함되면 제외)
            if exclude_queries:
                combined_query = exclude_queries[0]
                for query in exclude_queries[1:]:
                    combined_query |= query
                return combined_query
        
        # 해당 지역의 상세지역 정보가 없으면 빈 쿼리 반환
        return Q()