#!/usr/bin/env python
"""
Attribute ID 변경 스크립트 실행 파일
"""

from update_attribute_id import update_attribute_id, update_attribute_order, show_user_attributes

def main():
    print("=== Attribute ID 변경 도구 ===")
    
    # 사용자 ID 입력
    user_id = int(input("사용자 ID를 입력하세요: "))
    
    # 현재 Attribute 목록 확인
    print("\n현재 Attribute 목록:")
    show_user_attributes(user_id)
    
    print("\n=== 작업 선택 ===")
    print("1. 단일 Attribute ID 변경")
    print("2. 여러 Attribute 순서 일괄 변경")
    print("3. Attribute 목록만 확인")
    
    choice = input("\n작업을 선택하세요 (1-3): ")
    
    if choice == "1":
        # 단일 Attribute ID 변경
        old_id = int(input("변경할 Attribute ID: "))
        new_id = int(input("새로운 Attribute ID: "))
        
        print(f"\nAttribute ID {old_id}를 {new_id}로 변경합니다...")
        success = update_attribute_id(old_id, new_id, user_id)
        
        if success:
            print("\n✅ 변경 완료! 변경된 목록:")
            show_user_attributes(user_id)
        else:
            print("\n❌ 변경 실패!")
    
    elif choice == "2":
        # 여러 Attribute 순서 일괄 변경
        print("\n변경할 Attribute ID들을 입력하세요 (예: 16,18 17,19)")
        print("형식: old_id,new_id old_id,new_id ...")
        
        input_text = input("변경할 ID들: ")
        attribute_orders = []
        
        try:
            for pair in input_text.strip().split():
                old_id, new_id = map(int, pair.split(','))
                attribute_orders.append((old_id, new_id))
            
            print(f"\n{len(attribute_orders)}개의 Attribute를 변경합니다...")
            success = update_attribute_order(user_id, attribute_orders)
            
            if success:
                print("\n✅ 일괄 변경 완료! 변경된 목록:")
                show_user_attributes(user_id)
            else:
                print("\n❌ 일괄 변경 실패!")
                
        except ValueError:
            print("❌ 잘못된 형식입니다. 'old_id,new_id' 형식으로 입력하세요.")
    
    elif choice == "3":
        # Attribute 목록만 확인
        print("\n현재 Attribute 목록:")
        show_user_attributes(user_id)
    
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main() 