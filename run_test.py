#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 실행 스크립트
"""

import subprocess
import sys
import os

def main():
    print("🚀 정책자금 추천 엔진 테스트 시작")
    print("="*50)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f"현재 디렉토리: {current_dir}")
    
    # test_funding_calculator.py 파일 존재 확인
    if not os.path.exists('test_funding_calculator.py'):
        print("❌ test_funding_calculator.py 파일을 찾을 수 없습니다.")
        return
    
    try:
        # 테스트 실행
        print("📋 테스트 실행 중...")
        result = subprocess.run([sys.executable, 'test_funding_calculator.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        
        # 결과 출력
        print("📊 테스트 결과:")
        print("-" * 50)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ 오류 메시지:")
            print("-" * 50)
            print(result.stderr)
        
        # 결과 파일 확인
        if os.path.exists('test_results.json'):
            print("\n✅ 테스트 결과가 test_results.json에 저장되었습니다.")
        else:
            print("\n⚠️ test_results.json 파일이 생성되지 않았습니다.")
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
