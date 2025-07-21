import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import logging
import os
import tempfile
from datetime import datetime
from config import OPEN_AI_API_KEY, AWS_S3_ACCESS_KEY, AWS_S3_SECRET_KEY, AWS_S3_BUCKET_NAME, AWS_S3_REGION
from .models import Row, AttributeValue, Attribute
import pdfplumber
import uuid
import time
import subprocess
from PIL import Image
import warnings
import boto3
from botocore.exceptions import ClientError
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

@csrf_exempt
def ai_chat(request):
    """AI 채팅 API 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})
    
    try:
        # JSON 데이터 파싱
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        row_id = data.get('row_id')  # 행 ID 추가
        force_refresh = data.get('force_refresh', False)  # 강제 새로고침 플래그
        
        if not message:
            return JsonResponse({'success': False, 'error': '메시지가 비어있습니다'})
        
        # OpenAI API 키 확인
        if not OPEN_AI_API_KEY:
            return JsonResponse({'success': False, 'error': 'OpenAI API 키가 설정되지 않았습니다'})
        
        # 행 데이터 가져오기 (캐싱 활용)
        row_data = {}
        file_texts = []
        
        if row_id:
            # 세션에서 캐시된 데이터 확인
            cache_key = f'ai_chat_row_{row_id}'
            cached_data = request.session.get(cache_key)
            
            if cached_data and not force_refresh:
                # 캐시 만료 시간 체크 (30분)
                cache_timestamp = cached_data.get('timestamp', 0)
                current_time = time.time()
                cache_age = current_time - cache_timestamp
                
                if cache_age < 1800:  # 30분 (1800초)
                    # 캐시된 데이터 사용
                    row_data = cached_data.get('row_data', {})
                    file_texts = cached_data.get('file_texts', [])
                    print(f"[AI 캐시 HIT] row_id={row_id}")
                    print(f"  row_data: {json.dumps(row_data, ensure_ascii=False, indent=2)}")
                    for file_text in file_texts:
                        print(f"  file_text: {file_text}")
                    print(f"  캐시 timestamp: {cached_data.get('timestamp')}")
                    print(f"캐시된 데이터 사용: 행 {row_id} (캐시 나이: {cache_age:.1f}초)")
                else:
                    # 캐시 만료, 새로 생성
                    print(f"캐시 만료됨: 행 {row_id} (캐시 나이: {cache_age:.1f}초)")
                    if cache_key in request.session:
                        del request.session[cache_key]
                    cached_data = None
            else:
                # 캐시가 없거나 강제 새로고침이면 새로 생성
                if force_refresh:
                    print(f"강제 새로고침: 행 {row_id}")
                    if cache_key in request.session:
                        del request.session[cache_key]
                    cached_data = None
                try:
                    row = Row.objects.get(id=row_id)
                    user = row.user
                    
                    # 해당 행의 모든 속성값 가져오기
                    attribute_values = AttributeValue.objects.filter(row=row)
                    
                    for attr_value in attribute_values:
                        attr_name = attr_value.attribute.name
                        attr_type = attr_value.attribute.attributeType.name
                        
                        if attr_type == 'file':
                            # 파일인 경우 텍스트 추출
                            if attr_value.value:
                                try:
                                    # 파일 데이터 파싱
                                    file_data = json.loads(attr_value.value) if isinstance(attr_value.value, str) else attr_value.value
                                    
                                    # 음성파일 속성인 경우 (data 구조)
                                    if isinstance(file_data, dict) and 'data' in file_data:
                                        for file_id, file_info in file_data['data'].items():
                                            print(f'file_info: {file_info.get("type")}')

                                            if file_info.get('type') == 'file':
                                                # 파일 크기 체크 (10MB 제한)
                                                file_size = file_info.get('file_size', 0)
                                                if file_size > 10 * 1024 * 1024:  # 10MB
                                                    file_texts.append(f"[{attr_name} - {file_info.get('original_filename', '파일')}]: 파일이 너무 커서 텍스트 추출을 건너뜁니다.")
                                                    continue
                                                
                                                try:
                                                    file_path = None
                                                    # S3 키가 있으면 직접 사용
                                                    s3_key = file_info.get('s3_key')
                                                    if s3_key:
                                                        file_path = download_file_from_s3_key(s3_key)
                                                    # S3 키가 없고 download_url이 있으면 사용
                                                    elif file_info.get('download_url'):
                                                        file_path = download_file_from_url(file_info['download_url'])
                                                    
                                                    if file_path and os.path.exists(file_path):
                                                        file_text = extract_text_from_file(file_path)
                                                        if file_text:
                                                            file_texts.append(f"[{attr_name} - {file_info.get('original_filename', '파일')}]:\n{file_text}")
                                                        # 임시 파일 정리
                                                        try:
                                                            os.remove(file_path)
                                                        except:
                                                            pass
                                                except Exception as e:
                                                    logger.error(f"음성파일 텍스트 추출 실패: {e}")

                                            elif file_info.get('type') == 'text':
                                                print(f'file_info: {file_info.get("text")}')
                                                file_texts.append(file_info.get('text'))
                                                
                                    # 일반 파일 속성인 경우 (배열 구조)
                                    elif isinstance(file_data, list):
                                        for file_info in file_data:
                                            # 파일 크기 체크 (10MB 제한)
                                            file_size = file_info.get('file_size', 0)
                                            if file_size > 10 * 1024 * 1024:  # 10MB
                                                file_texts.append(f"[{attr_name} - {file_info.get('original_filename', '파일')}]: 파일이 너무 커서 텍스트 추출을 건너뜁니다.")
                                                continue
                                            
                                            try:
                                                file_path = None
                                                # S3 키가 있으면 직접 사용
                                                s3_key = file_info.get('s3_key')
                                                if s3_key:
                                                    file_path = download_file_from_s3_key(s3_key)
                                                # S3 키가 없고 download_url이 있으면 사용
                                                elif file_info.get('download_url'):
                                                    file_path = download_file_from_url(file_info['download_url'])
                                                
                                                if file_path and os.path.exists(file_path):
                                                    file_text = extract_text_from_file(file_path)
                                                    if file_text:
                                                        file_texts.append(f"[{attr_name} - {file_info.get('original_filename', '파일')}]:\n{file_text}")
                                                    # 임시 파일 정리
                                                    try:
                                                        os.remove(file_path)
                                                    except:
                                                        pass
                                            except Exception as e:
                                                logger.error(f"일반파일 텍스트 추출 실패: {e}")
                                    
                                    # 단일 파일 경로인 경우
                                    else:
                                        file_path = attr_value.value
                                        if file_path.startswith('http'):
                                            file_path = download_file_from_url(file_path)
                                        
                                        if file_path and os.path.exists(file_path):
                                            file_text = extract_text_from_file(file_path)
                                            if file_text:
                                                file_texts.append(f"[{attr_name} 파일 내용]:\n{file_text}")
                                            
                                            # 임시 파일 정리
                                            if attr_value.value.startswith('http'):
                                                try:
                                                    os.remove(file_path)
                                                except:
                                                    pass
                                                            
                                except Exception as e:
                                    logger.error(f"파일 텍스트 추출 실패: {e}")
                        
                        elif attr_type == 'outstanding_debts':
                            # 기대출 데이터 처리
                            if attr_value.value:
                                try:
                                    debt_data = json.loads(attr_value.value) if isinstance(attr_value.value, str) else attr_value.value
                                    if isinstance(debt_data, dict):
                                        debt_summary = []
                                        for key, value in debt_data.items():
                                            if value and value != 0:
                                                debt_summary.append(f"{key}: {value:,}만원")
                                        if debt_summary:
                                            row_data[attr_name] = " | ".join(debt_summary)
                                except Exception as e:
                                    logger.error(f"기대출 데이터 처리 실패: {e}")
                        
                        elif attr_type == 'recommend':
                            # 추천 데이터 처리
                            if attr_value.value:
                                try:
                                    recommend_data = json.loads(attr_value.value) if isinstance(attr_value.value, str) else attr_value.value
                                    if isinstance(recommend_data, dict):
                                        # 총 자금 정보
                                        total_funds = recommend_data.get('총자금', 0)
                                        if total_funds:
                                            row_data[f"{attr_name}_총자금"] = f"{total_funds:,}원"
                                        
                                        # 자금들 정보
                                        funds = recommend_data.get('자금들', {})
                                        if funds:
                                            fund_summary = []
                                            for fund_name, amount in funds.items():
                                                if amount and amount > 0:
                                                    fund_summary.append(f"{fund_name}: {amount:,}원")
                                            if fund_summary:
                                                row_data[f"{attr_name}_자금들"] = " | ".join(fund_summary)
                                        
                                        # 상세정보
                                        detail_info = recommend_data.get('상세정보', [])
                                        if detail_info:
                                            detail_summary = []
                                            for detail in detail_info:
                                                fund_name = detail.get('fund_name', '')
                                                limit = detail.get('limit', 0)
                                                institution = detail.get('institution', '')
                                                if fund_name and limit:
                                                    detail_summary.append(f"{fund_name}({institution}): {limit:,}원")
                                            if detail_summary:
                                                row_data[f"{attr_name}_상세정보"] = " | ".join(detail_summary)
                                except Exception as e:
                                    logger.error(f"추천 데이터 처리 실패: {e}")
                        
                        elif attr_type == 'dropdown':
                            # 드롭다운 데이터 처리
                            if attr_value.value:
                                try:
                                    dropdown_data = json.loads(attr_value.value) if isinstance(attr_value.value, str) else attr_value.value
                                    if isinstance(dropdown_data, dict):
                                        # 선택된 옵션의 라벨 표시
                                        if 'label' in dropdown_data:
                                            row_data[attr_name] = dropdown_data['label']
                                        elif 'selected_options' in dropdown_data and dropdown_data['selected_options']:
                                            options = []
                                            for option in dropdown_data['selected_options']:
                                                if 'label' in option:
                                                    options.append(option['label'])
                                            if options:
                                                row_data[attr_name] = " | ".join(options)
                                        else:
                                            row_data[attr_name] = str(attr_value.value)
                                    else:
                                        row_data[attr_name] = str(attr_value.value)
                                except Exception as e:
                                    logger.error(f"드롭다운 데이터 처리 실패: {e}")
                                    row_data[attr_name] = str(attr_value.value)
                        
                        elif attr_type == 'datetime':
                            # 날짜 데이터 처리
                            if attr_value.value:
                                try:
                                    # ISO 형식 날짜를 읽기 쉬운 형식으로 변환
                                    date_obj = datetime.fromisoformat(attr_value.value.replace('Z', '+00:00'))
                                    row_data[attr_name] = date_obj.strftime('%Y년 %m월 %d일')
                                except Exception as e:
                                    logger.error(f"날짜 데이터 처리 실패: {e}")
                                    row_data[attr_name] = str(attr_value.value)
                        
                        elif attr_type == 'number':
                            # 숫자 데이터 처리
                            if attr_value.value:
                                try:
                                    num_value = float(attr_value.value)
                                    if num_value >= 100000000:  # 1억 이상
                                        row_data[attr_name] = f"{num_value/100000000:.1f}억원"
                                    elif num_value >= 10000:  # 1만 이상
                                        row_data[attr_name] = f"{num_value/10000:.0f}만원"
                                    else:
                                        row_data[attr_name] = f"{num_value:,}원"
                                except Exception as e:
                                    logger.error(f"숫자 데이터 처리 실패: {e}")
                                    row_data[attr_name] = str(attr_value.value)
                        
                        else:
                            # 일반 텍스트 데이터 (text, age, region, region_detail 등)
                            if attr_value.value:
                                row_data[attr_name] = str(attr_value.value)
                    
                    # 캐시에 데이터 저장 (30분 유효)
                    cache_data = {
                        'row_data': row_data,
                        'file_texts': file_texts,
                        'timestamp': time.time()
                    }
                    request.session[cache_key] = cache_data
                    request.session.modified = True
                    
                    print(f"새로운 데이터 캐시 생성: 행 {row_id}")
                    
                except Row.DoesNotExist:
                    return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다'})
                except Exception as e:
                    logger.error(f"행 데이터 조회 실패: {e}")
        
        # OpenAI API 호출
        headers = {
            'Authorization': f'Bearer {OPEN_AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 오늘 날짜 정보 추가
        from datetime import datetime, timezone
        today_str = datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # 컨텍스트 정보 구성
        context_info = f"\n\n[오늘 날짜(현실 기준)]: {today_str}\n\n"
        if row_data:
            context_info += f"\n[현재 행 데이터]:\n"
            for key, value in row_data.items():
                if value:
                    context_info += f"- {key}: {value}\n"
        
        if file_texts:
            context_info += f"\n[첨부 파일 내용]:\n"
            for file_text in file_texts:
                context_info += f"{file_text}\n"
        
        # 영업 관련 컨텍스트를 포함한 프롬프트 생성
        system_prompt = """당신은 영업 전문가 AI 어시스턴트입니다. 
        사용자의 영업 관련 질문에 대해 도움이 되는 답변을 제공해주세요.
        답변은 친근하고 실용적이며, 한국어로 작성해주세요.
        영업 전략, 고객 관리, 매출 증대, 리드 관리 등에 대한 조언을 제공할 수 있습니다.
        
        사용자가 제공한 행 데이터와 첨부 파일 내용을 참고하여 더 구체적이고 맞춤형 답변을 제공해주세요.
        
        특히 다음 정보들을 활용하여 답변해주세요:
        - 회사 기본 정보 (회사명, 업종, 지역 등)
        - 재무 정보 (매출, 기대출, 추천 자금 등)
        - 첨부된 문서의 내용 (재무제표, 대출내역, 확인서 등)
        - 날짜 정보 (설립일, F/U 일정 등)"""
        
        user_message = f"{message}{context_info}"
        
        # print(f'context_info: {context_info}')
        
        payload = {
            'model': 'gpt-4.1-mini',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 1500,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            return JsonResponse({
                'success': True,
                'response': ai_response
            })
        else:
            error_msg = f"OpenAI API 오류: {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg = f"OpenAI API 오류: {error_data['error'].get('message', '알 수 없는 오류')}"
            except:
                pass
            return JsonResponse({'success': False, 'error': error_msg})
            
    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'error': '요청 시간이 초과되었습니다. 다시 시도해주세요.'})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'success': False, 'error': f'네트워크 오류: {str(e)}'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다'})
    except Exception as e:
        logger.error(f"AI 채팅 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': f'서버 오류: {str(e)}'})

@csrf_exempt
def ai_chat_cache_clear(request):
    """AI 채팅 캐시 삭제 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 지원합니다'})
    try:
        data = json.loads(request.body)
        row_id = data.get('row_id')
        if not row_id:
            return JsonResponse({'success': False, 'error': 'row_id가 필요합니다'})
        cache_key = f'ai_chat_row_{row_id}'
        if cache_key in request.session:
            del request.session[cache_key]
            request.session.modified = True
            return JsonResponse({'success': True, 'message': '캐시가 삭제되었습니다'})
        else:
            return JsonResponse({'success': True, 'message': '캐시가 존재하지 않습니다'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def extract_text_from_file(file_path):
    """파일에서 텍스트 추출 (update_bizinfo.py 참고) - PDF 표 우선 추출, 텍스트 부족시 OCR 자동 fallback"""
    import os
    if not file_path or not os.path.exists(file_path):
        return ""
    
    def is_text_extracted_enough(file_path, extracted_text):
        file_size = os.path.getsize(file_path)
        text_length = len(extracted_text)
        if file_size == 0:
            return False
        ratio = text_length / file_size
        return ratio > 0.001  # 0.1% 이상이면 텍스트가 어느 정도 있다고 판단

    try:
        if file_path.endswith(".pdf"):
            import tempfile
            with pdfplumber.open(file_path) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        all_tables.append(table)
                if all_tables:
                    # 표가 있으면 표만 추출
                    table_texts = []
                    for table in all_tables:
                        table_texts.append('\n'.join(['\t'.join([cell if cell is not None else '' for cell in row]) for row in table if row]))
                    result = '\n\n'.join(table_texts)
                else:
                    # 표가 없으면 기존 방식
                    text = ''
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n'
                    result = text.strip()
            # 텍스트 부족시 OCR 자동 fallback
            if not is_text_extracted_enough(file_path, result):
                ocr_texts = []
                with pdfplumber.open(file_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        # 페이지를 이미지로 저장
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
                            img = page.to_image(resolution=300)
                            img.save(tmp_img.name, format='PNG')
                            # OCR 수행
                            ocr_text = clova_ocr(tmp_img.name, 'jpg')
                            ocr_texts.append(f"[페이지 {i+1} OCR 결과]:\n{ocr_text}")
                            try:
                                os.remove(tmp_img.name)
                            except:
                                pass
                return f"[경고] 이 PDF는 텍스트가 거의 없는 이미지 기반 PDF로 판단되어 OCR로 텍스트를 추출했습니다.\n\n" + '\n\n'.join(ocr_texts)
            return result
        elif file_path.endswith((".jpg", ".jpeg", ".png")):
            return clova_ocr(file_path, "jpg")
        elif file_path.endswith(".hwp"):
            pdf_path = convert_hwp_to_pdf(file_path)
            if os.path.exists(pdf_path):
                extracted_text = extract_text_from_file(pdf_path)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                return extracted_text
            else:
                return "HWP 파일 변환 실패"
        return ""
    except Exception as e:
        logger.error(f"텍스트 추출 실패: {e}")
        return ""

def is_text_pdf(file_path):
    """PDF가 텍스트 기반인지 확인"""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:2]:
                if page.extract_text():
                    return True
        return False
    except:
        return False

def clova_ocr(file_path, fmt):
    """Clova OCR을 사용한 텍스트 추출"""
    from config import NAVER_CLOVA_OCR_API_KEY, NAVER_CLOUD_CLOVA_OCR_API_URL
    
    request_json = {
        'images': [{'format': fmt, 'name': 'demo'}],
        'requestId': str(uuid.uuid4()),
        'version': 'V1',
        'timestamp': int(time.time() * 1000)
    }
    payload = {'message': json.dumps(request_json).encode('UTF-8')}
    files = [('file', open(file_path, 'rb'))]
    headers = {'X-OCR-SECRET': NAVER_CLOVA_OCR_API_KEY}
    
    try:
        response = requests.post(NAVER_CLOUD_CLOVA_OCR_API_URL, headers=headers, data=payload, files=files)
        full_text = ""
        for field in response.json()['images'][0].get('fields', []):
            full_text += field['inferText'] + " "
        return full_text.strip()
    except Exception as e:
        logger.error(f"Clova OCR 실패: {e}")
        return ""

def convert_hwp_to_pdf(hwp_path):
    """HWP를 PDF로 변환"""
    output_dir = os.path.dirname(hwp_path)
    try:
        result = subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            hwp_path,
            "--outdir", output_dir
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        
        basename = os.path.splitext(os.path.basename(hwp_path))[0] + ".pdf"
        converted_pdf = os.path.join(output_dir, basename)
        
        if os.path.exists(converted_pdf):
            return converted_pdf
        else:
            return ""
    except Exception as e:
        logger.error(f"HWP 변환 실패: {e}")
        return ""

def download_file_from_url(url):
    """URL에서 파일 다운로드"""
    try:
        import tempfile
        import requests
        
        # S3 URL인 경우 boto3 사용
        if 's3.ap-northeast-2.amazonaws.com' in url:
            return download_file_from_s3(url)
        
        # 일반 URL인 경우 requests 사용
        temp_dir = tempfile.gettempdir()
        file_name = url.split('/')[-1].split('?')[0]  # 쿼리 파라미터 제거
        temp_path = os.path.join(temp_dir, file_name)
        
        # 파일 다운로드
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_path
    except Exception as e:
        logger.error(f"파일 다운로드 실패: {e}")
        return None

def download_file_from_s3(url):
    """S3에서 직접 파일 다운로드"""
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_S3_ACCESS_KEY,
            aws_secret_access_key=AWS_S3_SECRET_KEY,
            region_name=AWS_S3_REGION
        )
        
        # URL에서 S3 키 추출
        bucket_name = AWS_S3_BUCKET_NAME
        
        # URL에서 파일 경로 추출
        if '/media/' in url:
            s3_key = 'media/' + url.split('/media/')[-1].split('?')[0]
        elif '/note_files/' in url:
            s3_key = 'note_files/' + url.split('/note_files/')[-1].split('?')[0]
        else:
            # 다른 경로인 경우 전체 경로에서 추출
            s3_key = url.split(f'{bucket_name}/')[-1].split('?')[0]
        
        # 임시 파일 생성
        temp_dir = tempfile.gettempdir()
        file_name = s3_key.split('/')[-1]
        temp_path = os.path.join(temp_dir, file_name)
        
        # S3에서 파일 다운로드
        s3_client.download_file(bucket_name, s3_key, temp_path)
        
        return temp_path
    except Exception as e:
        logger.error(f"S3 파일 다운로드 실패: {e}")
        return None

def download_file_from_s3_key(s3_key):
    """S3 키를 사용하여 파일 다운로드"""
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_S3_ACCESS_KEY,
            aws_secret_access_key=AWS_S3_SECRET_KEY,
            region_name=AWS_S3_REGION
        )
        
        # 임시 파일 생성
        temp_dir = tempfile.gettempdir()
        file_name = s3_key.split('/')[-1]
        temp_path = os.path.join(temp_dir, file_name)
        
        # S3에서 파일 다운로드
        s3_client.download_file(AWS_S3_BUCKET_NAME, s3_key, temp_path)
        
        return temp_path
    except Exception as e:
        logger.error(f"S3 키를 사용한 파일 다운로드 실패: {e}")
        return None