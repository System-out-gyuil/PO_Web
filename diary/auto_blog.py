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
from selenium.webdriver import ActionChains
import traceback
import time
import random
from selenium.webdriver.common.keys import Keys
import pyperclip
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
        
        # 네이버 로그인 정보 받기 (nullable)
        naver_id = request.POST.get('naver_id', '').strip()
        naver_password = request.POST.get('naver_password', '').strip()
        
        # 값 범위 검증
        typo_probability = max(0.0, min(1.0, typo_probability))
        typing_speed = max(0.0, min(1.0, typing_speed))
        
        print("=" * 50)
        print(f"타이핑 설정:")
        print(f"오타 확률: {typo_probability}")
        print(f"타자 속도: {typing_speed}")
        if naver_id:
            print(f"네이버 아이디: {naver_id}")
            print(f"네이버 비밀번호: {'*' * len(naver_password)}")
        else:
            print("네이버 로그인 정보: 수동 입력 예정")
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
        auto_blog_naver(file_contents, text_content, typo_probability, typing_speed, naver_id, naver_password)
        
        # 응답 데이터 구성
        response_data = {
            'success': True,
            'message': '내용이 성공적으로 처리되었습니다.',
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
def kill_chrome_processes():
    """기존 Chrome 프로세스들을 강제 종료"""
    import subprocess
    import platform
    
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                         capture_output=True, check=False)
            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                         capture_output=True, check=False)
        else:
            subprocess.run(["pkill", "-f", "chrome"], 
                         capture_output=True, check=False)
            subprocess.run(["pkill", "-f", "chromedriver"], 
                         capture_output=True, check=False)
        print("✅ 기존 Chrome 프로세스 정리 완료")
    except Exception as e:
        print(f"⚠️ Chrome 프로세스 정리 중 오류: {str(e)}")

def create_driver():
    import tempfile
    import os
    import shutil
    
    # 기존 Chrome 프로세스 정리
    kill_chrome_processes()
    time.sleep(2)  # 프로세스 종료 대기
    
    options = webdriver.ChromeOptions()
    
    # 완전히 격리된 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix="selenium_chrome_")
    temp_user_data_dir = os.path.join(temp_dir, "user_data")
    temp_cache_dir = os.path.join(temp_dir, "cache")
    
    # 디렉토리 생성
    os.makedirs(temp_user_data_dir, exist_ok=True)
    os.makedirs(temp_cache_dir, exist_ok=True)
    
    # Chrome 옵션 설정
    options.add_argument(f"--user-data-dir={temp_user_data_dir}")
    options.add_argument(f"--disk-cache-dir={temp_cache_dir}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # 자동화 감지 방지
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 2
    })

    try:
        service = Service(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 자동화 감지 방지 스크립트 실행
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']})")
        
        # 임시 디렉토리 정보를 드라이버 객체에 저장 (나중에 정리용)
        driver.temp_dir = temp_dir
        
        return driver
        
    except Exception as e:
        # 드라이버 생성 실패 시 임시 디렉토리 정리
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        raise e

def slow_type_with_actionchains(driver, element, text, min_delay=0.05, max_delay=0.1):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()
    for char in text:
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        time.sleep(random.uniform(min_delay, max_delay))

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

    for char in text:
        # 오타 확률 발생
        if random.random() < typo_chance:
            typo_length = random.randint(2, 3)  # 2~3글자짜리 오타 생성
            fake_chars = ''.join(random.choices("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ", k=typo_length))

            # 오타 입력
            actions = ActionChains(driver)
            actions.send_keys(fake_chars).perform()
            time.sleep(random.uniform(min_delay, max_delay))

            # 오타 지우기 (Backspace 여러 번)
            for _ in range(typo_length):
                actions = ActionChains(driver)
                actions.send_keys(Keys.BACKSPACE).perform()
                time.sleep(random.uniform(min_delay, max_delay))

        # 정상 글자 입력
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        time.sleep(random.uniform(min_delay, max_delay))

# ✅ 네이버 로그인 (직접 입력 유도)
def naver_login(driver, naver_id=None, naver_password=None):
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(2)

    # 로그인 정보가 제공된 경우 자동 로그인
    if naver_id and naver_password:
        # 아이디 입력
        id_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
        id_input.click()
        time.sleep(1)
        pyperclip.copy(naver_id)
        id_input.send_keys(Keys.CONTROL, 'v')  # ⬅️ pyautogui 대신 이걸 사용
        time.sleep(1)

        # 비밀번호 입력
        pw_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pw")))
        pw_input.click()
        time.sleep(1)
        pyperclip.copy(naver_password)
        pw_input.send_keys(Keys.CONTROL, 'v')  # ⬅️ 여기도 동일
        time.sleep(1)

        # 로그인 버튼 클릭
        login_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "log.login"))
        )
        login_btn.click()
        time.sleep(3)
        print("✅ 자동 로그인 완료")
    else:
        # 수동 로그인 대기
        print("⏳ 네이버 창에서 수동으로 로그인해주세요...")
        print("로그인 완료 후 자동으로 진행됩니다.")
        
        # 로그인 완료까지 대기 (네이버 메인 페이지로 이동하는지 확인)
        try:
            WebDriverWait(driver, 300).until(lambda d: "nid.naver.com" not in d.current_url)
            print("✅ 수동 로그인 완료")
        except:
            print("❌ 로그인 대기 시간 초과")
            raise Exception("로그인 시간 초과")

# ✅ 블로그 글 작성페이지로 들어가기
def naver_blog(driver):
    try:
        blog_tab = WebDriverWait(driver, 600).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//li[contains(@class, 'MyView-module__menu_item')][.//span[contains(text(), '블로그')]]"
            ))
        )
        blog_tab.click()
        print("✅ '블로그' 탭 클릭 완료")

        try:
            blog_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "a.MyView-module__link_service___Ok8hP[href='https://blog.naver.com/MyBlog.naver']"
                ))
            )
            blog_link.click()
            print("✅ 내 블로그 버튼 클릭 완료")

            original_window = driver.current_window_handle
            time.sleep(2)

            # ✅ 새 창으로 전환
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    print("✅ 새 창으로 전환 완료")
                    break

            # ✅ 사용자 블로그 ID 추출
            try:
                current_url = driver.current_url  # 예: https://blog.naver.com/rbdlfdlsp2
                user_id = current_url.rstrip("/").split("/")[-1]
                print(f"✅ 블로그 사용자 ID 추출 완료: {user_id}")

                return driver, user_id
            
            except Exception:
                print("❌ 블로그 사용자 ID 추출 실패:")
                traceback.print_exc()


        except Exception:
            print("❌ 내 블로그 버튼 클릭 실패:")
            traceback.print_exc()

    except Exception:
        print("❌ 블로그 탭 클릭 실패:")
        traceback.print_exc()

def write_naver_blog(driver, user_id, title, content, typo_probability, typing_speed):
    min_d, max_d = get_typing_delays(typing_speed)
    time.sleep(3)

    try:
        driver.get(f"https://blog.naver.com/{user_id}?Redirect=Write&")
        print("✅ 블로그 글 작성 페이지로 이동 완료")

    except Exception:
        print("❌ 블로그 글 작성 페이지로 이동 실패:")
        traceback.print_exc()
    
    try:
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
            time.sleep(1)

        except Exception:
            print("⚠️ 글 이어쓰기 취소 실패 (없거나 클릭 안됨)")
            traceback.print_exc()

        try:
            help_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-help-panel-close-button"))
            )
            driver.execute_script("arguments[0].click();", help_btn)
            print("✅ 도움말 패널 닫기 성공 (JS click)")
            time.sleep(1)

        except Exception:
            print("⚠️ 도움말 패널 닫기 실패 (없거나 클릭 안됨)")
            traceback.print_exc()

        # ✅ 제목 입력
        try:
            title_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-title-text"))
            )
            slow_type_with_actionchains(driver, title_container, title, min_delay=min_d, max_delay=max_d)
            print("✅ 제목 입력 완료")
            time.sleep(1)

        except Exception:
            print("❌ 제목 입력 실패:")
            traceback.print_exc()

        # ✅ 본문 입력
        try:
            body_paragraph = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-a11y-title='본문'] p.se-text-paragraph"
                ))
            )

            typo_chance = get_typo_chance(typo_probability)
            slow_type_with_typos(driver, body_paragraph, content, min_delay=min_d, max_delay=max_d, typo_chance=typo_chance)

            print("✅ 본문 입력 완료")
            time.sleep(1)

        except Exception:
            print("❌ 본문 입력 실패:")
            traceback.print_exc()

        

        publish_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='저장']]"))
        )
        publish_button.click()
        print("✅ 저장 버튼 클릭 완료")
        time.sleep(1)

        # ✅ 저장 후: 현재 창 닫고 원래 창으로 복귀
        driver.close()  # 현재 블로그 작성 창 닫기
        driver.switch_to.window(driver.window_handles[0])  # 원래 창으로 전환
        print("✅ 블로그 작성 창 닫고 원래 창으로 전환 완료")

        # ✅ 네이버 메인으로 이동
        driver.get("https://www.naver.com")
        print("✅ 네이버 메인으로 이동 완료")
        time.sleep(1)

        return driver


    except Exception:
        print("❌ iframe(mainFrame) 진입 또는 제목 입력 실패:")
        traceback.print_exc()

def auto_blog_naver(file_texts, user_input, typo_probability, typing_speed, naver_id, naver_password):
    driver = None
    try:
        # 기존 Chrome 프로세스 정리
        kill_chrome_processes()
        time.sleep(3)  # 프로세스 종료 대기
        
        driver = create_driver()
        naver_login(driver, naver_id, naver_password)

        for file_text in file_texts:
            try:
                # 🔁 매 반복마다 작성 페이지 재진입
                driver, user_id = naver_blog(driver)

                lines = file_text.strip().split("\n")
                title = lines[0]
                body = "\n".join(lines[1:])

                driver = write_naver_blog(driver, user_id, title, body, typo_probability, typing_speed)

                print("✅ 게시 완료")

            except Exception as e:
                print(f"❌ 파일 처리 실패: {str(e)}")
                traceback.print_exc()
                continue  # 다음 파일로 계속 진행
                
    except Exception as e:
        print(f"❌ 초기화 실패: {str(e)}")
        traceback.print_exc()
    finally:
        # 드라이버 종료
        if driver:
            try:
                driver.quit()
                print("✅ 브라우저 종료 완료")
                
                # 임시 디렉토리 정리
                if hasattr(driver, 'temp_dir'):
                    try:
                        import shutil
                        shutil.rmtree(driver.temp_dir, ignore_errors=True)
                        print("✅ 임시 디렉토리 정리 완료")
                    except Exception as e:
                        print(f"⚠️ 임시 디렉토리 정리 중 오류: {str(e)}")
                        
            except Exception as e:
                print(f"⚠️ 브라우저 종료 중 오류: {str(e)}")