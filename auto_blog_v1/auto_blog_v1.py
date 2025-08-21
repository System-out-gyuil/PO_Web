import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import traceback
from tkinter import filedialog, messagebox
import time
import random
from selenium.webdriver.common.keys import Keys
import pyperclip
import pyautogui
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pygetwindow as gw
import requests
import json

# 전역 변수로 사용자 자격증명 저장
user_naver_id = ""
user_naver_pw = ""
root = None  # 메인 창 참조를 위한 전역 변수
naver_id_entry = None  # 네이버 아이디 입력 필드
naver_pw_entry = None  # 네이버 비밀번호 입력 필드
user_use_date = ""  # 사용 가능 기간
version_message = ""  # 버전 관련 메시지

def check_blog_account(user_id, password):
    """블로그 계정 확인 API 호출"""
    try:
        url = "https://자금왕.com/sales/blog_account_check_api/"
        # url = "http://127.0.0.1:8000/sales/blog_account_check_api/"
        params = {
            'user_id': user_id,
            'password': password,
            'version': '1.0'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API 연결 오류: {str(e)}'
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'API 응답 형식 오류'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'알 수 없는 오류: {str(e)}'
        }

def activate_chrome_window():
    for window in gw.getWindowsWithTitle("네이버"):
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
            break
        except:
            pass
    time.sleep(1)

def log_message(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    log_box.update_idletasks()  # 👈 바로 화면 반영

def slow_typing(element, text, delay=0.2):
    for char in text:
        element.send_keys(char)
        time.sleep(delay + random.uniform(0.05, 0.1))  # 약간 랜덤한 딜레이 추가

def slow_type_with_actionchains(driver, element, text, min_delay=0.05, max_delay=0.1):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()
    for char in text:
        actions = ActionChains(driver)
        actions.send_keys(char).perform()
        time.sleep(random.uniform(min_delay, max_delay))

def get_typing_delays():
    try:
        min_delay = float(min_delay_entry.get())
        max_delay = float(max_delay_entry.get())
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay  # 자동 정정
        return min_delay, max_delay
    except ValueError:
        return 0.03, 0.08  # 기본값
    
def slow_type_with_typos(driver, element, text, min_delay=0.05, max_delay=0.1, typo_chance=0.1):
    actions = ActionChains(driver)
    actions.move_to_element(element).click().perform()

    for char in text:
        # 오타 확률 발생
        if random.random() < typo_chance:
            typo_length = random.randint(2, 7)  # 2~3글자짜리 오타 생성
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


def get_typo_chance():
    try:
        typo_chance = float(typo_chance_entry.get())
        return max(0.0, min(typo_chance, 1.0))  # 0~1 사이 값으로 클램핑
    except ValueError:
        return 0.1  # 기본값


# ✅ Selenium 설정
def create_driver():

    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=C:/Users/사용자명/AppData/Local/Google/Chrome/User Data")
    options.add_argument("profile-directory=Default")  # 또는 "Profile 1" 등
    options.add_argument("--start-maximized")

    service = Service(executable_path=ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    return driver

# ✅ 네이버 로그인 (직접 입력 유도)
def naver_login(driver):
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(2)

    # 아이디 입력
    id_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
    id_input.click()
    time.sleep(1)
    pyperclip.copy(user_naver_id)
    id_input.send_keys(Keys.CONTROL, 'v')  # ⬅️ pyautogui 대신 이걸 사용
    time.sleep(1)

    # 비밀번호 입력
    pw_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pw")))
    pw_input.click()
    time.sleep(1)
    pyperclip.copy(user_naver_pw)
    pw_input.send_keys(Keys.CONTROL, 'v')  # ⬅️ 여기도 동일
    time.sleep(1)

    # 로그인 버튼 클릭
    login_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "log.login"))
    )
    login_btn.click()
    time.sleep(3)

    # try:
    #     # ✅ 아이디 입력
    #     id_input = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.ID, "id"))
    #     )
    #     id_input.clear()
    #     slow_type_with_typos(driver, id_input, naver_id, min_delay=0.05, max_delay=0.1, typo_chance=0.1)

    #     # ✅ 비밀번호 입력
    #     pw_input = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.ID, "pw"))
    #     )
    #     pw_input.clear()
    #     slow_type_with_typos(driver, pw_input, naver_pw, min_delay=0.05, max_delay=0.1, typo_chance=0.1)

    #     # ✅ 로그인 버튼 클릭
    #     login_btn = WebDriverWait(driver, 10).until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    #     )
    #     login_btn.click()
    #     log_message("✅ 로그인 버튼 클릭 완료")
    #     time.sleep(3)

    # except Exception:
    #     log_message("❌ 로그인 정보 입력 실패:")
    #     traceback.print_exc()


    # try:
    #     switch = WebDriverWait(driver, 5).until(
    #         EC.presence_of_element_located((By.ID, "switch"))
    #     )
    #     if switch.is_selected():
    #         driver.execute_script("arguments[0].click();", switch)
    #         log_message("✅ IP 보안 스위치 OFF 설정 완료")
    # except Exception:
    #     log_message("⚠️ 스위치 비활성화 실패 (없거나 비정상):")
    #     traceback.print_exc()

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
        log_message("✅ '블로그' 탭 클릭 완료")

        try:
            blog_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "a.MyView-module__link_service___Ok8hP[href='https://blog.naver.com/MyBlog.naver']"
                ))
            )
            blog_link.click()
            log_message("✅ 내 블로그 버튼 클릭 완료")

            original_window = driver.current_window_handle
            time.sleep(2)

            # ✅ 새 창으로 전환
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    log_message("✅ 새 창으로 전환 완료")
                    break

            # ✅ 사용자 블로그 ID 추출
            try:
                current_url = driver.current_url  # 예: https://blog.naver.com/rbdlfdlsp2
                user_id = current_url.rstrip("/").split("/")[-1]
                log_message(f"✅ 블로그 사용자 ID 추출 완료: {user_id}")

                return driver, user_id
            
            except Exception:
                log_message("❌ 블로그 사용자 ID 추출 실패:")
                traceback.print_exc()


        except Exception:
            log_message("❌ 내 블로그 버튼 클릭 실패:")
            traceback.print_exc()

    except Exception:
        log_message("❌ 블로그 탭 클릭 실패:")
        traceback.print_exc()


def write_naver_blog(driver, user_id, title, content):
    min_d, max_d = get_typing_delays()
    time.sleep(3)

    try:
        driver.get(f"https://blog.naver.com/{user_id}?Redirect=Write&")
        log_message("✅ 블로그 글 작성 페이지로 이동 완료")

    except Exception:
        log_message("❌ 블로그 글 작성 페이지로 이동 실패:")
        traceback.print_exc()
    
    try:
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
        )
        log_message("✅ iframe(mainFrame) 진입 완료")

        try:
            load_write = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-popup-button-cancel"))
            )
            load_write.click()
            log_message("✅ 글 이어쓰기 취소 완료")
            time.sleep(1)

        except Exception:
            log_message("⚠️ 글 이어쓰기 취소 실패 (없거나 클릭 안됨)")
            traceback.print_exc()

        try:
            help_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-help-panel-close-button"))
            )
            driver.execute_script("arguments[0].click();", help_btn)
            log_message("✅ 도움말 패널 닫기 성공 (JS click)")
            time.sleep(1)

        except Exception:
            log_message("⚠️ 도움말 패널 닫기 실패 (없거나 클릭 안됨)")
            traceback.print_exc()

        # ✅ 제목 입력
        try:
            title_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-title-text"))
            )
            slow_type_with_actionchains(driver, title_container, title, min_delay=min_d, max_delay=max_d)
            log_message("✅ 제목 입력 완료")
            time.sleep(1)

        except Exception:
            log_message("❌ 제목 입력 실패:")
            traceback.print_exc()

        # ✅ 본문 입력
        try:
            body_paragraph = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div[data-a11y-title='본문'] p.se-text-paragraph"
                ))
            )

            typo_chance = get_typo_chance()
            slow_type_with_typos(driver, body_paragraph, content, min_delay=min_d, max_delay=max_d, typo_chance=typo_chance)

            log_message("✅ 본문 입력 완료")
            time.sleep(1)

        except Exception:
            log_message("❌ 본문 입력 실패:")
            traceback.print_exc()

        

        publish_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='저장']]"))
        )
        publish_button.click()
        log_message("✅ 저장 버튼 클릭 완료")
        time.sleep(1)

        # ✅ 저장 후: 현재 창 닫고 원래 창으로 복귀
        driver.close()  # 현재 블로그 작성 창 닫기
        driver.switch_to.window(driver.window_handles[0])  # 원래 창으로 전환
        log_message("✅ 블로그 작성 창 닫고 원래 창으로 전환 완료")

        # ✅ 네이버 메인으로 이동
        driver.get("https://www.naver.com")
        log_message("✅ 네이버 메인으로 이동 완료")
        time.sleep(1)

        return driver


    except Exception:
        log_message("❌ iframe(mainFrame) 진입 또는 제목 입력 실패:")
        traceback.print_exc()

# ✅ 파일 처리 & 자동 등록 흐름
def process_files(file_paths):
    driver = create_driver()
    naver_login(driver)

    for filepath in file_paths:
        try:
            # 🔁 매 반복마다 작성 페이지 재진입
            driver, user_id = naver_blog(driver)

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.strip().split("\n")
            title = lines[0]
            body = "\n".join(lines[1:])

            log_message(f"📄 {os.path.basename(filepath)} 처리 중...")
            log_message(f"  └ 제목: {title}")
            driver = write_naver_blog(driver, user_id, title, body)

            log_message("✅ 게시 완료")

        except Exception:
            log_message(f"❌ 파일 처리 실패: {filepath}")
            traceback.print_exc()

# ✅ 파일 선택
def choose_file():
    # 네이버 계정 정보를 UI에서 자동으로 가져오기
    global user_naver_id, user_naver_pw
    
    if naver_id_entry and naver_pw_entry:
        user_naver_id = naver_id_entry.get().strip()
        user_naver_pw = naver_pw_entry.get().strip()
    
    # 네이버 계정 정보가 입력되지 않은 경우 경고
    if not user_naver_id or not user_naver_pw:
        messagebox.showwarning("경고", "네이버 계정 정보를 먼저 입력해주세요.")
        return
    
    file_paths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
    if file_paths:
        process_files(file_paths)


# ✅ 파일 드롭
def handle_drop(event):
    file_path = event.data.strip("{}")
    if file_path.endswith(".txt"):
        process_files(file_path)


# ✅ Tkinter UI 구성
def start_login_gui():
    """로그인 화면"""
    login_root = tk.Tk()
    login_root.title("블로그 자동 등록기 - 로그인")
    login_root.geometry("500x400")
    login_root.resizable(False, False)
    
    # 중앙 정렬을 위한 메인 프레임
    main_frame = tk.Frame(login_root)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    # 제목
    title_label = tk.Label(main_frame, text="블로그 자동 등록기", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # 아이디 입력
    id_frame = tk.Frame(main_frame)
    id_frame.pack(fill='x', pady=5)
    
    tk.Label(id_frame, text="아이디:", width=10, anchor='w').pack(side=tk.LEFT)
    id_entry = tk.Entry(id_frame, width=25)
    id_entry.pack(side=tk.LEFT, padx=(10, 0))
    id_entry.focus()
    
    # 비밀번호 입력
    pw_frame = tk.Frame(main_frame)
    pw_frame.pack(fill='x', pady=5)
    
    tk.Label(pw_frame, text="비밀번호:", width=10, anchor='w').pack(side=tk.LEFT)
    pw_entry = tk.Entry(pw_frame, show="*", width=25)
    pw_entry.pack(side=tk.LEFT, padx=(10, 0))
    
    # 로그인 버튼
    def try_login():
        user_id = id_entry.get().strip()
        password = pw_entry.get().strip()
        
        if not user_id or not password:
            messagebox.showerror("입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return
        
        # 로그인 중 표시
        login_btn.config(state='disabled', text="로그인 중...")
        login_root.update()
        
        # API 호출하여 계정 확인
        result = check_blog_account(user_id, password)
        
        if result.get('success'):
            global user_naver_id, user_naver_pw, user_use_date, version_message
            user_naver_id = user_id
            user_naver_pw = password
            user_use_date = result.get('use_date', '')  # API에서 use_date 받아오기
            version_message = result.get('version_message', '')  # API에서 버전 메시지 받아오기
            
            login_root.destroy()
            start_main_gui()
        else:
            error_msg = result.get('error', '알 수 없는 오류가 발생했습니다.')
            messagebox.showerror("로그인 실패", error_msg)
            login_btn.config(state='normal', text="로그인")
    
    login_btn = tk.Button(main_frame, text="로그인", command=try_login, width=15, height=2)
    login_btn.pack(pady=20)
    
    # Enter 키로 로그인
    def on_enter(event):
        try_login()
    
    id_entry.bind('<Return>', on_enter)
    pw_entry.bind('<Return>', on_enter)
    
    # 하단 정보
    info_label = tk.Label(main_frame, text="자금왕 이메일과 비밀번호를 입력해주세요", fg="gray")
    info_label.pack(side=tk.BOTTOM, pady=10)
    
    login_root.mainloop()

def start_main_gui():
    """메인 블로그 등록 화면"""
    global log_box, min_delay_entry, max_delay_entry, typo_chance_entry, root, naver_id_entry, naver_pw_entry
    root = TkinterDnD.Tk()
    root.title("네이버 블로그 자동 등록기")
    root.geometry("1380x800")

    # 네이버 계정 정보 입력 (선택사항)
    naver_frame = tk.LabelFrame(root, text="네이버 계정 정보 (선택사항)", padx=10, pady=10)
    naver_frame.pack(fill='x', padx=10, pady=5)
    
    naver_id_frame = tk.Frame(naver_frame)
    naver_id_frame.pack(fill='x', pady=2)
    
    tk.Label(naver_id_frame, text="네이버 아이디:", width=16, anchor='w').pack(side=tk.LEFT)
    naver_id_entry = tk.Entry(naver_id_frame, width=25)
    naver_id_entry.pack(side=tk.LEFT, padx=(10, 0))
    
    naver_pw_frame = tk.Frame(naver_frame)
    naver_pw_frame.pack(fill='x', pady=2)
    
    tk.Label(naver_pw_frame, text="네이버 비밀번호:", width=16, anchor='w').pack(side=tk.LEFT)
    naver_pw_entry = tk.Entry(naver_pw_frame, show="*", width=25)
    naver_pw_entry.pack(side=tk.LEFT, padx=(10, 0))

    # 타이핑 속도 입력창
    speed_frame = tk.LabelFrame(root, text="타이핑 속도 설정", padx=10, pady=10)
    speed_frame.pack(fill='x', padx=10, pady=5)

    tk.Label(speed_frame, text="n초마다 타이핑: 최소").pack(side=tk.LEFT)
    min_delay_entry = tk.Entry(speed_frame, width=5)
    min_delay_entry.insert(0, "0.05")
    min_delay_entry.pack(side=tk.LEFT, padx=(0, 10))

    tk.Label(speed_frame, text="최대").pack(side=tk.LEFT)
    max_delay_entry = tk.Entry(speed_frame, width=5)
    max_delay_entry.insert(0, "1.2")
    max_delay_entry.pack(side=tk.LEFT)

    # 오타 확률 입력창
    typo_frame = tk.LabelFrame(root, text="오타 설정", padx=10, pady=10)
    typo_frame.pack(fill='x', padx=10, pady=5)

    tk.Label(typo_frame, text="오타 확률(자동으로 오타 냈다가 다시 지움), 0:오타 없음, 1:전부 오타 (0~1): ").pack(side=tk.LEFT)
    typo_chance_entry = tk.Entry(typo_frame, width=5)
    typo_chance_entry.insert(0, "0.12")  # 기본값 10%
    typo_chance_entry.pack(side=tk.LEFT)

    # 파일 선택 (실행 로그 바로 위에 위치)
    file_frame = tk.LabelFrame(root, text="파일 선택", padx=10, pady=10)
    file_frame.pack(fill='x', padx=10, pady=5)
    
    tk.Button(file_frame, text="파일 선택하기", command=choose_file).pack(pady=5)

    # 로그 출력창
    log_frame = tk.LabelFrame(root, text="실행 로그", padx=10, pady=10)
    log_frame.pack(fill='both', expand=True, padx=10, pady=5)
    
    log_box = tk.Text(log_frame, height=10, wrap='word')
    log_box.pack(fill='both', expand=True)
    log_box.insert(tk.END, "🟢 프로그램 시작됨...\n")
    
    # 사용 가능 기간 표시
    if user_use_date:
        # ISO 형식의 날짜를 YYYY-MM-DD 형식으로 변환
        try:
            # ISO 형식 (예: 2099-09-09T00:00:00)에서 날짜 부분만 추출
            formatted_date = user_use_date.split('T')[0]
            log_box.insert(tk.END, f"📅 사용 가능 기간: {formatted_date} 까지\n")
        except:
            # 변환 실패 시 원본 값 그대로 표시
            log_box.insert(tk.END, f"📅 사용 가능 기간: {user_use_date} 까지\n")

        log_box.see(tk.END)
    
    # 버전 메시지 표시
    if version_message:
        log_box.insert(tk.END, f"⚠️{version_message}\n")
        log_box.see(tk.END)

# def launch_login_ui():
#     login_root = tk.Tk()
#     login_root.title("사용자 로그인")
#     login_root.geometry("400x250")

#     tk.Label(login_root, text="아이디").pack(pady=(10, 0))
#     id_entry = tk.Entry(login_root)
#     id_entry.pack()

#     tk.Label(login_root, text="비밀번호").pack(pady=(10, 0))
#     pw_entry = tk.Entry(login_root, show="*")
#     pw_entry.pack()

#     def try_login():
#         user_id = id_entry.get()
#         password = pw_entry.get()

#         valid_users = {
#             "test": "test",
#             "wnk1cx": "80rnnu",
#             "cg8cdx": "sxjws1",
#             "cprnnn": "i0x752",
#             "tvtkys": "dzg015",
#             "i604pv": "2g4b2y",
#             "lj0u6i": "mic8xq",
#             "result": "ga05190519!",
#             "8orwvw": "l3ff6g",
#             "h25z66": "i61vs6",
#         }
#         if valid_users.get(user_id) == password:
#             login_root.destroy()
#             start_main_gui()
#         else:
#             messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 틀렸습니다.")

#     tk.Button(login_root, text="로그인", command=try_login).pack(pady=15)

#     tk.Label(login_root, text="문의: 010-3217-1424", fg="gray").pack(pady=(10, 0))
#     login_root.mainloop()

# === 프로그램 시작 ===
if __name__ == "__main__":
    start_login_gui()