#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 결과 JSON 파일을 보기 좋게 표시하는 뷰어
"""

import json
import os
from datetime import datetime

def format_amount(amount):
    """금액을 보기 좋게 포맷팅"""
    if amount >= 100000000:
        return f"{amount:,}원 ({amount//100000000}억원)"
    elif amount >= 10000000:
        return f"{amount:,}원 ({amount//10000000}천만원)"
    else:
        return f"{amount:,}원"

def display_test_result(result):
    """단일 테스트 결과 표시"""
    print(f"\n{'='*80}")
    print(f"🧪 테스트 ID: {result['test_id']}")
    print(f"📝 설명: {result['description']}")
    print(f"🎯 테스트 포커스: {result['test_focus']}")
    print(f"📊 상태: {result['status']}")
    print(f"{'='*80}")
    
    # 입력 조건 표시
    print(f"\n📋 입력 조건:")
    print(f"{'─'*40} 원본 데이터 {'─'*40}")
    original_data = result['input_conditions']['original_data']
    for key, value in original_data.items():
        if isinstance(value, int) and value > 1000000:
            print(f"  {key}: {value:,}원 ({value//100000000}억원)")
        elif isinstance(value, int):
            print(f"  {key}: {value:,}")
        else:
            print(f"  {key}: {value}")
    
    print(f"{'─'*40} 변환된 데이터 {'─'*40}")
    converted_data = result['input_conditions']['converted_data']
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
    
    # 결과 표시
    print(f"\n📊 결과:")
    print(f"{'─'*40} 예상 결과 {'─'*40}")
    for i, expected in enumerate(result['results']['expected'], 1):
        print(f"  {i:2d}. {expected}")
    
    print(f"{'─'*40} 실제 결과 {'─'*40}")
    for i, actual in enumerate(result['results']['actual'], 1):
        print(f"  {i:2d}. {actual}")
    
    # 비교 결과
    comparison = result['comparison']
    print(f"\n🔍 비교 결과:")
    print(f"  일치 여부: {'✅ 일치' if comparison['is_match'] else '❌ 불일치'}")
    
    if not comparison['is_match']:
        if comparison['only_expected']:
            print(f"  🔴 예상에만 있음 ({len(comparison['only_expected'])}개):")
            for item in comparison['only_expected']:
                print(f"    • {item}")
        
        if comparison['only_actual']:
            print(f"  🔵 실제에만 있음 ({len(comparison['only_actual'])}개):")
            for item in comparison['only_actual']:
                print(f"    • {item}")
    
    # 금액 정보
    total_amount = result['results']['total_amount']
    funds_count = result['results']['funds_count']
    print(f"\n💰 금액 정보:")
    print(f"  총 추천 금액: {format_amount(total_amount)}")
    print(f"  추천 자금 수: {funds_count}개")
    
    # 오류 정보 (있는 경우)
    if 'error' in result:
        print(f"\n❌ 오류 정보:")
        print(f"  {result['error']}")

def display_summary(results):
    """전체 요약 표시"""
    total_tests = len(results)
    pass_count = len([r for r in results if r['status'] == 'PASS'])
    fail_count = len([r for r in results if r['status'] == 'FAIL'])
    error_count = len([r for r in results if r['status'] == 'ERROR'])
    
    print(f"\n{'='*80}")
    print("🎯 테스트 결과 요약")
    print(f"{'='*80}")
    print(f"📊 총 테스트 수: {total_tests}")
    print(f"✅ 통과: {pass_count} ({(pass_count/total_tests*100):.1f}%)")
    print(f"❌ 실패: {fail_count} ({(fail_count/total_tests*100):.1f}%)")
    print(f"⚠️ 오류: {error_count} ({(error_count/total_tests*100):.1f}%)")
    
    # 그룹별 분석
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

def main():
    """메인 함수"""
    json_file = 'test_results.json'
    
    if not os.path.exists(json_file):
        print(f"❌ {json_file} 파일을 찾을 수 없습니다.")
        print("먼저 test_funding_calculator.py를 실행하여 테스트를 수행하세요.")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print("🔍 테스트 결과 뷰어")
        print(f"📁 파일: {json_file}")
        print(f"📅 로드 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 전체 요약 표시
        display_summary(results)
        
        # 사용자 선택
        print(f"\n{'='*80}")
        print("📋 상세 보기 옵션")
        print(f"{'='*80}")
        print("1. 모든 테스트 결과 보기")
        print("2. 실패한 테스트만 보기")
        print("3. 특정 테스트 ID로 검색")
        print("4. 종료")
        
        while True:
            try:
                choice = input("\n선택하세요 (1-4): ").strip()
                
                if choice == '1':
                    print(f"\n{'='*80}")
                    print("📋 모든 테스트 결과")
                    print(f"{'='*80}")
                    for result in results:
                        display_test_result(result)
                        input("\n계속하려면 Enter를 누르세요...")
                
                elif choice == '2':
                    failed_results = [r for r in results if r['status'] in ['FAIL', 'ERROR']]
                    if not failed_results:
                        print("✅ 실패한 테스트가 없습니다!")
                    else:
                        print(f"\n{'='*80}")
                        print(f"❌ 실패한 테스트 ({len(failed_results)}개)")
                        print(f"{'='*80}")
                        for result in failed_results:
                            display_test_result(result)
                            input("\n계속하려면 Enter를 누르세요...")
                
                elif choice == '3':
                    test_id = input("테스트 ID를 입력하세요 (예: TEST_001): ").strip().upper()
                    found = False
                    for result in results:
                        if result['test_id'] == test_id:
                            display_test_result(result)
                            found = True
                            break
                    if not found:
                        print(f"❌ {test_id}를 찾을 수 없습니다.")
                
                elif choice == '4':
                    print("👋 종료합니다.")
                    break
                
                else:
                    print("❌ 잘못된 선택입니다. 1-4 중에서 선택하세요.")
                    
            except KeyboardInterrupt:
                print("\n👋 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {str(e)}")
                
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {str(e)}")

if __name__ == "__main__":
    main()
