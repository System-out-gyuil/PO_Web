# convert_debt_to_billion.py
import os
import django
import json

# ✅ Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")
django.setup()

from diary.models import User, Attribute, AttributeValue

def convert_debt_to_billion():
    """기대출 데이터를 만원 단위에서 억원 단위로 변환"""
    print("=== 기대출 단위 변환 시작 ===")
    print("만원 단위 → 억원 단위 변환")
    
    try:
        # 기대출 속성을 가져오기
        debt_attributes = Attribute.objects.filter(name='기대출')
        print(f"기대출 속성 수: {debt_attributes.count()}")
        
        if debt_attributes.count() == 0:
            print("❌ 기대출 속성이 존재하지 않습니다.")
            return
        
        converted_count = 0
        error_count = 0
        total_count = 0
        
        for debt_attr in debt_attributes:
            print(f"\n--- 사용자 {debt_attr.user.id} 처리 중 ---")
            
            # 해당 속성의 모든 값들 조회
            attr_values = AttributeValue.objects.filter(attribute=debt_attr)
            print(f"처리할 행 수: {attr_values.count()}")
            
            for attr_value in attr_values:
                total_count += 1
                try:
                    current_value = attr_value.value
                    
                    if not current_value:
                        continue
                    
                    # JSON 문자열인 경우 파싱
                    if isinstance(current_value, str):
                        try:
                            debt_data = json.loads(current_value)
                        except json.JSONDecodeError:
                            print(f"⚠️ JSON 파싱 실패 (행 {attr_value.row.id}): {current_value[:100]}...")
                            continue
                    elif isinstance(current_value, dict):
                        debt_data = current_value
                    else:
                        print(f"⚠️ 지원하지 않는 데이터 타입 (행 {attr_value.row.id}): {type(current_value)}")
                        continue
                    
                    # 8개 키값 변환
                    converted_data = {}
                    original_data = debt_data.copy()
                    has_changes = False
                    
                    # 변환할 키값들
                    debt_keys = [
                        'tech_guarantee',      # 기보 IP보증 (기술보증기금)
                        'credit_guarantee',    # 신보 (신용보증기금)
                        'smba',                # 중진공
                        'semas_innovation',    # 소진공 혁신성장
                        'semas_lowcredit',     # 소진공 저신용
                        'credit_foundation',   # 신용보증재단
                        'collateral',          # 담보
                        'credit'               # 신용
                    ]
                    
                    print(f"  행 {attr_value.row.id}:")
                    
                    for key in debt_keys:
                        if key in debt_data and debt_data[key]:
                            try:
                                # 만원 단위 값을 억원 단위로 변환
                                original_value = float(debt_data[key])
                                if original_value > 10:  # 10을 초과하는 경우 (만원 단위로 추정)
                                    converted_value = round(original_value / 10000, 2)  # 만원 → 억원 (소수점 2자리)
                                    converted_data[key] = converted_value
                                    print(f"    {key}: {original_value} → {converted_value}억원")
                                    has_changes = True
                                else:
                                    # 이미 억원 단위인 경우 그대로 유지
                                    converted_data[key] = original_value
                                    print(f"    {key}: {original_value}억원 (유지)")
                            except (ValueError, TypeError) as e:
                                print(f"    ⚠️ {key} 변환 오류: {debt_data[key]} - {e}")
                                converted_data[key] = 0
                        else:
                            converted_data[key] = 0
                    
                    # 변환된 데이터 저장
                    if has_changes:
                        attr_value.value = converted_data
                        attr_value.save()
                        converted_count += 1
                        print(f"    ✅ 변환 완료 및 저장")
                    else:
                        print(f"    ℹ️ 변환할 데이터 없음")
                    
                except Exception as e:
                    print(f"    ❌ 행 {attr_value.row.id} 처리 오류: {e}")
                    error_count += 1
                    continue
        
        print(f"\n=== 변환 완료 ===")
        print(f"✅ 성공: {converted_count}개 행")
        print(f"❌ 오류: {error_count}개 행")
        print(f"�� 총 처리: {total_count}개 행")
        print(f"🎯 변환률: {(converted_count/total_count*100):.1f}%")
        
    except Exception as e:
        print(f"❌ 전체 처리 오류: {e}")
        raise

def reverse_convert_debt_to_million():
    """억원 단위에서 만원 단위로 되돌리기 (롤백용)"""
    print("=== 기대출 단위 롤백 시작 ===")
    print("억원 단위 → 만원 단위 변환")
    
    try:
        debt_attributes = Attribute.objects.filter(name='기대출')
        converted_count = 0
        total_count = 0
        
        for debt_attr in debt_attributes:
            print(f"\n--- 사용자 {debt_attr.user.id} 롤백 처리 중 ---")
            
            attr_values = AttributeValue.objects.filter(attribute=debt_attr)
            print(f"처리할 행 수: {attr_values.count()}")
            
            for attr_value in attr_values:
                total_count += 1
                try:
                    current_value = attr_value.value
                    
                    if not current_value:
                        continue
                    
                    if isinstance(current_value, str):
                        try:
                            debt_data = json.loads(current_value)
                        except json.JSONDecodeError:
                            continue
                    elif isinstance(current_value, dict):
                        debt_data = current_value
                    else:
                        continue
                    # 8개 키값을 만원 단위로 되돌리기
                    # {"tech_guarantee": 1, "credit_guarantee": 1, "credit_foundation": 1, "smba": 1, "credit": 1, "collateral": 1, "semas_lowcredit": 1, "semas_innovation": 1}
                    converted_data = {}
                    has_changes = False
                    debt_keys = [
                        'tech_guarantee', 'credit_guarantee', 'smba', 
                        'semas_innovation', 'semas_lowcredit', 'credit_foundation', 
                        'collateral', 'credit'
                    ]
                    
                    print(f"  행 {attr_value.row.id}:")
                    
                    for key in debt_keys:
                        if key in debt_data and debt_data[key]:
                            try:
                                original_value = float(debt_data[key])
                                if original_value < 1:  # 1 미만인 경우 (억원 단위로 추정)
                                    converted_value = int(original_value * 10000)  # 억원 → 만원
                                    converted_data[key] = converted_value
                                    print(f"    {key}: {original_value}억원 → {converted_value}만원")
                                    has_changes = True
                                else:
                                    converted_data[key] = original_value
                                    print(f"    {key}: {original_value}만원 (유지)")
                            except (ValueError, TypeError):
                                converted_data[key] = 0
                        else:
                            converted_data[key] = 0
                    
                    if has_changes:
                        attr_value.value = converted_data
                        attr_value.save()
                        converted_count += 1
                        print(f"    ✅ 롤백 완료 및 저장")
                    else:
                        print(f"    ℹ️ 롤백할 데이터 없음")
                    
                except Exception as e:
                    print(f"    ❌ 롤백 오류: {e}")
                    continue
        
        print(f"\n=== 롤백 완료 ===")
        print(f"✅ 롤백 완료: {converted_count}개 행")
        print(f"�� 총 처리: {total_count}개 행")
        
    except Exception as e:
        print(f"❌ 롤백 처리 오류: {e}")
        raise

def show_debt_data_sample():
    """기대출 데이터 샘플 확인"""
    print("=== 기대출 데이터 샘플 확인 ===")
    
    try:
        debt_attributes = Attribute.objects.filter(name='기대출')
        
        if debt_attributes.count() == 0:
            print("❌ 기대출 속성이 존재하지 않습니다.")
            return
        
        # 첫 번째 사용자의 데이터만 샘플로 확인
        debt_attr = debt_attributes.first()
        attr_values = AttributeValue.objects.filter(attribute=debt_attr)[:3]  # 처음 3개만
        
        print(f"사용자 {debt_attr.user.id}의 기대출 데이터 샘플:")
        
        for i, attr_value in enumerate(attr_values, 1):
            print(f"\n--- 샘플 {i} (행 {attr_value.row.id}) ---")
            print(f"데이터 타입: {type(attr_value.value)}")
            print(f"데이터 내용: {attr_value.value}")
            
    except Exception as e:
        print(f"❌ 샘플 확인 오류: {e}")

if __name__ == "__main__":
    print("🚀 기대출 단위 변환 스크립트 시작")
    print("=" * 50)
    
    # 메뉴 선택
    while True:
        print("\n📋 메뉴를 선택하세요:")
        print("1. 만원 → 억원 변환 (실행)")
        print("2. 억원 → 만원 롤백 (되돌리기)")
        print("3. 데이터 샘플 확인")
        print("4. 종료")
        
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            print("\n⚠️ 주의: 이 작업은 되돌릴 수 있습니다. 계속하시겠습니까? (y/N)")
            confirm = input("확인: ").strip().lower()
            if confirm in ['y', 'yes']:
                convert_debt_to_billion()
            else:
                print("❌ 변환을 취소했습니다.")
        
        elif choice == "2":
            print("\n⚠️ 주의: 롤백을 진행합니다. 계속하시겠습니까? (y/N)")
            confirm = input("확인: ").strip().lower()
            if confirm in ['y', 'yes']:
                reverse_convert_debt_to_million()
            else:
                print("❌ 롤백을 취소했습니다.")
        
        elif choice == "3":
            show_debt_data_sample()
        
        elif choice == "4":
            print("👋 스크립트를 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요.")
        
        print("\n" + "=" * 50)