#!/usr/bin/env python
"""
비밀번호 암호화 테스트 스크립트
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PO.settings')

try:
    django.setup()
    print("Django 설정 성공")
    
    from django.contrib.auth.hashers import make_password, check_password
    from diary.models import User
    
    print("모듈 import 성공")
    
    # 테스트 비밀번호
    test_password = "test123"
    hashed_password = make_password(test_password)
    
    print(f"원본 비밀번호: {test_password}")
    print(f"암호화된 비밀번호: {hashed_password}")
    
    # 비밀번호 검증 테스트
    is_valid = check_password(test_password, hashed_password)
    print(f"비밀번호 검증 결과: {is_valid}")
    
    # 데이터베이스에서 사용자 확인
    users = User.objects.all()
    print(f"총 사용자 수: {users.count()}")
    
    for user in users:
        print(f"사용자: {user.email}, 비밀번호 암호화 여부: {user.password.startswith('pbkdf2_sha256$')}")
    
except Exception as e:
    print(f"오류 발생: {str(e)}")
    import traceback
    traceback.print_exc() 