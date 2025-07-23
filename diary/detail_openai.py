import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import logging
import os
import tempfile
from datetime import datetime
from config import OPEN_AI_API_KEY, AWS_S3_ACCESS_KEY, AWS_S3_SECRET_KEY, AWS_S3_BUCKET_NAME, AWS_S3_REGION
from .models import Row, AttributeValue, Attribute, DropdownAttribute
import pdfplumber
import uuid
import time
import subprocess
from PIL import Image
import warnings
import boto3
from botocore.exceptions import ClientError
import hashlib
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
        changes = data.get('changes', {})  # 변경사항 정보
        
        if not message:
            return JsonResponse({'success': False, 'error': '메시지가 비어있습니다'})
        
        # OpenAI API 키 확인
        if not OPEN_AI_API_KEY:
            return JsonResponse({'success': False, 'error': 'OpenAI API 키가 설정되지 않았습니다'})
        
        # 행 데이터 가져오기 (캐싱 활용)
        row_data = {}
        file_texts = []
        cache_updated = False
        
        if row_id:
            # 세션에서 캐시된 데이터 확인
            cache_key = f'ai_chat_row_{row_id}'
            cached_data = request.session.get(cache_key)
            
            # 현재 시간 정의 (캐시 만료 체크용)
            current_time = time.time()
            
            # 변경사항이 있는지 확인
            has_changes = changes.get('cacheInvalidated', False) or \
                         changes.get('fileChanges', {}).get('added', []) or \
                         changes.get('fileChanges', {}).get('modified', []) or \
                         changes.get('fileChanges', {}).get('deleted', [])
            
            print(f"변경사항 감지 결과:")
            print(f"  cacheInvalidated: {changes.get('cacheInvalidated', False)}")
            print(f"  added files: {len(changes.get('fileChanges', {}).get('added', []))}")
            print(f"  modified files: {len(changes.get('fileChanges', {}).get('modified', []))}")
            print(f"  deleted files: {len(changes.get('fileChanges', {}).get('deleted', []))}")
            print(f"  has_changes: {has_changes}")
            
            # 삭제된 파일 상세 정보 로깅
            deleted_files = changes.get('fileChanges', {}).get('deleted', [])
            if deleted_files:
                print(f"삭제된 파일 상세 정보:")
                for i, deleted_file in enumerate(deleted_files):
                    print(f"  삭제된 파일 {i + 1}: {deleted_file}")
            
            # 변경사항이 있거나 강제 새로고침이면 캐시 무시
            if force_refresh:
                print(f"강제 새로고침으로 인한 새로운 데이터 처리: 행 {row_id}")
                cache_updated = True
                cached_data = None  # 캐시 무시
            elif has_changes and cached_data:
                # 캐시가 있고 변경사항이 있는 경우 - 부분 업데이트만 수행
                print(f"캐시 기반 부분 업데이트: 행 {row_id}")
                cache_updated = True
                # cached_data는 유지 (None으로 설정하지 않음)
            elif has_changes and not cached_data:
                # 캐시가 없고 변경사항이 있는 경우 - 새로운 데이터 처리
                print(f"캐시 없음 + 변경사항으로 인한 새로운 데이터 처리: 행 {row_id}")
                cache_updated = True
                cached_data = None
            elif cached_data:
                # 캐시 만료 시간 체크 (30분)
                cache_timestamp = cached_data.get('timestamp', 0)
                cache_age = current_time - cache_timestamp
                
                if cache_age < 1800:  # 30분 (1800초)
                    # 캐시된 데이터 사용
                    row_data = cached_data.get('row_data', {})
                    file_texts = cached_data.get('file_texts', [])
                    print(f"캐시된 데이터 사용: 행 {row_id}")
                    
                    # text 타입 파일들은 항상 최신 데이터로 업데이트
                    try:
                        row = Row.objects.get(id=row_id)
                        text_file_attribute_values = AttributeValue.objects.filter(row=row, attribute__attributeType__name='file')
                        
                        for attr_value in text_file_attribute_values:
                            attr_name = attr_value.attribute.name
                            
                            if attr_value.value:
                                try:
                                    file_data = json.loads(attr_value.value) if isinstance(attr_value.value, str) else attr_value.value
                                    print(f'캐시 사용 중 text 타입 확인 - file_data: {file_data}')
                                    
                                    # 음성파일 속성인 경우 (data 구조)
                                    if isinstance(file_data, dict) and 'data' in file_data:
                                        for file_id, file_info in file_data['data'].items():
                                            if file_info.get('type') == 'text':
                                                # text 타입은 항상 새로 처리
                                                print(f'캐시 사용 중 text 타입 새로 처리: {attr_name}')
                                                text_content = file_info.get('text', '')
                                                if text_content:
                                                    # 기존 text 타입 파일 제거
                                                    file_texts = [text for text in file_texts if not text.startswith(f"[{attr_name} - 텍스트]:")]
                                                    # 새 text 내용 추가
                                                    file_texts.append(f"[{attr_name} - 텍스트]:\n{text_content}")
                                                    print(f'text 타입 파일 업데이트 완료: {attr_name}')
                                    
                                    # 일반 파일 속성인 경우 (배열 구조) - text 타입 처리
                                    elif isinstance(file_data, list):
                                        for file_info in file_data:
                                            if file_info.get('type') == 'text':
                                                print(f'캐시 사용 중 text 타입 새로 처리: {attr_name}')
                                                text_content = file_info.get('text', '')
                                                if text_content:
                                                    # 기존 text 타입 파일 제거
                                                    file_texts = [text for text in file_texts if not text.startswith(f"[{attr_name} - 텍스트]:")]
                                                    # 새 text 내용 추가
                                                    file_texts.append(f"[{attr_name} - 텍스트]:\n{text_content}")
                                                    print(f'text 타입 파일 업데이트 완료: {attr_name}')
                                except Exception as e:
                                    logger.error(f"캐시 사용 중 text 타입 파일 처리 실패: {e}")
                    except Exception as e:
                        logger.error(f"캐시 사용 중 text 타입 파일 새로 처리 중 오류: {e}")
                    
                    # 업데이트된 file_texts로 캐시 갱신
                    cache_data = {
                        'row_data': row_data,
                        'file_texts': file_texts,
                        'timestamp': current_time
                    }
                    request.session[cache_key] = cache_data
                    request.session.modified = True
                    cache_updated = True
                    print(f"text 타입 파일 업데이트로 인한 캐시 갱신 완료")
                else:
                    # 캐시 만료 - 새로운 데이터 처리
                    print(f"캐시 만료 - 새로운 데이터 처리: 행 {row_id}")
                    cache_updated = True
                    cached_data = None  # 캐시 무시
            else:
                # 캐시가 없음 - 새로운 데이터 처리
                print(f"캐시 없음 - 새로운 데이터 처리: 행 {row_id}")
                cache_updated = True
            
            # 새로운 데이터 처리 (캐시가 없거나 무효화된 경우)
            if not cached_data:
                try:
                    row = Row.objects.get(id=row_id)
                    user = row.user
                    
                    # 해당 행의 모든 속성값 가져오기 (파일 제외)
                    attribute_values = AttributeValue.objects.filter(row=row)
                    
                    for attr_value in attribute_values:
                        attr_name = attr_value.attribute.name
                        attr_type = attr_value.attribute.attributeType.name
                        
                        # 파일 타입은 건너뛰고 나머지 데이터만 처리
                        if attr_type != 'file':
                            if attr_type == 'outstanding_debts':
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
                                        # DropdownAttribute 테이블에서 실제 이름 조회
                                        dropdown_value = str(attr_value.value).strip()
                                        if dropdown_value:
                                            try:
                                                dropdown_attr = DropdownAttribute.objects.get(
                                                    attribute=attr_value.attribute,
                                                    value=dropdown_value
                                                )
                                                row_data[attr_name] = dropdown_attr.name
                                            except DropdownAttribute.DoesNotExist:
                                                row_data[attr_name] = dropdown_value
                                    except Exception as e:
                                        logger.error(f"드롭다운 데이터 처리 실패: {e}")
                                        row_data[attr_name] = attr_value.value
                            
                            elif attr_type == 'text':
                                # 텍스트 데이터 처리
                                if attr_value.value:
                                    row_data[attr_name] = attr_value.value
                            
                            elif attr_type == 'number':
                                # 숫자 데이터 처리
                                if attr_value.value:
                                    try:
                                        num_value = float(attr_value.value)
                                        row_data[attr_name] = f"{num_value:,}"
                                    except:
                                        row_data[attr_name] = attr_value.value
                            
                            elif attr_type == 'date':
                                # 날짜 데이터 처리
                                if attr_value.value:
                                    row_data[attr_name] = attr_value.value
                            
                            elif attr_type == 'boolean':
                                # 불린 데이터 처리
                                if attr_value.value:
                                    bool_value = attr_value.value.lower() if isinstance(attr_value.value, str) else str(attr_value.value)
                                    if bool_value in ['true', '1', 'yes', 'on']:
                                        row_data[attr_name] = "예"
                                    elif bool_value in ['false', '0', 'no', 'off']:
                                        row_data[attr_name] = "아니오"
                                    else:
                                        row_data[attr_name] = attr_value.value
                            
                            else:
                                # 기타 타입
                                if attr_value.value:
                                    row_data[attr_name] = attr_value.value
                    
                    # 파일 데이터 처리
                    file_texts = []
                    
                    # 파일 속성값들 처리
                    file_attribute_values = AttributeValue.objects.filter(row=row, attribute__attributeType__name='file')
                    
                    for attr_value in file_attribute_values:
                        attr_name = attr_value.attribute.name
                        
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
                                                    file_hash = calculate_file_hash(file_path)
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
                                            # text 타입은 항상 새로 처리 (캐시 무시)
                                            print(f'text 타입 파일 새로 처리: {file_info.get("text")}')
                                            text_content = file_info.get('text', '')
                                            if text_content:
                                                file_texts.append(f"[{attr_name} - 텍스트]:\n{text_content}")
                                                print(f'text 타입 파일 캐시에 저장: {attr_name}')
                                            
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
                                                file_hash = calculate_file_hash(file_path)
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
                                        file_hash = calculate_file_hash(file_path)
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
                    
                    # 캐시 업데이트
                    cache_data = {
                        'row_data': row_data,
                        'file_texts': file_texts,
                        'timestamp': current_time
                    }
                    request.session[cache_key] = cache_data
                    request.session.modified = True
                    
                    print(f"[AI 캐시 업데이트] row_id={row_id}")
                    print(f"  업데이트된 row_data: {json.dumps(row_data, ensure_ascii=False, indent=2)}")
                    for file_text in file_texts:
                        print(f"  업데이트된 file_text: {file_text}")
                    
                except Row.DoesNotExist:
                    return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다'})
                except Exception as e:
                    logger.error(f"행 데이터 조회 실패: {e}")
            else:
                # 캐시가 있고 변경사항이 있는 경우 - 부분 업데이트만 수행
                if has_changes:
                    print(f"캐시 기반 부분 업데이트: 행 {row_id}")
                    print(f"  캐시 데이터 존재: {cached_data is not None}")
                    print(f"  변경사항 존재: {has_changes}")
                    
                    # 기존 캐시 데이터 사용
                    row_data = cached_data.get('row_data', {})
                    file_texts = cached_data.get('file_texts', [])
                    
                    print(f"  기존 file_texts 개수: {len(file_texts)}")
                    for i, text in enumerate(file_texts):
                        print(f"    기존 file_text {i + 1}: {text[:100]}...")
                    
                    # text 타입 파일들은 항상 새로 처리 (캐시 무시)
                    try:
                        row = Row.objects.get(id=row_id)
                        text_file_attribute_values = AttributeValue.objects.filter(row=row, attribute__attributeType__name='file')
                        
                        for attr_value in text_file_attribute_values:
                            attr_name = attr_value.attribute.name
                            
                            if attr_value.value:
                                try:
                                    file_data = json.loads(attr_value.value) if isinstance(attr_value.value, str) else attr_value.value
                                    
                                    print(f'file_data: {file_data}')
                                    # 음성파일 속성인 경우 (data 구조)
                                    if isinstance(file_data, dict) and 'data' in file_data:
                                        for file_id, file_info in file_data['data'].items():
                                            if file_info.get('type') == 'text':
                                                # text 타입은 항상 새로 처리
                                                print(f'캐시 기반 부분 업데이트에서 text 타입 새로 처리: {attr_name}')
                                                text_content = file_info.get('text', '')
                                                if text_content:
                                                    # 기존 text 타입 파일 제거
                                                    file_texts = [text for text in file_texts if not text.startswith(f"[{attr_name} - 텍스트]:")]
                                                    # 새 text 내용 추가
                                                    file_texts.append(f"[{attr_name} - 텍스트]:\n{text_content}")
                                                    print(f'text 타입 파일 업데이트 완료: {attr_name}')
                                    
                                    # 일반 파일 속성인 경우 (배열 구조) - text 타입 처리
                                    elif isinstance(file_data, list):
                                        for file_info in file_data:
                                            if file_info.get('type') == 'text':
                                                print(f'캐시 기반 부분 업데이트에서 text 타입 새로 처리: {attr_name}')
                                                text_content = file_info.get('text', '')
                                                if text_content:
                                                    # 기존 text 타입 파일 제거
                                                    file_texts = [text for text in file_texts if not text.startswith(f"[{attr_name} - 텍스트]:")]
                                                    # 새 text 내용 추가
                                                    file_texts.append(f"[{attr_name} - 텍스트]:\n{text_content}")
                                                    print(f'text 타입 파일 업데이트 완료: {attr_name}')
                                except Exception as e:
                                    logger.error(f"캐시 기반 text 타입 파일 처리 실패: {e}")
                    except Exception as e:
                        logger.error(f"text 타입 파일 새로 처리 중 오류: {e}")
                    
                    # 파일 변경사항 처리
                    file_changes = changes.get('fileChanges', {})
                    
                    # 삭제된 파일 처리
                    deleted_files = file_changes.get('deleted', [])
                    for deleted_file in deleted_files:
                        field_name = deleted_file.get('fieldName')
                        file_info = deleted_file.get('fileInfo', {})
                        if field_name:
                            print(f"파일 삭제 처리 시작: {field_name}")
                            print(f"  삭제된 파일 정보: {file_info}")
                            
                            original_file_texts_count = len(file_texts)
                            
                            # 파일명이 있으면 해당 파일만 삭제
                            if file_info and file_info.get('original_filename'):
                                filename = file_info.get('original_filename')
                                file_texts = [text for text in file_texts if not text.startswith(f"[{field_name} - {filename}")]
                                print(f"  파일명 기반 삭제: {filename}")
                            # 파일 해시가 있으면 해당 파일만 삭제
                            elif file_info and file_info.get('file_hash'):
                                file_hash = file_info.get('file_hash')
                                # 해시 정보로는 직접 매칭이 어려우므로 해당 필드의 모든 파일 텍스트 제거
                                file_texts = [text for text in file_texts if not text.startswith(f"[{field_name} -")]
                                print(f"  해시 기반 삭제: {file_hash}")
                            # fileId가 있으면 해당 파일만 삭제
                            elif file_info and file_info.get('fileId'):
                                file_id = file_info.get('fileId')
                                # fileId로는 직접 매칭이 어려우므로 해당 필드의 모든 파일 텍스트 제거
                                file_texts = [text for text in file_texts if not text.startswith(f"[{field_name} -")]
                                print(f"  fileId 기반 삭제: {file_id}")
                            else:
                                # 기본적으로 해당 필드의 모든 파일 텍스트 제거
                                file_texts = [text for text in file_texts if not text.startswith(f"[{field_name} -")]
                                print(f"  필드 전체 삭제: {field_name}")
                            
                            removed_count = original_file_texts_count - len(file_texts)
                            print(f"  제거된 파일 텍스트 수: {removed_count}")
                            print(f"파일 삭제 처리 완료: {field_name}")
                    
                    # 추가된 파일들 처리
                    added_files = file_changes.get('added', [])
                    for added_file in added_files:
                        field_name = added_file.get('fieldName')
                        file_info = added_file.get('fileInfo', {})
                        if field_name and file_info:
                            try:
                                print(f"파일 추가 처리 시작: {field_name}")
                                print(f"  파일명: {file_info.get('original_filename', 'N/A')}")
                                print(f"  해시: {file_info.get('file_hash', 'N/A')}")
                                print(f"  크기: {file_info.get('file_size', 'N/A')}")
                                
                                # 새 파일 텍스트 추출
                                file_text, file_hash = extract_file_text(field_name, file_info)
                                if file_text:
                                    file_texts.append(file_text)
                                    print(f"파일 추가 처리: {field_name} - {file_info.get('original_filename', '파일')} (해시: {file_hash or 'N/A'})")
                                else:
                                    print(f"파일 추가 처리 실패: 텍스트 추출 실패")
                            except Exception as e:
                                logger.error(f"추가된 파일 텍스트 추출 실패: {e}")
                                print(f"파일 추가 처리 중 오류: {e}")
                    
                    # 수정된 파일들 처리
                    modified_files = file_changes.get('modified', [])
                    for modified_file in modified_files:
                        field_name = modified_file.get('fieldName')
                        file_info = modified_file.get('fileInfo', {})
                        if field_name and file_info:
                            try:
                                print(f"파일 수정 처리 시작: {field_name}")
                                print(f"  파일명: {file_info.get('original_filename', 'N/A')}")
                                print(f"  새 해시: {file_info.get('file_hash', 'N/A')}")
                                
                                # 기존 파일 텍스트 제거 (파일명 기반)
                                original_file_texts_count = len(file_texts)
                                file_texts = [text for text in file_texts if not text.startswith(f"[{field_name} - {file_info.get('original_filename', '')}")]
                                removed_count = original_file_texts_count - len(file_texts)
                                print(f"  제거된 파일 텍스트 수: {removed_count}")
                                
                                # 새 파일 텍스트 추출
                                file_text, file_hash = extract_file_text(field_name, file_info)
                                if file_text:
                                    file_texts.append(file_text)
                                    print(f"파일 수정 처리: {field_name} - {file_info.get('original_filename', '파일')} (해시: {file_hash or 'N/A'})")
                                else:
                                    print(f"파일 수정 처리 실패: 텍스트 추출 실패")
                            except Exception as e:
                                logger.error(f"수정된 파일 텍스트 추출 실패: {e}")
                                print(f"파일 수정 처리 중 오류: {e}")
                    
                    # 캐시 업데이트
                    cache_data = {
                        'row_data': row_data,
                        'file_texts': file_texts,
                        'timestamp': current_time
                    }
                    request.session[cache_key] = cache_data
                    request.session.modified = True
                    cache_updated = True
                    
                    print(f"[AI 캐시 부분 업데이트] row_id={row_id}")
                    print(f"  추가된 파일: {len(added_files)}개")
                    print(f"  수정된 파일: {len(modified_files)}개")
                    print(f"  삭제된 파일: {len(deleted_files)}개")
                    for file_text in file_texts:
                        print(f"  최종 file_text: {file_text}")
        
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
            timeout=120  # 타임아웃을 2분으로 증가
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            return JsonResponse({
                'success': True,
                'response': ai_response,
                'cache_updated': cache_updated
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

def calculate_file_hash(file_path):
    """파일의 MD5 해시를 계산"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"파일 해시 계산 실패: {e}")
        return None

def extract_file_text(field_name, file_info):
    """파일 정보에서 텍스트 추출하는 헬퍼 함수"""
    try:
        # 파일 크기 체크 (10MB 제한)
        file_size = file_info.get('file_size', 0)
        if file_size > 10 * 1024 * 1024:  # 10MB
            return f"[{field_name} - {file_info.get('original_filename', '파일')}]: 파일이 너무 커서 텍스트 추출을 건너뜁니다.", None
        
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
            file_hash = calculate_file_hash(file_path)
            
            if file_text:
                result = f"[{field_name} - {file_info.get('original_filename', '파일')}]:\n{file_text}"
                # 파일 해시 정보를 로그에 추가
                if file_hash:
                    print(f"파일 해시 계산 완료: {file_hash} - {file_info.get('original_filename', '파일')}")
                return result, file_hash
            else:
                result = f"[{field_name} - {file_info.get('original_filename', '파일')}]: 텍스트 추출 실패"
                if file_hash:
                    print(f"파일 해시 계산 완료: {file_hash} - {file_info.get('original_filename', '파일')}")
                return result, file_hash
            
            # 임시 파일 정리
            try:
                os.remove(file_path)
            except:
                pass
            
            return result, file_hash
        else:
            return f"[{field_name} - {file_info.get('original_filename', '파일')}]: 파일을 다운로드할 수 없습니다.", None
    except Exception as e:
        logger.error(f"파일 텍스트 추출 실패: {e}")
        return f"[{field_name} - {file_info.get('original_filename', '파일')}]: 텍스트 추출 중 오류 발생", None

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
        elif file_path.endswith((".txt", ".md", ".markdown", ".rst", ".adoc")):
            # 텍스트 파일과 마크다운 파일 처리
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return content.strip()
            except UnicodeDecodeError:
                # UTF-8로 읽기 실패시 다른 인코딩 시도
                try:
                    with open(file_path, 'r', encoding='cp949') as f:
                        content = f.read()
                        return content.strip()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='euc-kr') as f:
                            content = f.read()
                            return content.strip()
                    except Exception as e:
                        logger.error(f"텍스트 파일 인코딩 처리 실패: {e}")
                        return f"텍스트 파일 읽기 실패: 인코딩 문제"
            except Exception as e:
                logger.error(f"텍스트 파일 읽기 실패: {e}")
                return f"텍스트 파일 읽기 실패: {str(e)}"
        elif file_path.endswith((".csv", ".tsv")):
            # CSV/TSV 파일 처리
            try:
                import csv
                delimiter = ',' if file_path.endswith('.csv') else '\t'
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    rows = list(reader)
                    if rows:
                        # 헤더와 데이터를 텍스트로 변환
                        result = []
                        for i, row in enumerate(rows):
                            if i == 0:  # 헤더
                                result.append(f"헤더: {' | '.join(row)}")
                            else:  # 데이터
                                result.append(f"행 {i}: {' | '.join(row)}")
                        return '\n'.join(result)
                    else:
                        return "빈 CSV/TSV 파일"
            except Exception as e:
                logger.error(f"CSV/TSV 파일 읽기 실패: {e}")
                return f"CSV/TSV 파일 읽기 실패: {str(e)}"
        elif file_path.endswith((".json", ".xml", ".yaml", ".yml")):
            # 구조화된 데이터 파일 처리
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return f"구조화된 데이터 파일 내용:\n{content.strip()}"
            except Exception as e:
                logger.error(f"구조화된 데이터 파일 읽기 실패: {e}")
                return f"구조화된 데이터 파일 읽기 실패: {str(e)}"
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