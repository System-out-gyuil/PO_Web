from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, Row, AttributeValue
import json
from docx import Document
from docx.table import _Cell
from docx.text.paragraph import Paragraph
import re
from typing import Dict, List, Tuple
import requests
from config import OPEN_AI_API_KEY

@csrf_exempt
@require_http_methods(["GET", "POST"])
def auto_docx(request):
    print("=== auto_docx 함수 호출됨 ===")
    
    try:
        # 세션에서 사용자 ID 가져오기
        user_id = request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': '로그인이 필요합니다.'
            })
        
        # 사용자 정보 조회
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '사용자를 찾을 수 없습니다.'
            })
        
        print(f"사용자: {user.name} (ID: {user_id})")
        
        if request.method == "POST":
            # POST 요청: 특정 행의 DOCX 생성
            try:
                data = json.loads(request.body)
                row_id = data.get('row_id')
                
                if not row_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'row_id가 필요합니다.'
                    })
                
                print(f"요청된 row_id: {row_id}")
                
                # 특정 행 조회
                try:
                    row = Row.objects.filter(id=row_id, user=user).select_related('user').prefetch_related(
                        'values__attribute__attributeType',
                        'values__attribute__dropdown_attributes'
                    ).first()
                    
                    if not row:
                        return JsonResponse({
                            'success': False,
                            'error': '해당 행을 찾을 수 없습니다.'
                        })
                    
                    print(f"행 데이터 조회 성공: {row.id}")
                    
                    # 행의 모든 속성값들을 딕셔너리로 변환
                    row_data = {}
                    for attr_value in row.values.all():
                        if attr_value.attribute:
                            attr_name = attr_value.attribute.name
                            attr_value_text = attr_value.value
                            row_data[attr_name] = attr_value_text
                    
                    print(f"행 데이터: {row_data}")

                    # OpenAI API를 통해 사업계획서 데이터 생성
                    business_plan_data = generate_business_plan_with_openai(row_data)
                    
                    if not business_plan_data:
                        return JsonResponse({
                            'success': False,
                            'error': '사업계획서 데이터 생성에 실패했습니다.'
                        })
                    
                    print(f"OpenAI 응답 데이터: {business_plan_data}")

                    # DOCX 파일 생성
                    doc = Document("diary/사업계획서_양식.docx")
                    
                    # 사업계획서 데이터로 DOCX 채우기
                    try:
                        fill_business_plan_docx(doc, business_plan_data)
                        print("DOCX 채우기 완료")
                    except Exception as e:
                        print(f"DOCX 채우기 중 오류: {e}")
                        # 오류가 발생해도 기본 정보는 채워보기
                        try:
                            # 기본 정보만 채우기
                            basic_map = {
                                "주 서비스·생산품목": business_plan_data.get("주 서비스·생산품목", "정보 부족"),
                                "매출액": f'{business_plan_data.get("매출액(백만원)", 0)} 백만원',
                                "주 사용 플랫폼": business_plan_data.get("주 사용 플랫폼", "정보 부족"),
                            }
                            find_and_fill_simple_labels(doc, basic_map)
                            print("기본 정보 채우기 완료")
                        except Exception as basic_error:
                            print(f"기본 정보 채우기도 실패: {basic_error}")
                    
                    # 파일명 생성 (한글 안전 처리)
                    company_name = get_company_name_from_row(row)
                    
                    # 파일명에서 특수문자 제거 및 안전한 파일명 생성
                    safe_company_name = re.sub(r'[<>:"/\\|?*]', '_', str(company_name))
                    safe_company_name = safe_company_name.strip()
                    
                    if not safe_company_name:
                        safe_company_name = f"회사_{row.id}"
                    
                    output_filename = f"사업계획서_{safe_company_name}.docx"
                    
                    # 파일명이 너무 길면 자르기
                    if len(output_filename) > 100:
                        output_filename = f"사업계획서_{safe_company_name[:50]}.docx"
                    
                    print(f"생성될 파일명: {output_filename}")
                    
                    # 임시 파일로 저장 (다운로드용)
                    import tempfile
                    import os
                    
                    temp_dir = tempfile.gettempdir()
                    temp_file_path = os.path.join(temp_dir, output_filename)
                    doc.save(temp_file_path)
                    
                    # 파일을 읽어서 HTTP 응답으로 전송
                    from django.http import FileResponse
                    import mimetypes
                     
                    try:
                        # 파일이 실제로 존재하는지 확인
                        if not os.path.exists(temp_file_path):
                            return JsonResponse({
                                'success': False,
                                'error': '생성된 파일을 찾을 수 없습니다.'
                            })
                        
                        # 파일 크기 확인
                        file_size = os.path.getsize(temp_file_path)
                        if file_size == 0:
                            return JsonResponse({
                                'success': False,
                                'error': '생성된 파일이 비어있습니다.'
                            })
                        
                        print(f"파일 다운로드 준비: {output_filename} (크기: {file_size} bytes)")
                        
                        # MIME 타입 설정
                        mime_type, _ = mimetypes.guess_type(output_filename)
                        if mime_type is None:
                            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        
                        # 파일 응답 생성 (더 안전한 방식)
                        try:
                            # 파일을 바이너리로 읽어서 메모리에 저장
                            with open(temp_file_path, 'rb') as file_handle:
                                file_content = file_handle.read()
                            
                            # BytesIO를 사용하여 메모리에서 파일 응답 생성
                            from io import BytesIO
                            file_stream = BytesIO(file_content)
                            file_stream.seek(0)  # 스트림 포인터를 처음으로
                            
                            response = FileResponse(
                                file_stream,
                                content_type=mime_type
                            )
                            
                            # 다운로드 강제 설정
                            response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{output_filename}'
                            response['Content-Length'] = file_size
                            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                            response['Pragma'] = 'no-cache'
                            response['Expires'] = '0'
                            
                            print(f"파일 응답 생성 완료: {output_filename}")
                            print(f"=== 다운로드 준비 완료 ===")
                            print(f"파일명: {output_filename}")
                            print(f"파일 크기: {file_size} bytes")
                            print(f"MIME 타입: {mime_type}")
                            print(f"임시 경로: {temp_file_path}")
                            print(f"사용자에게 다운로드 시작...")
                            
                            # 임시 파일 정리 (응답 후)
                            def cleanup_temp_file():
                                try:
                                    if os.path.exists(temp_file_path):
                                        os.remove(temp_file_path)
                                        print(f"임시 파일 정리 완료: {temp_file_path}")
                                except Exception as cleanup_error:
                                    print(f"임시 파일 정리 실패: {cleanup_error}")
                            
                            # 응답 객체에 정리 함수 추가
                            response._cleanup = cleanup_temp_file
                            
                            return response
                                
                        except Exception as file_error:
                            print(f"파일 응답 생성 중 오류: {file_error}")
                            # 임시 파일 정리
                            try:
                                if os.path.exists(temp_file_path):
                                    os.remove(temp_file_path)
                            except:
                                pass
                            
                            return JsonResponse({
                                'success': False,
                                'error': f'파일 다운로드 준비 중 오류가 발생했습니다: {str(file_error)}'
                            })
                            
                    except Exception as download_error:
                        print(f"다운로드 준비 중 오류: {download_error}")
                        # 임시 파일 정리
                        try:
                            if os.path.exists(temp_file_path):
                                os.remove(temp_file_path)
                        except:
                            pass
                        
                        return JsonResponse({
                            'success': False,
                            'error': f'다운로드 준비 중 오류가 발생했습니다: {str(download_error)}'
                        })
                    
                except Row.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': '해당 행을 찾을 수 없습니다.'
                    })
                    
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': '잘못된 JSON 형식입니다.'
                })
                
        else:
            # GET 요청: 사용자의 모든 행 데이터 조회 (기존 기능 유지)
            rows = Row.objects.filter(user=user).select_related('user').prefetch_related(
                'values__attribute__attributeType',
                'values__attribute__dropdown_attributes'
            )
            
            print(f"총 {rows.count()}개의 행을 찾았습니다.")
            
            rows_data = []
            for row in rows[:10]:
                row_info = {
                    'id': row.id,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'attributes': {}
                }
                
                for attr_value in row.values.all():
                    if attr_value.attribute:
                        attr_name = attr_value.attribute.name
                        attr_value_text = attr_value.value
                        row_info['attributes'][attr_name] = attr_value_text
                
                rows_data.append(row_info)
            
            return JsonResponse({
                'success': True,
                'user_name': user.name,
                'total_rows': rows.count(),
                'rows_data': rows_data,
                'message': '사용자 데이터를 성공적으로 조회했습니다.'
            })
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def get_company_name_from_row(row):
    """행에서 회사명을 추출하는 헬퍼 함수"""
    try:
        company_attr = row.values.filter(attribute__name='회사명').first()
        if company_attr and company_attr.value:
            return company_attr.value
        return f"회사_{row.id}"
    except:
        return f"회사_{row.id}"

# ==========================
# OpenAI API 연동 함수들
# ==========================
def generate_business_plan_with_openai(row_data):
    """OpenAI API를 통해 사업계획서 데이터 생성"""
    try:
        if not OPEN_AI_API_KEY:
            print("OpenAI API 키가 설정되지 않았습니다.")
            return None
        
        # 기업 정보를 OpenAI에 전달할 프롬프트 구성
        company_info = format_company_info_for_openai(row_data)
        
        system_prompt = """당신은 사업계획서 작성 전문가입니다. 
        제공된 기업 정보를 바탕으로 신용취약 소상공인 자금 사업계획서에 필요한 모든 정보를 생성해주세요.
        
        **중요한 지침:**
        1. 제공된 기업 정보만을 기반으로 답변하세요.
        2. 정보가 부족한 경우 "정보 부족"이라고 명시하세요.
        3. 추측하지 말고 확실한 정보만 사용하세요.
        4. 모든 값은 현실적이고 구체적으로 작성해주세요.
        
        다음 JSON 형식으로 응답해주세요:
        {
            "주 서비스·생산품목": "기업의 주요 서비스나 생산품목 (정보 부족시 '정보 부족')",
            "매출액(백만원)": 숫자값 (정보 부족시 0),
            "주 사용 플랫폼": "주로 사용하는 플랫폼이나 채널 (정보 부족시 '정보 부족')",
            "점포 보유현황": "유" 또는 "무" (정보 부족시 '정보 부족'),
            "대표자_경력": [
                ["기간", "근무처", "담당업무", "최종직위"]
            ],
            "실제경영자_관계": "대표자와의 관계 (정보 부족시 '본인')",
            "실제경영자_경력": [
                ["기간", "근무처", "담당업무", "최종직위"]
            ],
            "사업개요": "사업의 주요 내용과 특징 (정보 부족시 '정보 부족')",
            "향후 사업계획(자금용도 포함)": "자금을 어떻게 사용할지 포함한 향후 계획 (정보 부족시 '정보 부족')",
            "자금소요_운전자금": 숫자값 (정보 부족시 30),
            "자금조달_본건차입금": 숫자값 (정보 부족시 20),
            "자금조달_자체자금": 숫자값 (정보 부족시 10),
            "자금조달_기타": 숫자값 (정보 부족시 0)
        }
        
        **경력 데이터 처리:**
        - 경력 정보가 없으면 빈 배열 [] 반환
        - 경력 정보가 있으면 ["기간", "근무처", "담당업무", "최종직위"] 형식으로 반환
        - 각 항목이 부족하면 빈 문자열 "" 사용"""
        
        user_message = f"다음 기업 정보를 바탕으로 사업계획서 데이터를 생성해주세요:\n\n{company_info}"
        
        # OpenAI API 호출
        headers = {
            'Authorization': f'Bearer {OPEN_AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 2000,
            'temperature': 0.3
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
            
            # JSON 응답 파싱
            try:
                # JSON 블록 추출 (```json ... ``` 형태일 수 있음)
                if '```json' in ai_response:
                    json_start = ai_response.find('```json') + 7
                    json_end = ai_response.find('```', json_start)
                    if json_end != -1:
                        json_str = ai_response[json_start:json_end].strip()
                    else:
                        json_str = ai_response[json_start:].strip()
                else:
                    json_str = ai_response
                
                business_plan_data = json.loads(json_str)
                print(f"OpenAI 응답 파싱 성공: {business_plan_data}")
                return business_plan_data
                
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 실패: {e}")
                print(f"AI 응답: {ai_response}")
                return None
        else:
            print(f"OpenAI API 호출 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"OpenAI API 연동 중 오류: {e}")
        return None

def format_company_info_for_openai(row_data):
    """기업 정보를 OpenAI에 전달하기 위한 형식으로 변환"""
    formatted_info = []
    
    for key, value in row_data.items():
        if value and str(value).strip():
            formatted_info.append(f"{key}: {value}")
    
    return "\n".join(formatted_info)

# ==========================
# DOCX 조작 유틸리티 함수들
# ==========================
def cell_right(table, r, c):
    """테이블에서 오른쪽 셀 반환"""
    try:
        if table is None or r < 0 or c < 0:
            return None
        
        # 행 범위 체크
        if r >= len(table.rows):
            return None
        
        row = table.rows[r]
        # 열 범위 체크
        if c + 1 >= len(row.cells):
            return None
        
        return row.cells[c + 1]
    except Exception as e:
        print(f"cell_right 오류 (r={r}, c={c}): {e}")
        return None

def cell_below(table, r, c):
    """테이블에서 아래쪽 셀 반환"""
    try:
        if table is None or r < 0 or c < 0:
            return None
        
        # 행 범위 체크
        if r + 1 >= len(table.rows):
            return None
        
        row = table.rows[r + 1]
        # 열 범위 체크
        if c >= len(row.cells):
            return None
        
        return row.cells[c]
    except Exception as e:
        print(f"cell_below 오류 (r={r}, c={c}): {e}")
        return None

def set_cell_text(cell, value):
    """셀에 텍스트 설정"""
    try:
        if cell is None:
            print("셀이 None입니다.")
            return
        
        # 기존 문단 제거하고 한 문단으로 교체
        try:
            for p in cell.paragraphs:
                if p:
                    p.clear()
        except Exception as clear_error:
            print(f"문단 정리 중 오류: {clear_error}")
        
        # 새 텍스트 설정
        try:
            cell.text = str(value)
        except Exception as text_error:
            print(f"텍스트 설정 중 오류: {text_error}")
            # 대안: 첫 번째 문단에 텍스트 추가
            try:
                if cell.paragraphs and len(cell.paragraphs) > 0:
                    cell.paragraphs[0].text = str(value)
                else:
                    # 문단이 없으면 새로 생성
                    cell.add_paragraph(str(value))
            except Exception as alt_error:
                print(f"대안 텍스트 설정도 실패: {alt_error}")
                
    except Exception as e:
        print(f"set_cell_text 전체 오류: {e}")
        # 최후의 수단: 아무것도 하지 않음
        pass

def norm(s):
    """텍스트 정규화"""
    if not s:
        return ""
    return re.sub(r"\s+", "", str(s)).strip()

def is_match(label, cell_text, aliases=None):
    """라벨 매칭 확인"""
    if aliases is None:
        aliases = []
    t = norm(cell_text)
    if norm(label) in t:
        return True
    return any(norm(a) in t for a in aliases)

# 라벨 별 동의어
ALIASES = {
    "주 서비스·생산품목": ["주서비스·생산품목", "주서비스/생산품목", "주서비스", "생산품목"],
    "매출액": ["매출액(백만원)", "매출액백만원"],
    "주 사용 플랫폼": ["주사용플랫폼", "사용플랫폼"],
    "점포 보유현황": ["점포보유현황", "점포보유"],
    "사업개요": ["주서비스·생산품목의용도및특성", "서비스및상품의주요내용"],
    "향후 사업계획": ["자금용도및사업계획", "향후사업계획", "자금용도"],
    "자금소요": ["자금소요내역", "자금소요(백만원)"],
    "자금조달": ["자금조달계획", "자금조달(백만원)"],
    "경력": ["경력", "대표자경력", "실제경영자경력"],
}

def find_and_fill_simple_labels(doc, fill_map):
    """표/문단에서 라벨을 찾아 값을 채우는 함수"""
    try:
        # 1) 표 내부
        for table in doc.tables:
            try:
                rows = len(table.rows)
                for r in range(rows):
                    try:
                        row = table.rows[r]
                        for c in range(len(row.cells)):
                            try:
                                cell = row.cells[c]
                                txt = cell.text if cell.text else ""
                                if not txt.strip():
                                    continue
                                
                                for label, value in fill_map.items():
                                    if is_match(label, txt, ALIASES.get(label, [])):
                                        try:
                                            # 우선 오른쪽 셀에 써보고, 없으면 아래 셀 시도
                                            target = cell_right(table, r, c) or cell_below(table, r, c)
                                            if target:
                                                set_cell_text(target, value)
                                            else:
                                                # 같은 셀 자체를 치환해야 하는 경우
                                                set_cell_text(cell, value)
                                        except Exception as cell_error:
                                            print(f"셀 채우기 중 오류: {cell_error}")
                                            continue
                            except Exception as col_error:
                                print(f"열 {c} 처리 중 오류: {col_error}")
                                continue
                    except Exception as row_error:
                        print(f"행 {r} 처리 중 오류: {row_error}")
                        continue
            except Exception as table_error:
                print(f"테이블 처리 중 오류: {table_error}")
                continue

        # 2) 문단
        try:
            paragraphs = doc.paragraphs
            for i, p in enumerate(paragraphs):
                try:
                    for label, value in fill_map.items():
                        if is_match(label, p.text, ALIASES.get(label, [])):
                            try:
                                # 다음 문단이 비어있으면 거기에, 아니면 라벨 문단 바로 뒤에 새 문단 삽입
                                target_index = i+1 if i+1 < len(paragraphs) else i
                                if target_index < len(paragraphs) and not paragraphs[target_index].text.strip():
                                    paragraphs[target_index].text = str(value)
                                else:
                                    p.insert_paragraph_before(str(value))
                            except Exception as para_error:
                                print(f"문단 채우기 중 오류: {para_error}")
                                continue
                except Exception as para_iter_error:
                    print(f"문단 {i} 처리 중 오류: {para_iter_error}")
                    continue
        except Exception as para_section_error:
            print(f"문단 섹션 처리 중 오류: {para_section_error}")
            
    except Exception as e:
        print(f"find_and_fill_simple_labels 전체 오류: {e}")
        raise

def fill_shop_checkbox_format(text, has_shop):
    """점포 보유현황 체크박스 형식 처리"""
    has = norm(has_shop) in ["유", "있음", "예", "true"]
    # 원문이 '☑ 유 □ 무'나 '□ 유 □ 무' 등일 수 있어 모두 정규화 처리
    base = re.sub(r"[☑■□]\s*유", "□ 유", text)
    base = re.sub(r"[☑■□]\s*무", "□ 무", base)
    if has:
        base = base.replace("□ 유", "☑ 유")
    else:
        base = base.replace("□ 무", "☑ 무")
    return base

def apply_shop_checkbox(doc, has_shop):
    """점포 보유현황 체크박스 적용"""
    try:
        for table in doc.tables:
            try:
                for row in table.rows:
                    try:
                        for cell in row.cells:
                            try:
                                if cell and cell.text:
                                    t = cell.text
                                    if is_match("점포 보유현황", t, ALIASES["점포 보유현황"]) and ("유" in t and "무" in t):
                                        formatted_text = fill_shop_checkbox_format(t, has_shop)
                                        set_cell_text(cell, formatted_text)
                                        print(f"점포 보유현황 체크박스 적용: {has_shop}")
                                        return  # 첫 번째 매칭되는 셀만 처리
                            except Exception as cell_error:
                                print(f"점포 보유현황 셀 처리 중 오류: {cell_error}")
                                continue
                    except Exception as row_error:
                        print(f"점포 보유현황 행 처리 중 오류: {row_error}")
                        continue
            except Exception as table_error:
                print(f"점포 보유현황 테이블 처리 중 오류: {table_error}")
                continue
    except Exception as e:
        print(f"apply_shop_checkbox 전체 오류: {e}")
        # 오류가 발생해도 계속 진행
        pass

def fill_career_table(doc, label_text, careers):
    """경력 표 채우기"""
    try:
        for table in doc.tables:
            try:
                # 테이블 텍스트 수집 (안전하게)
                table_text_parts = []
                for row in table.rows:
                    for cell in row.cells:
                        if cell and cell.text:
                            table_text_parts.append(cell.text)
                
                table_text = "\n".join(table_text_parts)
                
                if is_match(label_text, table_text, ALIASES["경력"]) and \
                   ("구 분" in table_text or "구분" in table_text) and "근무처" in table_text:
                    
                    print(f"경력 표 발견: {label_text}")
                    
                    # 헤더 다음 행부터 입력
                    needed_rows = len(careers) if careers else 0
                    header_row_idx = 0
                    start_row_idx = header_row_idx + 1
                    
                    # 필요한 행 수만큼 추가
                    while len(table.rows) < start_row_idx + needed_rows:
                        try:
                            table.add_row()
                        except Exception as add_row_error:
                            print(f"행 추가 중 오류: {add_row_error}")
                            break

                    # 각 행 채우기 (안전한 인덱스 접근)
                    for i, career in enumerate(careers):
                        try:
                            r = start_row_idx + i
                            
                            # 행 범위 체크
                            if r >= len(table.rows):
                                print(f"행 {r}가 테이블 범위를 벗어남")
                                break
                            
                            # career가 리스트인지 확인하고 안전하게 접근
                            if isinstance(career, list) and len(career) >= 4:
                                period = career[0] if career[0] else ""
                                company = career[1] if career[1] else ""
                                duty = career[2] if career[2] else ""
                                title = career[3] if career[3] else ""
                            else:
                                # career가 리스트가 아니거나 길이가 부족한 경우
                                period = str(career) if career else ""
                                company = ""
                                duty = ""
                                title = ""
                            
                            # 안전한 셀 접근
                            row = table.rows[r]
                            if len(row.cells) > 1:
                                set_cell_text(row.cells[1], period)
                            if len(row.cells) > 2:
                                set_cell_text(row.cells[2], company)
                            if len(row.cells) > 3:
                                set_cell_text(row.cells[3], duty)
                            if len(row.cells) > 4:
                                set_cell_text(row.cells[4], title)
                                
                        except Exception as e:
                            print(f"경력 표 채우기 중 오류 (행 {i}): {e}")
                            continue
                    
                    print(f"경력 표 채우기 완료: {label_text}")
                    return  # 첫 번째 매칭되는 테이블만 처리
                    
            except Exception as table_error:
                print(f"테이블 처리 중 오류: {table_error}")
                continue
                
    except Exception as e:
        print(f"fill_career_table 전체 오류: {e}")
        raise

def fill_money_tables(doc, data):
    """자금소요/자금조달 표 채우기"""
    try:
        need = data.get("자금소요_운전자금", 0)
        need_total = data.get("자금소요_합계", need)

        loan = data.get("자금조달_본건차입금", 0)
        self_ = data.get("자금조달_자체자금", 0)
        other = data.get("자금조달_기타", 0)
        fund_total = data.get("자금조달_합계", loan + self_ + other)

        def fmt(v):
            try:
                return str(int(v))
            except:
                return str(v)

        for table in doc.tables:
            try:
                # 테이블 텍스트 수집 (안전하게)
                table_text_parts = []
                for row in table.rows:
                    for cell in row.cells:
                        if cell and cell.text:
                            table_text_parts.append(cell.text)
                
                table_text = "\n".join(table_text_parts)

                # 자금소요 표
                if any(k in table_text for k in ["자금소요", "자금소요내역"]):
                    print("자금소요 표 발견")
                    for r, row in enumerate(table.rows):
                        try:
                            row_text_parts = []
                            for c in row.cells:
                                if c and c.text:
                                    row_text_parts.append(c.text)
                            
                            row_text = " ".join(row_text_parts)
                            
                            if "운전" in row_text and len(row.cells) > 0:
                                set_cell_text(row.cells[-1], fmt(need))
                            if "합계" in row_text and len(row.cells) > 0:
                                set_cell_text(row.cells[-1], fmt(need_total))
                        except Exception as row_error:
                            print(f"자금소요 행 {r} 처리 중 오류: {row_error}")
                            continue

                # 자금조달 표
                if any(k in table_text for k in ["자금조달", "자금조달계획"]):
                    print("자금조달 표 발견")
                    for r, row in enumerate(table.rows):
                        try:
                            row_text_parts = []
                            for c in row.cells:
                                if c and c.text:
                                    row_text_parts.append(c.text)
                            
                            row_text = " ".join(row_text_parts)
                            
                            if "본건" in row_text and len(row.cells) > 0:
                                set_cell_text(row.cells[-1], fmt(loan))
                            if "자체" in row_text and len(row.cells) > 0:
                                set_cell_text(row.cells[-1], fmt(self_))
                            if "기타" in row_text or "은행차입금등 기타" in row_text:
                                if len(row.cells) > 0:
                                    set_cell_text(row.cells[-1], fmt(other))
                            if "합 계" in row_text or "합계" in row_text:
                                if len(row.cells) > 0:
                                    set_cell_text(row.cells[-1], fmt(fund_total))
                        except Exception as row_error:
                            print(f"자금조달 행 {r} 처리 중 오류: {row_error}")
                            continue
                            
            except Exception as table_error:
                print(f"자금 표 처리 중 오류: {table_error}")
                continue
                
    except Exception as e:
        print(f"fill_money_tables 전체 오류: {e}")
        raise

def fill_business_plan_docx(doc, business_plan_data):
    """사업계획서 DOCX 파일 채우기 메인 함수"""
    try:
        # 1) 간단 라벨-값 매핑
        simple_map = {
            "주 서비스·생산품목": business_plan_data.get("주 서비스·생산품목", "정보 부족"),
            "매출액": f'{business_plan_data.get("매출액(백만원)", 0)} 백만원',
            "주 사용 플랫폼": business_plan_data.get("주 사용 플랫폼", "정보 부족"),
            "사업개요": business_plan_data.get("사업개요", "정보 부족"),
            "향후 사업계획": business_plan_data.get("향후 사업계획(자금용도 포함)", "정보 부족"),
        }
        find_and_fill_simple_labels(doc, simple_map)
        print("1) 라벨-값 매핑 완료")

        # 2) 점포 보유현황 체크박스 처리
        try:
            apply_shop_checkbox(doc, business_plan_data.get("점포 보유현황", "정보 부족"))
            print("2) 점포 보유현황 체크박스 처리 완료")
        except Exception as e:
            print(f"점포 보유현황 처리 중 오류: {e}")

        # 3) 경력 표 채우기
        try:
            fill_career_table(doc, "대표자", business_plan_data.get("대표자_경력", []))
            print("3-1) 대표자 경력 표 채우기 완료")
        except Exception as e:
            print(f"대표자 경력 표 채우기 중 오류: {e}")
        
        try:
            find_and_fill_simple_labels(doc, {"실제경영자": f"(대표자와의 관계 : {business_plan_data.get('실제경영자_관계','본인')})"})
            print("3-2) 실제경영자 관계 처리 완료")
        except Exception as e:
            print(f"실제경영자 관계 처리 중 오류: {e}")
        
        try:
            fill_career_table(doc, "실제경영자", business_plan_data.get("실제경영자_경력", []))
            print("3-3) 실제경영자 경력 표 채우기 완료")
        except Exception as e:
            print(f"실제경영자 경력 표 채우기 중 오류: {e}")

        # 4) 자금 소요/조달 표 채우기
        try:
            fill_money_tables(doc, business_plan_data)
            print("4) 자금 소요/조달 표 채우기 완료")
        except Exception as e:
            print(f"자금 소요/조달 표 채우기 중 오류: {e}")
        
        print("사업계획서 DOCX 채우기 완료")
        
    except Exception as e:
        print(f"사업계획서 DOCX 채우기 중 전체 오류: {e}")
        raise