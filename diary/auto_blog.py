from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver import ActionChains
import traceback
import time
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.core.cache import cache
import json
import os
import uuid
import hashlib
from .session_handlers import cleanup_session_cache, get_active_sessions
from .models import User
from django.contrib.auth.hashers import check_password

def blog_account_check_api(request):
    """자동 블로그 exe 계정 확인 API"""
    try: 
        user_id = request.GET.get('user_id')
        password = request.GET.get('password')
        version = request.GET.get('version')
        pc_info = request.GET.get('pc_info')
        message = ''

        # 현재 배포중인 버전은 1.0
        # 조건 변경 시 메세지 나타남
        if version != '1.0':
            message = '자금왕에서 새로운 버전을 다운로드해주세요!'

        # 비정상적인 요청 처리
        if not user_id or not password:
            return JsonResponse({
                'success': False,
                'error': 'ID와 비밀번호를 확인하세요'
            })
        else:
            
            try:
                member = User.objects.get(email=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '아이디 또는 비밀번호가 일치하지 않습니다.'
                })

            # 사용 기간 만료 확인
            if member.is_expired():
                return JsonResponse({
                    'success': False,
                    'error': '사용기간이 만료되었습니다.'
                })
            
            if check_password(password, member.password):
                # pc_info 처리 로직
                if pc_info:
                    # 기존 pc_info가 있는지 확인
                    if member.pc_info and member.pc_info != {}:
                        # 기존 pc_info와 비교
                        if member.pc_info != pc_info:
                            return JsonResponse({
                                'success': False,
                                'error': '기존 PC에서 이용해주세요.'
                            })
                    else:
                        # pc_info가 비어있으면 새로 저장
                        member.pc_info = pc_info
                        member.save()
                
                return JsonResponse({
                        'success': True,
                        'message': '로그인되었습니다.',
                        'use_date': member.use_date,
                        'version_message': message
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '아이디 또는 비밀번호가 일치하지 않습니다.'
                })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
                
