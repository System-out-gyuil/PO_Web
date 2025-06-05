from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from langchain_openai import ChatOpenAI
from config import OPEN_AI_API_KEY
import pdfplumber
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
import os
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
from django.http import HttpResponse
import zipfile
import shutil
import subprocess
import tempfile

class BlogView(View):
    def get(self, request):
        return render(request, 'naver_blog/naver_blog.html')

@method_decorator(csrf_exempt, name='dispatch')
class BlogGPTAPIView(View):
    def post(self, request):
        def convert_hwp_to_pdf(hwp_path):
            output_dir = os.path.dirname(hwp_path)
            try:
                result = subprocess.run([
                    "libreoffice", "--headless",
                    "--convert-to", "pdf:writer_pdf_Export",
                    hwp_path,
                    "--outdir", output_dir
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

                print("🖥️ libreoffice stdout:", result.stdout.decode())

                pdf_name = os.path.splitext(os.path.basename(hwp_path))[0] + ".pdf"
                converted_pdf = os.path.join(output_dir, pdf_name)

                if os.path.exists(converted_pdf):
                    return converted_pdf
                else:
                    print(f"[❌ 변환 실패] {converted_pdf} 존재하지 않음")
                    return ""
            except Exception as e:
                print(f"[예외 발생] HWP → PDF 변환 실패: {e}")
                return ""

        user_input = request.POST.get("input", "")
        files = request.FILES.getlist("files")
        file_list = []

        for file in files:
            full_text = ""
            print(f"input: {user_input}")
            print(f"file name: {file.name}, size: {file.size}")

            try:
                if file.name.endswith(".txt"):
                    full_text = file.read().decode("utf-8")

                elif file.name.endswith(".pdf"):
                    with pdfplumber.open(file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                full_text += text + "\n"

                elif file.name.endswith(".hwp"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".hwp") as tmp_hwp:
                        for chunk in file.chunks():
                            tmp_hwp.write(chunk)
                        tmp_hwp_path = tmp_hwp.name

                    pdf_path = convert_hwp_to_pdf(tmp_hwp_path)

                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            with pdfplumber.open(pdf_path) as pdf:
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    if text:
                                        full_text += text + "\n"
                        except Exception as e:
                            print(f"[PDF 파싱 실패]: {e}")
                        finally:
                            os.remove(pdf_path)
                    os.remove(tmp_hwp_path)

            except Exception as e:
                print(f"[파일 처리 중 오류]: {e}")
                full_text = "(본문을 읽는 중 오류 발생)"

            # GPT 호출
            llm = ChatOpenAI(temperature=0, model_name='gpt-4o-mini', openai_api_key=OPEN_AI_API_KEY, max_tokens=10000)
            input_data = f"{user_input}\n\n{full_text}"
            response = llm.invoke(input_data)
            content = response.content.replace("**", "").replace("#", "").strip()
            print("[GPT 응답]:", content)

            file_list.append(content)

        # 결과 저장
        save_dir = os.path.join(settings.MEDIA_ROOT, 'naver_blog_원고')
        os.makedirs(save_dir, exist_ok=True)

        for file_content in file_list:
            first_line = file_content.strip().split('\n')[0][:60]
            safe_name = "".join(c if c.isalnum() else "_" for c in first_line)
            filename = f"{safe_name}.txt"
            file_path = os.path.join(save_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            print(f"파일 저장 완료: {file_path}")

        return JsonResponse({"response": "파일 처리 성공", "previews": file_list})
    
class DownloadZipView(View):
    def get(self, request):
        # 1. 압축 대상 폴더
        source_dir = os.path.join(settings.MEDIA_ROOT, 'naver_blog_원고')
        if not os.path.exists(source_dir):
            return HttpResponse("원고 폴더가 존재하지 않습니다.", status=404)

        # 2. zip 파일 경로
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"naver_blog_texts_{timestamp}.zip"
        zip_path = os.path.join(settings.MEDIA_ROOT, zip_filename)

        # 3. zip 파일 생성
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=source_dir)
                    zipf.write(file_path, arcname)

        # 4. 사용자에게 파일 전송
        with open(zip_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'

        # 5. zip 파일과 원본 폴더 삭제
        try:
            os.remove(zip_path)  # zip 파일 삭제
            shutil.rmtree(source_dir)  # 원고 텍스트 폴더 전체 삭제
        except Exception as e:
            print(f"삭제 중 오류 발생: {e}")

        return response
    
@method_decorator(csrf_exempt, name='dispatch')
class SaveTxtView(View):
    def post(self, request):
        data = json.loads(request.body)
        text = data.get("input", "")

        print("저장할 텍스트:", text)
        # 저장할 디렉토리 생성
        save_dir = os.path.join(settings.MEDIA_ROOT, 'naver_blog_texts')
        os.makedirs(save_dir, exist_ok=True)

        # 첫 번째 줄 추출 + 파일명으로 사용
        first_line = text.strip().split('\n')[0][:60]  # 너무 긴 제목 방지
        filename = f"{first_line}.txt"
        file_path = os.path.join(save_dir, filename)

        # 파일 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"파일 저장 완료: {file_path}")

        return JsonResponse({"response": "파일 처리 성공", "filename": filename})


# @method_decorator(csrf_exempt, name='dispatch')
# class BlogWriteView(View):
#     def post(self, request):
#         print("블로그 작성 요청")

#         # 저장된 텍스트 파일 디렉토리
#         folder_path = os.path.join(settings.MEDIA_ROOT, 'naver_blog_texts')

#         file_texts = []

#         # 폴더 내 모든 .txt 파일 순회
#         if os.path.exists(folder_path):
#             for filename in os.listdir(folder_path):
#                 if filename.endswith('.txt'):
#                     file_path = os.path.join(folder_path, filename)
#                     with open(file_path, 'r', encoding='utf-8') as f:
#                         content = f.read()
#                         file_texts.append({
#                             "filename": filename,
#                             "content": content
#                         })
        
#         print(file_texts)


# # ==============================================================================
#         def slow_type_with_typos(driver, element, text, min_delay=0.05, max_delay=0.1, typo_chance=0.1):
#             actions = ActionChains(driver)
#             actions.move_to_element(element).click().perform()

#             for char in text:
#                 # 오타 확률 발생
#                 if random.random() < typo_chance:
#                     typo_length = random.randint(2, 7)  # 2~3글자짜리 오타 생성
#                     fake_chars = ''.join(random.choices("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ", k=typo_length))

#                     # 오타 입력
#                     actions = ActionChains(driver)
#                     actions.send_keys(fake_chars).perform()
#                     time.sleep(random.uniform(min_delay, max_delay))

#                     # 오타 지우기 (Backspace 여러 번)
#                     for _ in range(typo_length):
#                         actions = ActionChains(driver)
#                         actions.send_keys(Keys.BACKSPACE).perform()
#                         time.sleep(random.uniform(min_delay, max_delay))

#                 # 정상 글자 입력
#                 actions = ActionChains(driver)
#                 actions.send_keys(char).perform()
#                 time.sleep(random.uniform(min_delay, max_delay))

#         def slow_type_with_actionchains(driver, element, text, min_delay=0.05, max_delay=0.1):
#             actions = ActionChains(driver)
#             actions.move_to_element(element).click().perform()
#             for char in text:
#                 actions = ActionChains(driver)
#                 actions.send_keys(char).perform()
#                 time.sleep(random.uniform(min_delay, max_delay))

#         def get_typo_chance():
#             try:
#                 typo_chance = 0.1
#                 # typo_chance = float(typo_chance_entry.get())
#                 return max(0.0, min(typo_chance, 1.0))  # 0~1 사이 값으로 클램핑
#             except ValueError:
#                 return 0.1  # 기본값
#         def get_typing_delays():
#             try:
#                 min_delay = 0.03
#                 max_delay = 0.08
#                 # min_delay = float(min_delay_entry.get())
#                 # max_delay = float(max_delay_entry.get())
#                 if min_delay > max_delay:
#                     min_delay, max_delay = max_delay, min_delay  # 자동 정정
#                 return min_delay, max_delay
#             except ValueError:
#                 return 0.03, 0.08  # 기본값

#         # ✅ Selenium 설정
#         def create_driver():
#             options = webdriver.ChromeOptions()
#             options.add_argument("--start-maximized")
#             # options.add_argument("user-data-dir=selenium")  # 쿠키 저장용
#             driver = webdriver.Chrome(options=options)
#             return driver
        
#         # ✅ 네이버 로그인 (직접 입력 유도)
#         def naver_login(driver):
#             driver.get("https://nid.naver.com/nidlogin.login")
#             time.sleep(1)

#             try:
#                 switch = WebDriverWait(driver, 5).until(
#                     EC.presence_of_element_located((By.ID, "switch"))
#                 )
#                 if switch.is_selected():
#                     driver.execute_script("arguments[0].click();", switch)
#                     print("✅ IP 보안 스위치 OFF 설정 완료")
#             except Exception:
#                 print("⚠️ 스위치 비활성화 실패 (없거나 비정상):")

#         # ✅ 블로그 글 작성페이지로 들어가기
#         def naver_blog(driver):
#             try:
#                 blog_tab = WebDriverWait(driver, 600).until(
#                     EC.element_to_be_clickable((
#                         By.XPATH,
#                         "//li[contains(@class, 'MyView-module__menu_item')][.//span[contains(text(), '블로그')]]"
#                     ))
#                 )
#                 blog_tab.click()
#                 print("✅ '블로그' 탭 클릭 완료")

#                 try:
#                     blog_link = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((
#                             By.CSS_SELECTOR,
#                             "a.MyView-module__link_service___Ok8hP[href='https://blog.naver.com/MyBlog.naver']"
#                         ))
#                     )
#                     blog_link.click()
#                     print("✅ 내 블로그 버튼 클릭 완료")

#                     original_window = driver.current_window_handle
#                     time.sleep(2)

#                     # ✅ 새 창으로 전환
#                     for handle in driver.window_handles:
#                         if handle != original_window:
#                             driver.switch_to.window(handle)
#                             print("✅ 새 창으로 전환 완료")
#                             break

#                     # ✅ 사용자 블로그 ID 추출
#                     try:
#                         current_url = driver.current_url  # 예: https://blog.naver.com/rbdlfdlsp2
#                         user_id = current_url.rstrip("/").split("/")[-1]
#                         print(f"✅ 블로그 사용자 ID 추출 완료: {user_id}")

#                         return driver, user_id
                    
#                     except Exception:
#                         print("❌ 블로그 사용자 ID 추출 실패:")
#                         traceback.print_exc()


#                 except Exception:
#                     print("❌ 내 블로그 버튼 클릭 실패:")
#                     traceback.print_exc()

#             except Exception:
#                 print("❌ 블로그 탭 클릭 실패:")
#                 traceback.print_exc()

#         def write_naver_blog(driver, user_id, title, content):
#             min_d, max_d = get_typing_delays()
#             time.sleep(3)

#             try:
#                 driver.get(f"https://blog.naver.com/{user_id}?Redirect=Write&")
#                 print("✅ 블로그 글 작성 페이지로 이동 완료")

#             except Exception:
#                 print("❌ 블로그 글 작성 페이지로 이동 실패:")
#                 traceback.print_exc()
            
#             try:
#                 WebDriverWait(driver, 10).until(
#                     EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
#                 )
#                 print("✅ iframe(mainFrame) 진입 완료")

#                 try:
#                     load_write = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-popup-button-cancel"))
#                     )
#                     load_write.click()
#                     print("✅ 글 이어쓰기 취소 완료")
#                     time.sleep(1)

#                 except Exception:
#                     print("⚠️ 글 이어쓰기 취소 실패 (없거나 클릭 안됨)")
#                     traceback.print_exc()

#                 try:
#                     help_btn = WebDriverWait(driver, 5).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "button.se-help-panel-close-button"))
#                     )
#                     driver.execute_script("arguments[0].click();", help_btn)
#                     print("✅ 도움말 패널 닫기 성공 (JS click)")
#                     time.sleep(1)

#                 except Exception:
#                     print("⚠️ 도움말 패널 닫기 실패 (없거나 클릭 안됨)")
#                     traceback.print_exc()

#                 # ✅ 제목 입력
#                 try:
#                     title_container = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-title-text"))
#                     )
#                     slow_type_with_actionchains(driver, title_container, title, min_delay=min_d, max_delay=max_d)
#                     print("✅ 제목 입력 완료")
#                     time.sleep(1)

#                 except Exception:
#                     print("❌ 제목 입력 실패:")
#                     traceback.print_exc()

#                 # ✅ 본문 입력
#                 try:
#                     body_paragraph = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((
#                             By.CSS_SELECTOR,
#                             "div[data-a11y-title='본문'] p.se-text-paragraph"
#                         ))
#                     )

#                     typo_chance = get_typo_chance()
#                     slow_type_with_typos(driver, body_paragraph, content, min_delay=min_d, max_delay=max_d, typo_chance=typo_chance)

#                     print("✅ 본문 입력 완료")
#                     time.sleep(1)

#                 except Exception:
#                     print("❌ 본문 입력 실패:")
#                     traceback.print_exc()

                

#                 publish_button = WebDriverWait(driver, 10).until(
#                     EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='저장']]"))
#                 )
#                 publish_button.click()
#                 print("✅ 저장 버튼 클릭 완료")
#                 time.sleep(1)

#                 # ✅ 저장 후: 현재 창 닫고 원래 창으로 복귀
#                 driver.close()  # 현재 블로그 작성 창 닫기
#                 driver.switch_to.window(driver.window_handles[0])  # 원래 창으로 전환
#                 print("✅ 블로그 작성 창 닫고 원래 창으로 전환 완료")

#                 # ✅ 네이버 메인으로 이동
#                 driver.get("https://www.naver.com")
#                 print("✅ 네이버 메인으로 이동 완료")
#                 time.sleep(1)

#                 return driver


#             except Exception:
#                 print("❌ iframe(mainFrame) 진입 또는 제목 입력 실패:")
#                 traceback.print_exc()

#             # ✅ 파일 처리 & 자동 등록 흐름
#         def process_files(file_paths):
#             driver = create_driver()
#             naver_login(driver)

#             for filepath in file_paths:
#                 file_path = os.path.join(folder_path, filepath.get("filename"))
#                 try:
#                     # 🔁 매 반복마다 작성 페이지 재진입
#                     driver, user_id = naver_blog(driver)

#                     with open(file_path, "r", encoding="utf-8") as f:
#                         content = f.read()

#                     lines = content.strip().split("\n")
#                     title = lines[0]
#                     body = "\n".join(lines[1:])

#                     print(f"📄 {os.path.basename(file_path)} 처리 중...")
#                     print(f"  └ 제목: {title}")
#                     driver = write_naver_blog(driver, user_id, title, body)

#                     print("✅ 게시 완료")

#                 except Exception:
#                     print(f"❌ 파일 처리 실패: {file_path}")
#                     traceback.print_exc()

# # ==============================================================================

#         process_files(file_texts)

#         context = {
#             "files": file_texts
#         }

#         return JsonResponse("success")