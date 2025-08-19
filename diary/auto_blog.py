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

# 전역 변수로 현재 세션 ID 관리
current_session_id = None

# Redis 연결 디버깅을 위한 함수들
def check_redis_connection():
    """Redis 연결 상태 확인"""
    try:
        from django_redis import get_redis_connection
        redis_client = get_redis_connection("default")
        redis_client.ping()
        print("✅ Redis 연결 정상")
        return True
    except Exception as e:
        print(f"❌ Redis 연결 실패: {str(e)}")
        return False

def debug_cache_keys(session_id=None):
    """캐시 키 디버깅"""
    try:
        from django_redis import get_redis_connection
        redis_client = get_redis_connection("default")
        
        if session_id:
            # 특정 세션 관련 키 검색
            pattern = f"*{session_id}*"
        else:
            # 모든 blog_status 키 검색
            pattern = "*blog_status*"
        
        keys = redis_client.keys(pattern)
        print(f"📊 Redis 키 검색 결과 (패턴: {pattern}):")
        for key in keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            try:
                value = cache.get(key_str)
                print(f"  - {key_str}: {value}")
            except Exception as e:
                print(f"  - {key_str}: 조회 실패 ({str(e)})")
        
        return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
    except Exception as e:
        print(f"❌ 캐시 키 디버깅 실패: {str(e)}")
        return []

def set_current_session_id(session_id):
    """현재 세션 ID 설정"""
    global current_session_id
    current_session_id = session_id
    print(f"🔧 현재 세션 ID 설정: {session_id}")

def get_current_session_id():
    """현재 세션 ID 반환"""
    global current_session_id
    return current_session_id

def generate_session_id(request):
    """사용자별 고유 세션 ID 생성"""
    # IP 주소와 User-Agent를 조합하여 고유 ID 생성
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    # 세션 ID가 이미 있으면 재사용
    session_id = request.session.get('blog_session_id')
    if not session_id:
        # 새로운 세션 ID 생성
        unique_string = f"{client_ip}:{user_agent}:{datetime.now().isoformat()}"
        session_id = hashlib.md5(unique_string.encode()).hexdigest()[:16]
        request.session['blog_session_id'] = session_id
    
    # 전역 변수에도 설정
    set_current_session_id(session_id)
    
    return session_id

def get_cache_key(session_id, key_name='blog_status'):
    """세션별 캐시 키 생성"""
    return f"blog_status_{session_id}_{key_name}"

def update_status(step, title='', content='', progress=0, session_id=None):
    """실시간 상태 업데이트 함수 - 세션별 Redis 캐시 사용"""
    # 세션 ID가 없으면 전역 변수에서 가져오기
    if not session_id:
        session_id = get_current_session_id()
    
    if not session_id:
        print("⚠️ 세션 ID가 없어 기본 키를 사용합니다.")
        cache_key = 'blog_status'
    else:
        cache_key = get_cache_key(session_id, 'blog_status')
    
    status_data = {
        'step': step,
        'title': title,
        'content': content,
        'progress': progress,
        'timestamp': datetime.now().isoformat(),
        'session_id': session_id  # 세션 ID도 함께 저장
    }
    
    # Redis 캐시에 상태 저장 (예외 처리 강화)
    try:
        cache.set(cache_key, status_data, 1800)
        print(f"📊 상태 업데이트 [{session_id}]: {step} - {title} - {content[:50]}{'...' if len(content) > 50 else ''}")
        print(f"📊 Redis에 저장된 상태 [{cache_key}]: {status_data}")
    except Exception as e:
        print(f"⚠️ Redis 캐시 저장 실패 [{cache_key}]: {str(e)}")
        # Redis 실패 시 로컬 변수에 임시 저장
        global _local_cache
        if '_local_cache' not in globals():
            _local_cache = {}
        _local_cache[cache_key] = status_data
        print(f"📊 로컬 캐시에 임시 저장: {cache_key}")

def get_status_safe(cache_key, session_id=None):
    """안전한 상태 조회 함수 - Redis 실패 시 로컬 캐시 사용"""
    try:
        status_data = cache.get(cache_key)
        if status_data:
            return status_data
    except Exception as e:
        print(f"⚠️ Redis 캐시 조회 실패 [{cache_key}]: {str(e)}")
    
    # Redis 실패 시 로컬 캐시 확인
    global _local_cache
    if '_local_cache' in globals() and cache_key in _local_cache:
        print(f"📊 로컬 캐시에서 조회: {cache_key}")
        return _local_cache[cache_key]
    
    return None

@csrf_exempt
@require_http_methods(["POST"])
def upload_blog_file(request):
    """
    블로그 텍스트 파일 업로드 처리 - 파일 저장 없이 내용만 출력
    """
    try:
        # Redis 연결 상태 먼저 확인
        redis_connected = check_redis_connection()
        print(f"📊 블로그 업로드 시작 - Redis 연결: {'정상' if redis_connected else '실패'}")
        
        # 사용자별 고유 세션 ID 생성
        session_id = generate_session_id(request)
        print(f"📊 새로운 블로그 작성 세션 시작: {session_id}")
        print(f"📊 세션 ID 타입: {type(session_id)}, 값: '{session_id}'")
        
        # 캐시 키 디버깅
        if redis_connected:
            debug_cache_keys(session_id)
        
        file_contents = []
        text_content = ""
        file_infos = []
        
        # 블로그 작성 시작 시 즉시 상태 업데이트
        print("📊 블로그 작성 요청 받음 - 상태 초기화 시작")
        initial_status = {
            'step': 'upload_received',
            'title': '파일 업로드 처리 중...',
            'content': '업로드된 파일을 처리하고 있습니다.',
            'progress': 5,
            'total_files': 0,
            'current_file': 0,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        }
        
        # 초기 상태 저장 시도
        cache_key = get_cache_key(session_id, 'blog_status')
        try:
            cache.set(cache_key, initial_status, 1800)
            print(f"📊 초기 상태 캐시에 저장됨 [{session_id}]: {initial_status}")
        except Exception as e:
            print(f"⚠️ 초기 상태 캐시 저장 실패: {str(e)}")
            # 로컬 캐시에 저장
            global _local_cache
            if '_local_cache' not in globals():
                _local_cache = {}
            _local_cache[cache_key] = initial_status
            print(f"📊 로컬 캐시에 초기 상태 저장: {cache_key}")
        
        # 타이핑 설정 받기
        typo_probability = float(request.POST.get('typo_probability', 0.1))
        typing_speed = float(request.POST.get('typing_speed', 0.5))
        
        # 네이버 로그인 정보 받기 (필수)
        naver_id = request.POST.get('naver_id', '').strip()
        naver_password = request.POST.get('naver_password', '').strip()
        
        # 네이버 로그인 정보 필수 검증
        if not naver_id:
            update_status('validation_error', '입력 오류', '네이버 아이디를 입력해주세요.', session_id=session_id)
            return JsonResponse({
                'success': False,
                'error': '네이버 아이디를 입력해주세요.',
                'session_id': session_id
            })
        
        if not naver_password:
            update_status('validation_error', '입력 오류', '네이버 비밀번호를 입력해주세요.', session_id=session_id)
            return JsonResponse({
                'success': False,
                'error': '네이버 비밀번호를 입력해주세요.',
                'session_id': session_id
            })
        
        # 값 범위 검증
        typo_probability = max(0.0, min(1.0, typo_probability))
        typing_speed = max(0.0, min(1.0, typing_speed))
        
        print("=" * 50)
        print(f"세션 ID: {session_id}")
        print(f"타이핑 설정:")
        print(f"오타 확률: {typo_probability}")
        print(f"타자 속도: {typing_speed}")
        print(f"네이버 아이디: {naver_id}")
        print(f"네이버 비밀번호: {'*' * len(naver_password)}")
        print("=" * 50)
        
        # 파일 처리 상태 업데이트
        update_status('file_processing', '파일 처리 중', '업로드된 파일을 검증하고 있습니다.', 10, session_id)
        
        # 파일들이 요청에 포함되어 있는지 확인
        if 'files' in request.FILES:
            uploaded_files = request.FILES.getlist('files')
            
            for uploaded_file in uploaded_files:
                # 파일 확장자 검사
                if not uploaded_file.name.lower().endswith('.txt'):
                    update_status('validation_error', '파일 오류', f'파일 "{uploaded_file.name}"은(는) 텍스트 파일(.txt)이 아닙니다.', session_id=session_id)
                    return JsonResponse({
                        'success': False,
                        'error': f'파일 "{uploaded_file.name}"은(는) 텍스트 파일(.txt)이 아닙니다.',
                        'session_id': session_id
                    })
                
                # 파일 크기 검사 (10MB 제한)
                max_size = 10 * 1024 * 1024  # 10MB
                if uploaded_file.size > max_size:
                    update_status('validation_error', '파일 크기 오류', f'파일 "{uploaded_file.name}"의 크기가 10MB를 초과합니다.', session_id=session_id)
                    return JsonResponse({
                        'success': False,
                        'error': f'파일 "{uploaded_file.name}"의 크기가 10MB를 초과합니다.',
                        'session_id': session_id
                    })
                
                # 파일 내용 읽기
                file_content = uploaded_file.read().decode('utf-8')
                file_contents.append(file_content)
                
                # 파일 정보 설정
                file_info = {
                    'original_name': uploaded_file.name,
                    'file_size': uploaded_file.size,
                    'content_length': len(file_content),
                    'upload_time': datetime.now().isoformat()
                }
                file_infos.append(file_info)
                
                # 파일 내용을 콘솔에 출력
                print("=" * 50)
                print(f"업로드된 파일: {uploaded_file.name}")
                print(f"파일 크기: {uploaded_file.size} bytes")
                print("=" * 50)
                print("파일 내용:")
                print(file_content)
                print("=" * 50)
        
        # 텍스트 입력 확인
        if 'text' in request.POST:
            text_content = request.POST['text'].strip()
            if text_content:
                print("=" * 50)
                print("입력된 텍스트:")
                print(text_content)
                print("=" * 50)
        
        # 파일과 텍스트 모두 없는 경우
        if not file_contents and not text_content:
            update_status('validation_error', '내용 없음', '파일 또는 텍스트를 입력해주세요.', session_id=session_id)
            return JsonResponse({
                'success': False,
                'error': '파일 또는 텍스트를 입력해주세요.',
                'session_id': session_id
            })
        
        # 블로그 작성 시작 상태 업데이트
        total_contents = len(file_contents) + (1 if text_content and text_content.strip() else 0)
        update_status('blog_start', '블로그 작성 시작', f'총 {total_contents}개 콘텐츠 블로그 작성을 시작합니다.', 15, session_id)
        
        print(f"📊 블로그 작성 함수 호출 직전 - 총 {total_contents}개 콘텐츠")
        print(f"📊 auto_blog_naver 호출 시 세션 ID: {session_id}")
        
        # auto_blog_naver 함수 호출 시 세션 ID와 타이핑 설정 전달
        success, message = auto_blog_naver(file_contents, text_content, typo_probability, typing_speed, naver_id, naver_password, session_id)
        
        # 성공/실패에 따른 응답 데이터 구성
        if success:
            response_data = {
                'success': True,
                'message': message,
                'file_count': len(file_contents),
                'file_infos': file_infos,
                'typing_settings': {
                    'typo_probability': typo_probability,
                    'typing_speed': typing_speed
                },
                'session_id': session_id
            }
            
            if file_contents:
                # 모든 파일의 내용을 하나로 합치거나 개별적으로 처리
                combined_content = "\n\n".join([f"=== {info['original_name']} ===\n{content}" for info, content in zip(file_infos, file_contents)])
                response_data['content_preview'] = combined_content[:1000] + '...' if len(combined_content) > 1000 else combined_content
            
            if text_content:
                response_data['text_content'] = text_content
                
        else:
            response_data = {
                'success': False,
                'error': message,
                'session_id': session_id
            }
        
        return JsonResponse(response_data)
        
    except UnicodeDecodeError:
        update_status('encoding_error', '인코딩 오류', '파일 인코딩 오류. UTF-8 인코딩의 텍스트 파일만 지원합니다.', session_id=session_id)
        return JsonResponse({
            'success': False,
            'error': '파일 인코딩 오류. UTF-8 인코딩의 텍스트 파일만 지원합니다.',
            'session_id': session_id
        })
    except Exception as e:
        update_status('upload_error', '업로드 오류', f'처리 중 오류가 발생했습니다: {str(e)}', session_id=session_id)
        return JsonResponse({
            'success': False,
            'error': f'처리 중 오류가 발생했습니다: {str(e)}',
            'session_id': session_id
        })
    


@require_http_methods(["GET"])
def get_blog_files(request):
    """
    업로드된 블로그 파일 목록 조회 - 현재는 파일을 저장하지 않으므로 빈 목록 반환
    """
    return JsonResponse({
        'success': True,
        'files': [],
        'message': '현재 파일 저장 기능이 비활성화되어 있습니다.'
    })

# ✅ Selenium 설정
def create_driver(session_id=None):
    import tempfile
    import os
    import socket
    
    def find_free_port():
        """사용 가능한 포트 찾기"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    options = webdriver.ChromeOptions()
    
    # 우분투 서버 환경을 위한 설정
    options.add_argument("--headless")  # GUI 없이 실행
    options.add_argument("--no-sandbox")  # 샌드박스 비활성화 (우분투 서버에서 필요)
    options.add_argument("--disable-dev-shm-usage")  # /dev/shm 사용 안함 (메모리 부족 방지)
    options.add_argument("--disable-gpu")  # GPU 비활성화
    
    # 세션별 고유 포트 할당 (포트 충돌 방지)
    if session_id:
        # 세션 ID를 기반으로 포트 범위 설정 (9222~9299)
        port_offset = int(session_id[:4], 16) % 78  # 0~77 범위
        debug_port = 9222 + port_offset
        print(f"🔧 세션 {session_id}에 포트 {debug_port} 할당")
    else:
        # 기본 포트 또는 사용 가능한 포트 찾기
        debug_port = find_free_port()
        print(f"🔧 동적 포트 할당: {debug_port}")
    
    options.add_argument(f"--remote-debugging-port={debug_port}")
    
    # 고유한 임시 디렉토리 사용하여 충돌 방지 (사용자 데이터 디렉토리 완전 제거)
    # temp_dir = tempfile.mkdtemp()
    # options.add_argument(f"--user-data-dir={temp_dir}")
    
    # 대신 user-data-dir 없이 실행
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-default-apps")
    
    options.add_argument("--window-size=1920,1080")  # headless에서 창 크기 설정
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 자동화 탐지 방지
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def slow_type_with_actionchains(driver, element, text, min_delay=0.05, max_delay=0.1, session_id=None):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()
    
    # 실시간 타이핑 상태 업데이트 (전체 진행도는 유지) - 제목 타이핑임을 명시
    current_status = cache.get(get_cache_key(session_id, 'blog_status') if session_id else 'blog_status')
    current_progress = current_status.get('progress', 0) if current_status else 0
    update_status('typing_title', '제목 타이핑 중...', f'"{text[:50]}{"..." if len(text) > 50 else ""}"', current_progress, session_id)
    
    for i, char in enumerate(text):
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        time.sleep(random.uniform(min_delay, max_delay))
        
        # 타이핑 중에는 진행도를 변경하지 않고 상태만 업데이트
        if i % 10 == 0:
            update_status('typing_title', '제목 타이핑 중...', text[:i+1], current_progress, session_id)

def get_typing_delays(typing_speed):
    try:
        # typing_speed가 0~1 범위로 들어옴
        # 0: 매우 빠름 (0.01~0.03초), 1: 매우 느림 (0.1~0.2초)
        min_delay = 0.01 + (typing_speed * 0.09)  # 0.01 ~ 0.1
        max_delay = 0.03 + (typing_speed * 0.17)  # 0.03 ~ 0.2
        return min_delay, max_delay
    except ValueError:
        return 0.03, 0.08  # 기본값

def get_typo_chance(typo_probability):
    try:
        return max(0.0, min(typo_probability, 1.0))  # 0~1 사이 값으로 클램핑
    except ValueError:
        return 0.1  # 기본값

def slow_type_with_typos(driver, element, text, min_delay=0.05, max_delay=0.1, typo_chance=0.1, session_id=None):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()

    # 실시간 타이핑 상태 업데이트 - 본문 타이핑임을 명시
    update_status('typing_body', '본문 타이핑 중...', f'"{text[:50]}{"..." if len(text) > 50 else ""}"', session_id=session_id)
    
    typed_text = ""
    
    for i, char in enumerate(text):
        # 오타 확률 발생
        if random.random() < typo_chance:
            typo_length = random.randint(2, 3)  # 2~3글자짜리 오타 생성
            fake_chars = ''.join(random.choices("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ", k=typo_length))

            # 오타 입력
            actions = ActionChains(driver)
            actions.send_keys(fake_chars).perform()
            typed_text += fake_chars
            update_status('typing_body_typo', '본문 오타 발생!', typed_text, session_id=session_id)
            time.sleep(random.uniform(min_delay, max_delay))

            # 오타 지우기 (Backspace 여러 번)
            for _ in range(typo_length):
                actions = ActionChains(driver)
                actions.send_keys(Keys.BACKSPACE).perform()
                typed_text = typed_text[:-1] if typed_text else ""
                update_status('typing_body_correction', '본문 오타 수정 중...', typed_text, session_id=session_id)
                time.sleep(random.uniform(min_delay, max_delay))

        # 정상 글자 입력
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        typed_text += char
        time.sleep(random.uniform(min_delay, max_delay))
        
        # 타이핑 진행률 업데이트 (5글자마다)
        if i % 5 == 0:
            progress = int((i / len(text)) * 100)
            update_status('typing_body', '본문 타이핑 중...', typed_text, progress, session_id)

# ✅ 네이버 로그인 (자동 로그인)
def naver_login(driver, naver_id, naver_password, session_id=None):
    try:
        update_status('login_start', '네이버 로그인 시작', f'아이디: {naver_id}', session_id=session_id)
        
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)

        update_status('login_input', '로그인 정보 입력 중', '아이디와 비밀번호 입력', session_id=session_id)
        
        # 자동 로그인
        # 아이디 입력 (JavaScript로 직접 값 설정)
        id_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
        id_input.click()
        time.sleep(1)
        
        # JavaScript로 직접 값 설정 (pyperclip 대신)
        driver.execute_script("arguments[0].value = arguments[1];", id_input, naver_id)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", id_input)
        time.sleep(1)

        # 비밀번호 입력 (JavaScript로 직접 값 설정)
        pw_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pw")))
        pw_input.click()
        time.sleep(1)
        
        # JavaScript로 직접 값 설정 (pyperclip 대신)
        driver.execute_script("arguments[0].value = arguments[1];", pw_input, naver_password)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", pw_input)
        time.sleep(1)

        update_status('login_submit', '로그인 버튼 클릭', '로그인 처리 중...', session_id=session_id)
        
        # 로그인 버튼 클릭
        login_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "log.login"))
        )
        login_btn.click()
        time.sleep(3)
        
        # 로그인 성공 여부 확인
        try:
            # 로그인 실패 시 나타나는 오류 메시지 확인
            error_element = driver.find_element(By.CLASS_NAME, "error_txt")
            if error_element and error_element.is_displayed():
                error_text = error_element.text
                print(f"❌ 네이버 로그인 실패: {error_text}")
                update_status('login_failed', '로그인 실패', error_text, session_id=session_id)
                return False, f"네이버 로그인 실패: {error_text}"
        except:
            pass
        
        # 보안 인증 창 처리 (새로운 창이 열렸는지 확인)
        try:
            # 현재 창 핸들 저장
            original_window = driver.current_window_handle
            original_handles_count = len(driver.window_handles)
            
            # 로그인 후 잠시 대기 (새 창이 열릴 시간 확보)
            time.sleep(3)
            
            # 새 창이 열렸는지 확인
            current_handles_count = len(driver.window_handles)
            
            if current_handles_count > original_handles_count:
                print(f"�� 보안 인증 창 감지됨 (창 개수: {original_handles_count} → {current_handles_count})")
                update_status('security_auth', '보안 인증 창 처리 중', '추가 인증 진행 중...', session_id=session_id)
                
                # 새 창으로 전환
                for handle in driver.window_handles:
                    if handle != original_window:
                        driver.switch_to.window(handle)
                        print(f"🔐 보안 인증 창으로 전환: {handle}")
                        
                        # 페이지 로딩 대기
                        time.sleep(2)
                        
                        # 등록 버튼 찾기 및 클릭 (XPath와 CSS 선택자 모두 시도)
                        register_btn = None
                        
                        # XPath 선택자들
                        xpath_selectors = [
                            "//a[@id='new.save' and @class='btn']",
                            "//a[@id='new.save']",
                            "//a[contains(@class, 'btn') and @id='new.save']",
                            "//span[@class='btn_upload']//a[@id='new.save']"
                        ]
                        
                        # CSS 선택자들
                        css_selectors = [
                            "a#new\\.save.btn",
                            "a[id='new.save']",
                            "a.btn[id*='new']",
                            "a.btn"
                        ]
                        
                        # XPath 먼저 시도
                        for xpath in xpath_selectors:
                            try:
                                register_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, xpath))
                                )
                                print(f"✅ 등록 버튼 발견 (XPath): {xpath}")
                                break
                            except Exception as xpath_error:
                                print(f"⚠️ XPath {xpath} 실패: {str(xpath_error)}")
                                continue
                        
                        # XPath 실패 시 CSS 선택자 시도
                        if not register_btn:
                            for css_selector in css_selectors:
                                try:
                                    register_btn = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
                                    )
                                    print(f"✅ 등록 버튼 발견 (CSS): {css_selector}")
                                    break
                                except Exception as css_error:
                                    print(f"⚠️ CSS 선택자 {css_selector} 실패: {str(css_error)}")
                                    continue
                        
                        if register_btn:
                            # 버튼 클릭 전 잠시 대기
                            time.sleep(1)
                            register_btn.click()
                            print("✅ 보안 인증 등록 버튼 클릭 완료")
                            update_status('security_auth_complete', '보안 인증 완료', '인증 창 닫는 중...', session_id=session_id)
                            
                            # 인증 완료 후 잠시 대기
                            time.sleep(3)
                        else:
                            print("⚠️ 등록 버튼을 찾을 수 없음")
                        
                        # 인증 창 닫기
                        driver.close()
                        
                        # 원래 창으로 복귀
                        driver.switch_to.window(original_window)
                        print("✅ 보안 인증 창 닫고 원래 창으로 복귀")
                        
                        # 원래 창에서 페이지 로딩 대기
                        time.sleep(2)
                        break
            else:
                print(f"ℹ️ 보안 인증 창 없음 (창 개수: {original_handles_count} → {current_handles_count})")
                    
        except Exception as e:
            # 새 창 처리 중 오류 발생 시 무시하고 진행
            print(f"⚠️ 보안 인증 창 처리 중 오류 발생: {str(e)}")
            # 원래 창으로 복귀 시도
            try:
                driver.switch_to.window(original_window)
                print("✅ 오류 발생 후 원래 창으로 복귀")
            except:
                pass
        
        # 현재 URL 확인으로 로그인 성공 여부 판단
        current_url = driver.current_url
        if "nid.naver.com" in current_url:
            print("❌ 네이버 로그인 실패: 로그인 페이지에 머물러 있음")
            update_status('login_failed', '로그인 실패', '아이디 또는 비밀번호를 확인해주세요', session_id=session_id)
            return False, "네이버 로그인 실패: 아이디 또는 비밀번호를 확인해주세요"
        
        print("✅ 자동 로그인 완료")
        update_status('login_success', '로그인 성공', '네이버 메인페이지로 이동 완료', session_id=session_id)
        return True, "네이버 로그인 성공"
        
    except Exception as e:
        print(f"❌ 네이버 로그인 중 오류 발생: {str(e)}")
        update_status('login_error', '로그인 오류', str(e), session_id=session_id)
        return False, f"네이버 로그인 중 오류 발생: {str(e)}"

# ✅ 블로그 글 작성페이지로 들어가기
def naver_blog(driver, session_id=None):
    try:
        update_status('blog_nav_start', '블로그 페이지 이동', '블로그 탭 찾는 중...', session_id=session_id)
        
        blog_tab = WebDriverWait(driver, 600).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//li[contains(@class, 'MyView-module__menu_item')][.//span[contains(text(), '블로그')]]"
            ))
        )
        blog_tab.click()
        print("✅ '블로그' 탭 클릭 완료")
        update_status('blog_tab_clicked', '블로그 탭 클릭 완료', '내 블로그 버튼 찾는 중...', session_id=session_id)

        try:
            blog_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "a.MyView-module__link_service___Ok8hP[href='https://blog.naver.com/MyBlog.naver']"
                ))
            )
            blog_link.click()
            print("✅ 내 블로그 버튼 클릭 완료")
            update_status('blog_link_clicked', '내 블로그 버튼 클릭 완료', '새 창으로 전환 중...', session_id=session_id)

            original_window = driver.current_window_handle
            time.sleep(2)

            # ✅ 새 창으로 전환
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    print("✅ 새 창으로 전환 완료")
                    update_status('window_switched', '새 창 전환 완료', '블로그 사용자 ID 추출 중...', session_id=session_id)
                    break

            # ✅ 사용자 블로그 ID 추출
            try:
                current_url = driver.current_url  # 예: https://blog.naver.com/rbdlfdlsp2
                user_id = current_url.rstrip("/").split("/")[-1]
                print(f"✅ 블로그 사용자 ID 추출 완료: {user_id}")
                update_status('user_id_extracted', 'ID 추출 완료', f'블로그 ID: {user_id}', session_id=session_id)

                return True, driver, user_id
            
            except Exception as e:
                print(f"❌ 블로그 사용자 ID 추출 실패: {str(e)}")
                update_status('user_id_failed', 'ID 추출 실패', str(e), session_id=session_id)
                return False, None, f"블로그 사용자 ID 추출 실패: {str(e)}"

        except Exception as e:
            print(f"❌ 내 블로그 버튼 클릭 실패: {str(e)}")
            update_status('blog_link_failed', '내 블로그 버튼 클릭 실패', str(e), session_id=session_id)
            return False, None, f"내 블로그 버튼 클릭 실패: {str(e)}"

    except Exception as e:
        print(f"❌ 블로그 탭 클릭 실패: {str(e)}")
        update_status('blog_tab_failed', '블로그 탭 클릭 실패', str(e), session_id=session_id)
        return False, None, f"블로그 탭 클릭 실패: {str(e)}"

def write_naver_blog(driver, user_id, title, content, typo_probability, typing_speed, session_id=None):
    min_d, max_d = get_typing_delays(typing_speed)
    time.sleep(3)

    try:
        update_status('write_page_nav', '글 작성 페이지 이동', f'제목: {title[:30]}{"..." if len(title) > 30 else ""}', session_id=session_id)
        
        driver.get(f"https://blog.naver.com/{user_id}?Redirect=Write&")
        print("✅ 블로그 글 작성 페이지로 이동 완료")

    except Exception as e:
        print(f"❌ 블로그 글 작성 페이지로 이동 실패: {str(e)}")
        update_status('write_page_failed', '작성 페이지 이동 실패', str(e), session_id=session_id)
        return False, f"블로그 글 작성 페이지로 이동 실패: {str(e)}"
    
    try:
        update_status('iframe_enter', 'iframe 진입 중', '에디터 로딩 중...', session_id=session_id)
        
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
        )
        print("✅ iframe(mainFrame) 진입 완료")

        try:
            load_write = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-popup-button-cancel"))
            )
            load_write.click()
            print("✅ 글 이어쓰기 취소 완료")
            update_status('popup_closed', '팝업 닫기 완료', '에디터 준비 중...', session_id=session_id)
            time.sleep(1)

        except Exception:
            print("⚠️ 글 이어쓰기 취소 실패 (없거나 클릭 안됨)")

        try:
            help_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-help-panel-close-button"))
            )
            driver.execute_script("arguments[0].click();", help_btn)
            print("✅ 도움말 패널 닫기 성공 (JS click)")
            time.sleep(1)

        except Exception:
            print("⚠️ 도움말 패널 닫기 실패 (없거나 클릭 안됨)")

        # ✅ 제목 입력
        try:
            update_status('title_input_start', '제목 입력 시작', f'제목: {title}', session_id=session_id)
            
            title_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-title-text"))
            )
            slow_type_with_actionchains(driver, title_container, title, min_delay=min_d, max_delay=max_d, session_id=session_id)
            print("✅ 제목 입력 완료")
            # 제목 입력 완료 시 전체 제목을 함께 전달
            time.sleep(1)

        except Exception as e:
            print(f"❌ 제목 입력 실패: {str(e)}")
            update_status('title_input_failed', '제목 입력 실패', str(e), session_id=session_id)
            return False, f"제목 입력 실패: {str(e)}"

        # ✅ 본문 입력
        try:
            update_status('content_input_start', '본문 입력 시작', f'본문 길이: {len(content)}자', session_id=session_id)
            
            body_paragraph = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-a11y-title='본문'] p.se-text-paragraph"
                ))
            )

            typo_chance = get_typo_chance(typo_probability)
            slow_type_with_typos(driver, body_paragraph, content, min_delay=min_d, max_delay=max_d, typo_chance=typo_chance, session_id=session_id)

            print("✅ 본문 입력 완료")
            # 본문 입력 완료 시 전체 내용을 함께 전달
            time.sleep(1)

        except Exception as e:
            print(f"❌ 본문 입력 실패: {str(e)}")
            update_status('content_input_failed', '본문 입력 실패', str(e), session_id=session_id)
            return False, f"본문 입력 실패: {str(e)}"

        try:
            update_status('save_start', '저장 시작', '저장 버튼 클릭 중...', session_id=session_id)
            
            publish_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='저장']]"))
            )
            publish_button.click()
            print("✅ 저장 버튼 클릭 완료")
            update_status('save_complete', '저장 완료', '블로그 글이 성공적으로 저장되었습니다', session_id=session_id)
            time.sleep(1)

            # ✅ 저장 후: 현재 창 닫고 원래 창으로 복귀
            driver.close()  # 현재 블로그 작성 창 닫기
            driver.switch_to.window(driver.window_handles[0])  # 원래 창으로 전환
            print("✅ 블로그 작성 창 닫고 원래 창으로 전환 완료")

            # ✅ 네이버 메인으로 이동
            driver.get("https://www.naver.com")
            print("✅ 네이버 메인으로 이동 완료")
            update_status('post_complete', '글 작성 완료', '다음 글 준비 중...', session_id=session_id)
            time.sleep(1)

            return True, "블로그 글 작성 완료"
            
        except Exception as e:
            print(f"❌ 저장 버튼 클릭 실패: {str(e)}")
            update_status('save_failed', '저장 실패', str(e), session_id=session_id)
            return False, f"저장 버튼 클릭 실패: {str(e)}"

    except Exception as e:
        print(f"❌ iframe(mainFrame) 진입 실패: {str(e)}")
        update_status('iframe_failed', 'iframe 진입 실패', str(e), session_id=session_id)
        return False, f"iframe(mainFrame) 진입 실패: {str(e)}"

def auto_blog_naver(file_texts, text_content, typo_probability, typing_speed, naver_id, naver_password, session_id):
    driver = None
    try:
        # 전역 변수에 세션 ID 설정
        set_current_session_id(session_id)
        print(f"🔧 auto_blog_naver에서 세션 ID 설정: {session_id}")
        
        # 전체 작업 상태 초기화
        total_contents = len(file_texts) + (1 if text_content and text_content.strip() else 0)
        
        # 초기 상태를 캐시에 저장
        initial_status = {
            'step': 'init',
            'title': '블로그 자동 작성 시작',
            'content': f'총 {total_contents}개 콘텐츠 처리 예정',
            'progress': 0,
            'total_files': total_contents,
            'current_file': 0,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        }
        cache.set(get_cache_key(session_id, 'blog_status'), initial_status, 1800)
        
        update_status('init', '블로그 자동 작성 시작', f'총 {total_contents}개 콘텐츠 처리 예정', session_id=session_id)
        
        driver = create_driver(session_id)
        
        # 로그인 시도
        login_success, login_message = naver_login(driver, naver_id, naver_password, session_id)
        if not login_success:
            return False, login_message

        # 처리할 콘텐츠 목록 생성
        contents_to_process = []
        
        # 파일 내용 추가
        for i, file_text in enumerate(file_texts):
            contents_to_process.append(('파일', i+1, file_text))
        
        # 텍스트 내용 추가 (있는 경우)
        if text_content and text_content.strip():
            contents_to_process.append(('텍스트', 1, text_content))

        if not contents_to_process:
            update_status('no_content', '처리할 콘텐츠 없음', '업로드된 파일이나 텍스트가 없습니다', session_id=session_id)
            return False, "처리할 콘텐츠가 없습니다."

        current_file_index = 0
        for content_type, content_index, content_text in contents_to_process:
            try:
                current_file_index += 1
                progress = int((current_file_index / total_contents) * 100)
                
                # 현재 파일 정보를 캐시에 업데이트
                current_status = cache.get(get_cache_key(session_id, 'blog_status'))
                if current_status is None:
                    current_status = {}
                    
                current_status.update({
                    'current_file': current_file_index,
                    'total_files': total_contents,
                    'progress': progress
                })
                cache.set(get_cache_key(session_id, 'blog_status'), current_status, 1800)
                
                update_status('processing_file', f'{content_type} {content_index} 처리 중', 
                            f'진행률: {current_file_index}/{total_contents}', progress, session_id)
                
                # 🔁 매 반복마다 작성 페이지 재진입
                blog_success, driver_or_error, user_id_or_message = naver_blog(driver, session_id)
                if not blog_success:
                    return False, user_id_or_message

                driver = driver_or_error
                user_id = user_id_or_message

                lines = content_text.strip().split("\n")
                title = lines[0] if lines else f"{content_type} {content_index}"
                body = "\n".join(lines[1:]) if len(lines) > 1 else content_text

                write_success, write_message = write_naver_blog(driver, user_id, title, body, typo_probability, typing_speed, session_id)
                if not write_success:
                    return False, f"{content_type} {content_index} 작성 실패: {write_message}"

                print(f"✅ {content_type} {content_index} 게시 완료")
                update_status('file_complete', f'{content_type} {content_index} 완료', 
                            f'"{title}" 게시 완료', session_id=session_id)

            except Exception as e:
                print(f"❌ {content_type} {content_index} 처리 실패: {str(e)}")
                update_status('file_error', f'{content_type} {content_index} 오류', str(e), session_id=session_id)
                return False, f"{content_type} {content_index} 처리 실패: {str(e)}"
        
        update_status('all_complete', '모든 작업 완료', f'총 {total_contents}개 콘텐츠 처리 완료', 100, session_id)
        return True, "모든 블로그 글 작성이 완료되었습니다"
        
    except Exception as e:
        print(f"❌ 블로그 작성 중 전체적인 오류 발생: {str(e)}")
        update_status('global_error', '전체 작업 오류', str(e), session_id=session_id)
        return False, f"블로그 작성 중 오류 발생: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
                print("✅ 브라우저 종료 완료")
                update_status('cleanup', '브라우저 종료', '모든 작업이 완료되었습니다', session_id=session_id)
            except Exception as e:
                print(f"⚠️ 브라우저 종료 실패: {str(e)}")
        
        # 작업 완료 후 전역 변수 정리
        set_current_session_id(None)

# Redis 디버깅을 위한 추가 뷰
@require_http_methods(["GET"])
def debug_redis_status(request):
    """Redis 상태 및 캐시 키 디버깅"""
    try:
        # Redis 연결 확인
        redis_connected = check_redis_connection()
        
        # 모든 blog_status 관련 키 조회
        all_keys = debug_cache_keys()
        
        # 세션 관련 정보
        session_id = request.GET.get('session_id', '')
        if not session_id:
            session_id = generate_session_id(request)
        
        # 현재 세션의 캐시 키
        current_cache_key = get_cache_key(session_id, 'blog_status')
        current_status = get_status_safe(current_cache_key, session_id)
        
        debug_info = {
            'redis_connected': redis_connected,
            'session_id': session_id,
            'current_cache_key': current_cache_key,
            'current_status': current_status,
            'all_cache_keys': all_keys,
            'cache_key_count': len(all_keys),
            'timestamp': datetime.now().isoformat()
        }
        
        # 로컬 캐시 정보도 포함
        global _local_cache
        if '_local_cache' in globals():
            debug_info['local_cache_keys'] = list(_local_cache.keys())
            debug_info['local_cache_count'] = len(_local_cache)
        else:
            debug_info['local_cache_keys'] = []
            debug_info['local_cache_count'] = 0
        
        return JsonResponse({
            'success': True,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# 상태 조회를 위한 새로운 뷰 함수
@require_http_methods(["GET"])
def get_blog_status(request):
    """실시간 블로그 작성 상태 조회"""
    # Redis 연결 상태 확인
    redis_connected = check_redis_connection()
    
    # 세션 ID 가져오기 (URL 파라미터 또는 세션에서)
    session_id = None
    
    # URL 파라미터에서 세션 ID 확인
    session_id = request.GET.get('session_id', '').strip()
    if not session_id:
        # URL 파라미터에 없으면 세션에서 가져오기
        session_id = generate_session_id(request)
    
    # 세션 ID 유효성 검증 (16자리 해시 형태인지 확인)
    if session_id and (len(session_id) != 16 or not all(c in '0123456789abcdef' for c in session_id.lower())):
        print(f"⚠️ 유효하지 않은 세션 ID 형식: {session_id}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid session ID format',
            'session_id': session_id
        })
    
    print(f"📊 상태 조회 요청 - 세션 ID: {session_id}")
    print(f"📊 Redis 연결 상태: {'정상' if redis_connected else '실패'}")
    
    # 캐시 키 디버깅 (세션 ID 관련 키들 확인)
    if redis_connected:
        debug_cache_keys(session_id)
    
    # 해당 세션의 상태 데이터 조회 (안전한 조회 함수 사용)
    cache_key = get_cache_key(session_id, 'blog_status')
    status_data = get_status_safe(cache_key, session_id)
    
    print(f"📊 상태 조회 요청 - 캐시 키: {cache_key}")
    print(f"📊 상태 조회 요청 - 조회 결과: {status_data}")
    
    if status_data:
        # 세션 ID 일치 여부 확인
        stored_session_id = status_data.get('session_id')
        if stored_session_id and stored_session_id != session_id:
            print(f"⚠️ 세션 ID 불일치: 요청={session_id}, 저장됨={stored_session_id}")
        
        return JsonResponse({
            'success': True,
            'status': status_data,
            'session_id': session_id,
            'redis_connected': redis_connected
        })
    else:
        # 캐시에 데이터가 없는 경우 기본 상태 반환
        default_status = {
            'step': 'ready',
            'title': '준비 중...',
            'content': '',
            'progress': 0,
            'total_files': 0,
            'current_file': 0,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        }
        print(f"📊 캐시에 데이터 없음 - 기본 상태 반환: {default_status}")
        
        # 기본 상태를 캐시에 저장 시도
        try:
            cache.set(cache_key, default_status, 1800)
            print(f"📊 기본 상태를 캐시에 저장: {cache_key}")
        except Exception as e:
            print(f"⚠️ 기본 상태 캐시 저장 실패: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'status': default_status,
            'session_id': session_id,
            'redis_connected': redis_connected
        })