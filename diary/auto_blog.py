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

@csrf_exempt
@require_http_methods(["POST"])
def upload_blog_file(request):
    """
    블로그 텍스트 파일 업로드 처리 - 파일 저장 없이 내용만 출력
    """
    try:
        file_contents = []
        text_content = ""
        file_infos = []
        
        # 타이핑 설정 받기
        typo_probability = float(request.POST.get('typo_probability', 0.1))
        typing_speed = float(request.POST.get('typing_speed', 0.5))
        
        # 네이버 로그인 정보 받기 (필수)
        naver_id = request.POST.get('naver_id', '').strip()
        naver_password = request.POST.get('naver_password', '').strip()
        
        # 네이버 로그인 정보 필수 검증
        if not naver_id:
            return JsonResponse({
                'success': False,
                'error': '네이버 아이디를 입력해주세요.'
            })
        
        if not naver_password:
            return JsonResponse({
                'success': False,
                'error': '네이버 비밀번호를 입력해주세요.'
            })
        
        # 값 범위 검증
        typo_probability = max(0.0, min(1.0, typo_probability))
        typing_speed = max(0.0, min(1.0, typing_speed))
        
        print("=" * 50)
        print(f"타이핑 설정:")
        print(f"오타 확률: {typo_probability}")
        print(f"타자 속도: {typing_speed}")
        print(f"네이버 아이디: {naver_id}")
        print(f"네이버 비밀번호: {'*' * len(naver_password)}")
        print("=" * 50)
        
        # 파일들이 요청에 포함되어 있는지 확인
        if 'files' in request.FILES:
            uploaded_files = request.FILES.getlist('files')
            
            for uploaded_file in uploaded_files:
                # 파일 확장자 검사
                if not uploaded_file.name.lower().endswith('.txt'):
                    return JsonResponse({
                        'success': False,
                        'error': f'파일 "{uploaded_file.name}"은(는) 텍스트 파일(.txt)이 아닙니다.'
                    })
                
                # 파일 크기 검사 (10MB 제한)
                max_size = 10 * 1024 * 1024  # 10MB
                if uploaded_file.size > max_size:
                    return JsonResponse({
                        'success': False,
                        'error': f'파일 "{uploaded_file.name}"의 크기가 10MB를 초과합니다.'
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
            return JsonResponse({
                'success': False,
                'error': '파일 또는 텍스트를 입력해주세요.'
            })
        
        # auto_blog_naver 함수 호출 시 타이핑 설정 전달
        success, message = auto_blog_naver(file_contents, text_content, typo_probability, typing_speed, naver_id, naver_password)
        
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
                }
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
                'error': message
            }
        
        return JsonResponse(response_data)
        
    except UnicodeDecodeError:
        return JsonResponse({
            'success': False,
            'error': '파일 인코딩 오류. UTF-8 인코딩의 텍스트 파일만 지원합니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'처리 중 오류가 발생했습니다: {str(e)}'
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
def create_driver():
    import tempfile
    import os
    
    options = webdriver.ChromeOptions()
    
    # 우분투 서버 환경을 위한 설정
    options.add_argument("--headless")  # GUI 없이 실행
    options.add_argument("--no-sandbox")  # 샌드박스 비활성화 (우분투 서버에서 필요)
    options.add_argument("--disable-dev-shm-usage")  # /dev/shm 사용 안함 (메모리 부족 방지)
    options.add_argument("--disable-gpu")  # GPU 비활성화
    options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트 설정
    
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

# 실시간 상태 업데이트를 위한 전역 변수
current_status = {
    'step': '',
    'title': '',
    'content': '',
    'progress': 0,
    'total_files': 0,
    'current_file': 0
}

def update_status(step, title='', content='', progress=0):
    """실시간 상태 업데이트 함수"""
    global current_status
    current_status.update({
        'step': step,
        'title': title,
        'content': content,
        'progress': progress
    })
    print(f"📊 상태 업데이트: {step} - {title}")

def slow_type_with_actionchains(driver, element, text, min_delay=0.05, max_delay=0.1):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()
    
    # 실시간 타이핑 상태 업데이트 (전체 진행도는 유지)
    current_progress = current_status.get('progress', 0)
    update_status('typing', '타이핑 중...', f'"{text[:50]}{"..." if len(text) > 50 else ""}"', current_progress)
    
    for i, char in enumerate(text):
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        time.sleep(random.uniform(min_delay, max_delay))
        
        # 타이핑 중에는 진행도를 변경하지 않고 상태만 업데이트
        if i % 10 == 0:
            update_status('typing', '타이핑 중...', text[:i+1], current_progress)

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

def slow_type_with_typos(driver, element, text, min_delay=0.05, max_delay=0.1, typo_chance=0.1):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()

    # 실시간 타이핑 상태 업데이트
    update_status('typing_with_typos', '오타 포함 타이핑 중...', f'"{text[:50]}{"..." if len(text) > 50 else ""}"')
    
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
            update_status('typing_typo', '오타 발생!', typed_text)
            time.sleep(random.uniform(min_delay, max_delay))

            # 오타 지우기 (Backspace 여러 번)
            for _ in range(typo_length):
                actions = ActionChains(driver)
                actions.send_keys(Keys.BACKSPACE).perform()
                typed_text = typed_text[:-1] if typed_text else ""
                update_status('typing_correction', '오타 수정 중...', typed_text)
                time.sleep(random.uniform(min_delay, max_delay))

        # 정상 글자 입력
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        typed_text += char
        time.sleep(random.uniform(min_delay, max_delay))
        
        # 타이핑 진행률 업데이트 (5글자마다)
        if i % 5 == 0:
            progress = int((i / len(text)) * 100)
            update_status('typing_with_typos', '오타 포함 타이핑 중...', typed_text, progress)

# ✅ 네이버 로그인 (자동 로그인)
def naver_login(driver, naver_id, naver_password):
    try:
        update_status('login_start', '네이버 로그인 시작', f'아이디: {naver_id}')
        
        driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)

        update_status('login_input', '로그인 정보 입력 중', '아이디와 비밀번호 입력')
        
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

        update_status('login_submit', '로그인 버튼 클릭', '로그인 처리 중...')
        
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
                update_status('login_failed', '로그인 실패', error_text)
                return False, f"네이버 로그인 실패: {error_text}"
        except:
            pass
        
        # 현재 URL 확인으로 로그인 성공 여부 판단
        current_url = driver.current_url
        if "nid.naver.com" in current_url:
            print("❌ 네이버 로그인 실패: 로그인 페이지에 머물러 있음")
            update_status('login_failed', '로그인 실패', '아이디 또는 비밀번호를 확인해주세요')
            return False, "네이버 로그인 실패: 아이디 또는 비밀번호를 확인해주세요"
        
        print("✅ 자동 로그인 완료")
        update_status('login_success', '로그인 성공', '네이버 메인페이지로 이동 완료')
        return True, "네이버 로그인 성공"
        
    except Exception as e:
        print(f"❌ 네이버 로그인 중 오류 발생: {str(e)}")
        update_status('login_error', '로그인 오류', str(e))
        return False, f"네이버 로그인 중 오류 발생: {str(e)}"

# ✅ 블로그 글 작성페이지로 들어가기
def naver_blog(driver):
    try:
        update_status('blog_nav_start', '블로그 페이지 이동', '블로그 탭 찾는 중...')
        
        blog_tab = WebDriverWait(driver, 600).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//li[contains(@class, 'MyView-module__menu_item')][.//span[contains(text(), '블로그')]]"
            ))
        )
        blog_tab.click()
        print("✅ '블로그' 탭 클릭 완료")
        update_status('blog_tab_clicked', '블로그 탭 클릭 완료', '내 블로그 버튼 찾는 중...')

        try:
            blog_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "a.MyView-module__link_service___Ok8hP[href='https://blog.naver.com/MyBlog.naver']"
                ))
            )
            blog_link.click()
            print("✅ 내 블로그 버튼 클릭 완료")
            update_status('blog_link_clicked', '내 블로그 버튼 클릭 완료', '새 창으로 전환 중...')

            original_window = driver.current_window_handle
            time.sleep(2)

            # ✅ 새 창으로 전환
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    print("✅ 새 창으로 전환 완료")
                    update_status('window_switched', '새 창 전환 완료', '블로그 사용자 ID 추출 중...')
                    break

            # ✅ 사용자 블로그 ID 추출
            try:
                current_url = driver.current_url  # 예: https://blog.naver.com/rbdlfdlsp2
                user_id = current_url.rstrip("/").split("/")[-1]
                print(f"✅ 블로그 사용자 ID 추출 완료: {user_id}")
                update_status('user_id_extracted', 'ID 추출 완료', f'블로그 ID: {user_id}')

                return True, driver, user_id
            
            except Exception as e:
                print(f"❌ 블로그 사용자 ID 추출 실패: {str(e)}")
                update_status('user_id_failed', 'ID 추출 실패', str(e))
                return False, None, f"블로그 사용자 ID 추출 실패: {str(e)}"

        except Exception as e:
            print(f"❌ 내 블로그 버튼 클릭 실패: {str(e)}")
            update_status('blog_link_failed', '내 블로그 버튼 클릭 실패', str(e))
            return False, None, f"내 블로그 버튼 클릭 실패: {str(e)}"

    except Exception as e:
        print(f"❌ 블로그 탭 클릭 실패: {str(e)}")
        update_status('blog_tab_failed', '블로그 탭 클릭 실패', str(e))
        return False, None, f"블로그 탭 클릭 실패: {str(e)}"

def write_naver_blog(driver, user_id, title, content, typo_probability, typing_speed):
    min_d, max_d = get_typing_delays(typing_speed)
    time.sleep(3)

    try:
        update_status('write_page_nav', '글 작성 페이지 이동', f'제목: {title[:30]}{"..." if len(title) > 30 else ""}')
        
        driver.get(f"https://blog.naver.com/{user_id}?Redirect=Write&")
        print("✅ 블로그 글 작성 페이지로 이동 완료")

    except Exception as e:
        print(f"❌ 블로그 글 작성 페이지로 이동 실패: {str(e)}")
        update_status('write_page_failed', '작성 페이지 이동 실패', str(e))
        return False, f"블로그 글 작성 페이지로 이동 실패: {str(e)}"
    
    try:
        update_status('iframe_enter', 'iframe 진입 중', '에디터 로딩 중...')
        
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
            update_status('popup_closed', '팝업 닫기 완료', '에디터 준비 중...')
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
            update_status('title_input_start', '제목 입력 시작', f'제목: {title}')
            
            title_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-title-text"))
            )
            slow_type_with_actionchains(driver, title_container, title, min_delay=min_d, max_delay=max_d)
            print("✅ 제목 입력 완료")
            update_status('title_input_complete', '제목 입력 완료', title)
            time.sleep(1)

        except Exception as e:
            print(f"❌ 제목 입력 실패: {str(e)}")
            update_status('title_input_failed', '제목 입력 실패', str(e))
            return False, f"제목 입력 실패: {str(e)}"

        # ✅ 본문 입력
        try:
            update_status('content_input_start', '본문 입력 시작', f'본문 길이: {len(content)}자')
            
            body_paragraph = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-a11y-title='본문'] p.se-text-paragraph"
                ))
            )

            typo_chance = get_typo_chance(typo_probability)
            slow_type_with_typos(driver, body_paragraph, content, min_delay=min_d, max_delay=max_d, typo_chance=typo_chance)

            print("✅ 본문 입력 완료")
            update_status('content_input_complete', '본문 입력 완료', f'총 {len(content)}자 입력 완료')
            time.sleep(1)

        except Exception as e:
            print(f"❌ 본문 입력 실패: {str(e)}")
            update_status('content_input_failed', '본문 입력 실패', str(e))
            return False, f"본문 입력 실패: {str(e)}"

        try:
            update_status('save_start', '저장 시작', '저장 버튼 클릭 중...')
            
            publish_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='저장']]"))
            )
            publish_button.click()
            print("✅ 저장 버튼 클릭 완료")
            update_status('save_complete', '저장 완료', '블로그 글이 성공적으로 저장되었습니다')
            time.sleep(1)

            # ✅ 저장 후: 현재 창 닫고 원래 창으로 복귀
            driver.close()  # 현재 블로그 작성 창 닫기
            driver.switch_to.window(driver.window_handles[0])  # 원래 창으로 전환
            print("✅ 블로그 작성 창 닫고 원래 창으로 전환 완료")

            # ✅ 네이버 메인으로 이동
            driver.get("https://www.naver.com")
            print("✅ 네이버 메인으로 이동 완료")
            update_status('post_complete', '글 작성 완료', '다음 글 준비 중...')
            time.sleep(1)

            return True, "블로그 글 작성 완료"
            
        except Exception as e:
            print(f"❌ 저장 버튼 클릭 실패: {str(e)}")
            update_status('save_failed', '저장 실패', str(e))
            return False, f"저장 버튼 클릭 실패: {str(e)}"

    except Exception as e:
        print(f"❌ iframe(mainFrame) 진입 실패: {str(e)}")
        update_status('iframe_failed', 'iframe 진입 실패', str(e))
        return False, f"iframe(mainFrame) 진입 실패: {str(e)}"

def auto_blog_naver(file_texts, text_content, typo_probability, typing_speed, naver_id, naver_password):
    driver = None
    try:
        # 전체 작업 상태 초기화
        total_contents = len(file_texts) + (1 if text_content and text_content.strip() else 0)
        current_status['total_files'] = total_contents
        current_status['current_file'] = 0
        
        update_status('init', '블로그 자동 작성 시작', f'총 {total_contents}개 콘텐츠 처리 예정')
        
        driver = create_driver()
        
        # 로그인 시도
        login_success, login_message = naver_login(driver, naver_id, naver_password)
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
            update_status('no_content', '처리할 콘텐츠 없음', '업로드된 파일이나 텍스트가 없습니다')
            return False, "처리할 콘텐츠가 없습니다."

        for content_type, content_index, content_text in contents_to_process:
            try:
                current_status['current_file'] += 1
                progress = int((current_status['current_file'] / total_contents) * 100)
                
                update_status('processing_file', f'{content_type} {content_index} 처리 중', 
                            f'진행률: {current_status["current_file"]}/{total_contents}', progress)
                
                # 🔁 매 반복마다 작성 페이지 재진입
                blog_success, driver_or_error, user_id_or_message = naver_blog(driver)
                if not blog_success:
                    return False, user_id_or_message

                driver = driver_or_error
                user_id = user_id_or_message

                lines = content_text.strip().split("\n")
                title = lines[0] if lines else f"{content_type} {content_index}"
                body = "\n".join(lines[1:]) if len(lines) > 1 else content_text

                write_success, write_message = write_naver_blog(driver, user_id, title, body, typo_probability, typing_speed)
                if not write_success:
                    return False, f"{content_type} {content_index} 작성 실패: {write_message}"

                print(f"✅ {content_type} {content_index} 게시 완료")
                update_status('file_complete', f'{content_type} {content_index} 완료', 
                            f'"{title}" 게시 완료')

            except Exception as e:
                print(f"❌ {content_type} {content_index} 처리 실패: {str(e)}")
                update_status('file_error', f'{content_type} {content_index} 오류', str(e))
                return False, f"{content_type} {content_index} 처리 실패: {str(e)}"
        
        update_status('all_complete', '모든 작업 완료', f'총 {total_contents}개 콘텐츠 처리 완료', 100)
        return True, "모든 블로그 글 작성이 완료되었습니다"
        
    except Exception as e:
        print(f"❌ 블로그 작성 중 전체적인 오류 발생: {str(e)}")
        update_status('global_error', '전체 작업 오류', str(e))
        return False, f"블로그 작성 중 오류 발생: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
                print("✅ 브라우저 종료 완료")
                update_status('cleanup', '브라우저 종료', '모든 작업이 완료되었습니다')
            except Exception as e:
                print(f"⚠️ 브라우저 종료 실패: {str(e)}")

# 상태 조회를 위한 새로운 뷰 함수
@require_http_methods(["GET"])
def get_blog_status(request):
    """실시간 블로그 작성 상태 조회"""
    global current_status
    return JsonResponse({
        'success': True,
        'status': current_status
    })