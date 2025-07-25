#!/usr/bin/env python
"""
기존 사용자들의 비밀번호를 암호화하는 마이그레이션 스크립트
"""
import os
import sys
import django

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.insert(0, project_dir)

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PO.settings')

try:
    django.setup()
    print("Django 설정 성공")
    
    from django.contrib.auth.hashers import make_password
    from diary.models import User
    
    print("모듈 import 성공")
    
    def migrate_passwords():
        """
        기존 사용자들의 평문 비밀번호를 암호화된 형태로 변경
        """
        print("비밀번호 마이그레이션을 시작합니다...")
        
        # 모든 사용자 조회
        users = User.objects.all()
        updated_count = 0
        
        for user in users:
            # 이미 암호화된 비밀번호인지 확인 (make_password로 생성된 비밀번호는 특정 패턴을 가짐)
            if not user.password.startswith('pbkdf2_sha256$'):
                # 평문 비밀번호를 암호화
                hashed_password = make_password(user.password)
                user.password = hashed_password
                user.save()
                updated_count += 1
                print(f"사용자 {user.email}의 비밀번호를 암호화했습니다.")
        
        print(f"마이그레이션 완료: {updated_count}명의 사용자 비밀번호가 암호화되었습니다.")

    def check_password_encryption():
        """
        현재 데이터베이스의 비밀번호 암호화 상태를 확인
        """
        print("비밀번호 암호화 상태를 확인합니다...")
        
        users = User.objects.all()
        encrypted_count = 0
        plain_count = 0
        
        for user in users:
            if user.password.startswith('pbkdf2_sha256$'):
                encrypted_count += 1
            else:
                plain_count += 1
                print(f"평문 비밀번호 발견: {user.email}")
        
        print(f"암호화된 비밀번호: {encrypted_count}개")
        print(f"평문 비밀번호: {plain_count}개")

    if __name__ == '__main__':
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'migrate':
                migrate_passwords()
            elif command == 'check':
                check_password_encryption()
            else:
                print("사용법:")
                print("python migrate_passwords.py migrate  # 비밀번호 암호화")
                print("python migrate_passwords.py check    # 암호화 상태 확인")
        else:
            print("사용법:")
            print("python migrate_passwords.py migrate  # 비밀번호 암호화")
            print("python migrate_passwords.py check    # 암호화 상태 확인")

except Exception as e:
    print(f"Django 설정 또는 모듈 import 오류: {str(e)}")
    print("현재 디렉토리:", os.getcwd())
    print("Python 경로:", sys.path)
    import traceback
    traceback.print_exc() 