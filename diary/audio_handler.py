from .clova_speech import ClovaSpeechClient
from config import OPEN_AI_API_KEY
from langchain_openai import ChatOpenAI
from django.views.decorators.http import require_http_methods, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Attribute, AttributeValue, User, Row
import boto3
from django.conf import settings
import uuid
import os
import json
import logging
import hashlib
from django.http import JsonResponse
from .cascade_handlers import sync_cascade_attributes
import subprocess
import tempfile
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def calculate_file_hash(file_obj):
    """파일의 MD5 해시를 계산"""
    try:
        hash_md5 = hashlib.md5()
        # 파일 포인터를 처음으로 되돌림
        file_obj.seek(0)
        for chunk in iter(lambda: file_obj.read(4096), b""):
            hash_md5.update(chunk)
        # 파일 포인터를 다시 처음으로 되돌림 (다른 곳에서 사용할 수 있도록)
        file_obj.seek(0)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"파일 해시 계산 실패: {e}")
        return None

# ----------------------------음성파일------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def upload_audio_file(request):
    """음성파일을 업로드하고 변환된 텍스트를 저장하는 뷰"""
    
    if request.method == 'POST':
        audio_file = request.FILES.get('audio_file')
        row_id = request.POST.get('row_id')
        field_name = request.POST.get('field_name', '음성파일')

        print(f"Received audio file: {audio_file}")
        print(f"Received row ID: {row_id}")
        print(f"Received field name: {field_name}")
        
        # 필수 파라미터 검증
        if not audio_file:
            return JsonResponse({
                'success': False,
                'error': '음성파일이 필요합니다.'
            })
        
        if not row_id:
            return JsonResponse({
                'success': False,
                'error': 'row_id가 필요합니다.'
            })
        
        # 파일 크기 제한 (20MB)
        max_file_size = 20 * 1024 * 1024  # 20MB
        if audio_file.size > max_file_size:
            return JsonResponse({
                'success': False,
                'error': '파일 크기가 20MB를 초과합니다.'
            })
        
        # 오디오 파일 검증
        if not audio_file.content_type.startswith('audio/'):
            return JsonResponse({
                'success': False,
                'error': '오디오 파일만 업로드 가능합니다.'
            })
        
        try:
            # 사용자 ID를 1로 고정 (이미 import된 User 모델 사용)
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            
            # Row 존재 여부 확인
            row = Row.objects.get(id=row_id, user=user)
            
            # 음성파일 속성 조회 (변환된 텍스트 속성은 더 이상 사용하지 않음)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            
            if not audio_attribute:
                return JsonResponse({
                    'success': False,
                    'error': '음성파일 속성을 찾을 수 없습니다.'
                })
            
            # 오늘 날짜 생성
            from datetime import date
            today = date.today().strftime('%y.%m.%d')
            
            # Clova Speech-to-Text API 호출
            converted_text = ""
            gpt_summary = ""
            try:
                # 임시 파일로 저장 (Clova Speech는 파일 업로드 방식)
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as temp_file:
                    for chunk in audio_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                # Clova Speech API 호출
                clova_client = ClovaSpeechClient()
                response = clova_client.req_upload(file=temp_file_path, completion='sync')
                result = response.json()
                
                # 화자별 인식 결과 segment 추출
                segments = result.get('segments', [])
                speaker_segments = []
                converted_text = ''

                for segment in segments:
                    speaker_label = segment['speaker']['label']
                    text = segment['text']
                    speaker_segments.append({'start': segment['start'], 'end': segment['end'], 'speaker': speaker_label, 'text': text})

                for speaker_segment in speaker_segments:
                    start_mil = speaker_segment['start']
                    end_mil = speaker_segment['end']
                    
                    # Convert milliseconds to minutes and seconds
                    def ms_to_min_sec(milliseconds):
                        if milliseconds == 0:
                            return 0, 0
                        
                        total_seconds = milliseconds / 1000
                        minutes = int(total_seconds // 60)
                        seconds = int(total_seconds % 60)
                        return minutes, seconds
                    
                    def format_time(minutes, seconds):
                        if minutes == 0:
                            return f"{seconds}초"
                        else:
                            return f"{minutes}분 {seconds}초"
                    
                    start_min, start_sec = ms_to_min_sec(start_mil)
                    end_min, end_sec = ms_to_min_sec(end_mil)
                    
                    start_time_str = format_time(start_min, start_sec)
                    end_time_str = format_time(end_min, end_sec)
                
                    speaker_label = speaker_segment['speaker']
                    text = speaker_segment['text']

                    converted_text += f'Speaker {speaker_label}({start_time_str}~): {text} \n'
                
                # GPT 요약 생성
                llm = ChatOpenAI(
                    temperature=0,
                    model_name='gpt-4o-mini',
                    openai_api_key=OPEN_AI_API_KEY
                )

                user_input = "담당자와 고객사가 대한 통화한 내용이야. 각자 언급한 내용을 정리하고, 전체적인 소통내용을 정리해줘. 그리고 고객사의 심리상태를 간단하게 설명해줘. "

                texts = converted_text + user_input

                response = llm.invoke(texts)
                # 다양한 종류의 공백 문자를 제거하는 강력한 정리
                import re
                gpt_summary = response.content.replace("**", "").replace("#", "")
                # 모든 종류의 공백 문자 제거 (공백, 탭, 개행 등)
                gpt_summary = re.sub(r'^\s+', '', gpt_summary)  # 앞쪽 공백 제거
                gpt_summary = re.sub(r'\s+$', '', gpt_summary)  # 뒤쪽 공백 제거
                gpt_summary = re.sub(r'\n\s*\n', '\n\n', gpt_summary)  # 연속된 빈 줄 정리
                print("[GPT 응답 원본]:", gpt_summary)
                
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                    
            except Exception as stt_error:
                print(f"Clova STT API 오류: {stt_error}")
                # 임시 파일이 있다면 삭제
                try:
                    if 'temp_file_path' in locals():
                        os.unlink(temp_file_path)
                except:
                    pass

            # S3에 파일 업로드
            try:
                # 파일 포인터를 다시 처음으로 이동 (S3 업로드용)
                audio_file.seek(0)
                
                # 고유한 파일명 생성
                file_extension = os.path.splitext(audio_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                s3_key = f"audio_files/{unique_filename}"
                
                # S3 클라이언트 생성
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # S3에 파일 업로드
                s3_client.upload_fileobj(
                    audio_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': audio_file.content_type,
                        'ContentDisposition': f'attachment; filename="{audio_file.name}"'
                    }
                )
                
                # 다운로드 URL 생성
                download_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                
                # 서명된 다운로드 URL 생성 (24시간 유효)
                try:
                    signed_download_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': s3_key
                        },
                        ExpiresIn=300  # 5분
                    )
                    print(f"서명된 다운로드 URL 생성 성공 (5분 유효)")
                except Exception as e:
                    print(f"서명된 URL 생성 실패: {e}")
                    signed_download_url = download_url
                
                # 서명된 미리보기 URL 생성 (24시간 유효, inline으로 설정)
                try:
                    signed_preview_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': s3_key,
                            'ResponseContentDisposition': 'inline'
                        },
                        ExpiresIn=300  # 5분
                    )
                    print(f"서명된 미리보기 URL 생성 성공 (5분 유효)")
                except Exception as e:
                    print(f"서명된 미리보기 URL 생성 실패: {e}")
                    signed_preview_url = download_url
                
                print(f"S3 업로드 성공:")
                print(f"  원본 파일명: {audio_file.name}")
                print(f"  S3 파일명: {unique_filename}")
                print(f"  다운로드 URL: {download_url}")
                print(f"  서명된 다운로드 URL: {signed_download_url}")
                print(f"  서명된 미리보기 URL: {signed_preview_url}")
                
            except Exception as e:
                print(f"S3 업로드 실패: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'파일 업로드 실패: {str(e)}'
                })
            
            # 기존 음성파일 데이터 가져오기 또는 빈 dict 생성
            existing_attr_value = AttributeValue.objects.filter(
                row=row,
                attribute=audio_attribute
            ).first()
            
            if existing_attr_value and existing_attr_value.value:
                try:
                    existing_data = json.loads(existing_attr_value.value)
                except (json.JSONDecodeError, TypeError):
                    existing_data = {}
            else:
                existing_data = {}
            
            # 기존 파일들의 order 값을 1씩 증가시키기 (새 파일이 맨 위에 오도록)
            for date_key in existing_data:
                date_data = existing_data[date_key]
                
                # date_data가 딕셔너리인 경우 (기존 구조)
                if isinstance(date_data, dict):
                    for file_id_key in date_data:
                        file_info = date_data[file_id_key]
                        if isinstance(file_info, dict):
                            current_order = file_info.get('order', 0)
                            file_info['order'] = current_order + 1
                
                # date_data가 리스트인 경우 (새로운 구조)
                elif isinstance(date_data, list):
                    for file_info in date_data:
                        if isinstance(file_info, dict):
                            current_order = file_info.get('order', 0)
                            file_info['order'] = current_order + 1
            
            # 고유한 파일 ID 생성 (시간 포함)
            from datetime import datetime
            file_id = datetime.now().strftime('%H%M%S')  # HHMMSS 형식
            
            # 파일 해시 계산
            file_hash = calculate_file_hash(audio_file)
            
            # 새로운 파일 데이터 생성 (order를 0으로 설정하여 맨 위에 표시)
            new_file_data = {
                'original_filename': audio_file.name,
                'stored_filename': unique_filename,
                's3_key': s3_key,
                'download_url': signed_download_url,
                'preview_url': signed_preview_url,
                'public_url': download_url,
                'file_size': audio_file.size,
                'content_type': audio_file.content_type,
                'converted_text': converted_text,
                'gpt_summary': gpt_summary,
                'upload_time': datetime.now().strftime('%H:%M:%S'),
                'order': 0,  # 새로 업로드된 파일은 항상 맨 위에
                'type': 'audio',  # 타입 구분을 위한 필드 추가
                'file_hash': file_hash,  # 파일 해시 추가
                'last_modified': audio_file.last_modified if hasattr(audio_file, 'last_modified') else None
            }
            
            # 날짜별로 데이터 구조화
            if 'data' not in existing_data:
                existing_data['data'] = {}
            new_file_data['upload_date'] = today
            existing_data['data'][file_id] = new_file_data
            
            # 음성파일 속성에 전체 데이터 저장
            if existing_attr_value:
                existing_attr_value.value = json.dumps(existing_data, ensure_ascii=False)
                existing_attr_value.save()
            else:
                AttributeValue.objects.create(
                    row=row,
                    attribute=audio_attribute,
                    value=json.dumps(existing_data, ensure_ascii=False)
                )
            
            print(f"Row ID {row_id}의 음성파일 데이터 저장 완료 (날짜: {today})")
            
            return JsonResponse({
                'success': True,
                'date': today,
                'file_id': file_id,
                'converted_text': converted_text,
                'gpt_summary': gpt_summary,
                'file_info': {
                    'original_filename': audio_file.name,
                    'download_url': signed_download_url,
                    'preview_url': signed_preview_url,
                    'file_size': audio_file.size,
                    'content_type': audio_file.content_type,
                    'upload_time': new_file_data['upload_time']
                },
                'message': '음성파일 업로드 및 변환이 완료되었습니다.'
            })
                
        except Row.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 행을 찾을 수 없습니다.'
            })
        except Exception as e:
            print(f"음성파일 처리 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'처리 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'POST 요청만 허용됩니다.'
    })

@require_GET
def get_audio_files_by_date(request):
    """특정 행의 날짜별 음성파일 데이터를 조회하는 API"""
    try:
        row_id = request.GET.get('row_id')
        
        if not row_id:
            return JsonResponse({
                'success': False,
                'error': 'row_id가 필요합니다.'
            })
        
        # 사용자 ID를 1로 고정
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # Row와 음성파일 속성 조회
        row = Row.objects.get(id=row_id, user=user)
        audio_attribute = Attribute.objects.get(name='음성파일', user=user)
        
        # 음성파일 데이터 조회
        attr_value = AttributeValue.objects.filter(
            row=row,
            attribute=audio_attribute
        ).first()
        
        if attr_value and attr_value.value:
            try:
                audio_data = json.loads(attr_value.value)
                
                # 날짜별로 정리된 데이터 반환
                formatted_data = {}
                for date_key, files in audio_data.items():
                    formatted_data[date_key] = []
                    for file_id, file_info in files.items():
                        formatted_data[date_key].append({
                            'file_id': file_id,
                            'original_filename': file_info.get('original_filename', ''),
                            'converted_text': file_info.get('converted_text', ''),
                            'gpt_summary': file_info.get('gpt_summary', ''),
                            'download_url': file_info.get('download_url', ''),
                            'preview_url': file_info.get('preview_url', ''),
                            'file_size': file_info.get('file_size', 0),
                            'upload_time': file_info.get('upload_time', ''),
                            'content_type': file_info.get('content_type', '')
                        })
                
                return JsonResponse({
                    'success': True,
                    'audio_data': formatted_data
                })
                
            except (json.JSONDecodeError, TypeError):
                return JsonResponse({
                    'success': True,
                    'audio_data': {}
                })
        else:
            return JsonResponse({
                'success': True,
                'audio_data': {}
            })
            
    except Row.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 행을 찾을 수 없습니다.'
        })
    except Attribute.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '음성파일 속성을 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"오디오 파일 조회 오류: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'오디오 파일 조회 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
def delete_audio_file(request):
    """특정 날짜의 특정 음성파일 삭제"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 메서드만 허용됩니다.'})
    
    try:
        row_id = request.POST.get('row_id')
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        
        if not all([row_id, date, file_id]):
            return JsonResponse({
                'success': False,
                'error': 'row_id, date, file_id가 모두 필요합니다.'
            })
        
        # 사용자 및 Row 조회
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        row = Row.objects.get(id=row_id, user=user)
        
        # 음성파일 속성 조회
        audio_attribute = Attribute.objects.get(name='음성파일', user=user)
        
        # 기존 AttributeValue 조회
        try:
            attr_value = AttributeValue.objects.filter(row=row, attribute=audio_attribute).first()
            current_data = json.loads(attr_value.value) if attr_value and attr_value.value else {}
        except AttributeValue.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 데이터를 찾을 수 없습니다.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '음성파일 데이터 형식이 올바르지 않습니다.'})
        
        # 해당 날짜와 파일 ID 확인
        if date not in current_data:
            return JsonResponse({'success': False, 'error': f'{date} 날짜 데이터를 찾을 수 없습니다.'})
        
        if file_id not in current_data[date]:
            return JsonResponse({'success': False, 'error': f'파일 ID {file_id}를 찾을 수 없습니다.'})
        
        # S3에서 파일 삭제 시도
        file_info = current_data[date][file_id]
        try:
            if 'stored_filename' in file_info:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                delete_response = s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f"audio_files/{file_info['stored_filename']}"
                )
                logger.info(f"S3 파일 삭제 완료: {file_info['stored_filename']}")
        except Exception as e:
            logger.warning(f"S3 파일 삭제 실패 (계속 진행): {str(e)}")
        
        # 데이터에서 해당 파일 제거
        del current_data[date][file_id]
        
        # 해당 날짜에 다른 파일이 없으면 날짜 자체도 제거
        if not current_data[date]:
            del current_data[date]
        
        # 업데이트된 데이터 저장
        if current_data:
            attr_value.value = json.dumps(current_data, ensure_ascii=False)
            attr_value.save()
        else:
            # 모든 음성파일이 삭제된 경우
            attr_value.value = ''
            attr_value.save()
        
        logger.info(f"음성파일 삭제 완료 - Row: {row_id}, Date: {date}, File: {file_id}")
        
        return JsonResponse({
            'success': True,
            'message': '음성파일이 성공적으로 삭제되었습니다.',
            'remaining_files': len(current_data)
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
    except Row.DoesNotExist:
        return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
    except Attribute.DoesNotExist:
        return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
    except Exception as e:
        logger.error(f"음성파일 삭제 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'음성파일 삭제 중 오류가 발생했습니다: {str(e)}'
        })
    
@csrf_exempt
def update_audio_file_order(request):
    """
    음성파일들의 순서를 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # 파라미터 검증
        row_id = request.POST.get('row_id')
        ordered_files = request.POST.get('ordered_files')
        
        if not all([row_id, ordered_files]):
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 순서 데이터 파싱
        try:
            ordered_files_data = json.loads(ordered_files)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '순서 데이터 형식이 올바르지 않습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        
        # 기존 AttributeValue 가져오기
        try:
            attr_value = AttributeValue.objects.filter(row=row, attribute=audio_attribute).first()
            current_data = json.loads(attr_value.value) if attr_value and attr_value.value else {}
        except AttributeValue.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 데이터를 찾을 수 없습니다.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '음성파일 데이터 형식이 올바르지 않습니다.'})
        
        # 각 파일에 순서 번호 추가
        for index, file_data in enumerate(ordered_files_data):
            date = file_data.get('date')
            file_id = file_data.get('file_id')
            
            if date and file_id and date in current_data and file_id in current_data[date]:
                current_data[date][file_id]['order'] = index
        
        # 업데이트된 데이터 저장
        attr_value.value = json.dumps(current_data, ensure_ascii=False)
        attr_value.save()
        
        logger.info(f"음성파일 순서 업데이트 완료 - Row: {row_id}")
        
        return JsonResponse({
            'success': True,
            'message': '파일 순서가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"음성파일 순서 업데이트 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'순서 업데이트 중 오류가 발생했습니다: {str(e)}'
        })
    
@csrf_exempt
def upload_note_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        row_id = request.POST.get('row_id')
        if not file or not row_id:
            return JsonResponse({'success': False, 'error': '파일 또는 row_id 누락'})
        
        # 파일 크기 제한 (20MB)
        max_file_size = 20 * 1024 * 1024  # 20MB
        if file.size > max_file_size:
            return JsonResponse({'success': False, 'error': '파일 크기가 20MB를 초과합니다.'})
        
        # 파일 해시 계산 (업로드 전에 먼저 계산)
        import hashlib
        file_hash = None
        try:
            hash_md5 = hashlib.md5()
            file.seek(0)
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
            file.seek(0)
            file_hash = hash_md5.hexdigest()
        except Exception as e:
            print(f"파일 해시 계산 실패: {e}")
        
        # === DB 저장 로직 추가 ===
        from .models import User, Row, Attribute, AttributeValue
        import json
        from django.db import transaction
        from django.db.models import Q

        user_id = request.session.get('diary_member_id')

        try:
            with transaction.atomic():
                user = User.objects.get(id=user_id)
                row = Row.objects.get(id=row_id, user=user)
                attr = Attribute.objects.get(name='음성파일', user=user)
                
                # 중복 데이터 문제 해결: get_or_create 대신 filter().first() 사용
                attr_value = AttributeValue.objects.filter(row=row, attribute=attr).first()
                if not attr_value:
                    attr_value = AttributeValue.objects.create(row=row, attribute=attr, value='{"data": {}}')
                
                # 기존 값이 있으면 파싱, 없으면 빈 dict
                try:
                    value_dict = json.loads(attr_value.value) if attr_value.value else {"data": {}}
                except Exception:
                    value_dict = {"data": {}}
                
                # 파일 해시 기반 중복 체크
                existing_files = value_dict.get("data", {})
                duplicate_file_id = None
                for fid, file_data in existing_files.items():
                    if (file_data.get('original_filename') == file.name and 
                        file_data.get('file_size') == file.size and
                        file_data.get('file_hash') == file_hash):
                        duplicate_file_id = fid
                        break
                
                if duplicate_file_id:
                    # 중복 파일이 이미 존재하는 경우 기존 파일 정보 반환
                    existing_file_info = existing_files[duplicate_file_id]
                    return JsonResponse({
                        'success': True, 
                        'file_info': existing_file_info, 
                        'file_id': duplicate_file_id,
                        'message': '이미 업로드된 파일입니다.'
                    })
                
                # S3 업로드
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                file_extension = os.path.splitext(file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                s3_key = f"note_files/{unique_filename}"
                s3_client.upload_fileobj(
                    file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': file.content_type,
                        'ContentDisposition': f'attachment; filename=\"{file.name}\"'
                    }
                )
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
                    ExpiresIn=300
                )
                preview_url = download_url
                
                file_info = {
                    'original_filename': file.name,
                    'stored_filename': unique_filename,
                    's3_key': s3_key,
                    'download_url': download_url,
                    'preview_url': preview_url,
                    'file_size': file.size,
                    'content_type': file.content_type,
                    'type': None,  # type 필드 추가
                    'file_hash': file_hash,  # 파일 해시 추가
                    'last_modified': file.last_modified if hasattr(file, 'last_modified') else None
                }
                # 파일 타입 판별
                if file.content_type.startswith('image/'):
                    file_info['type'] = 'image'
                elif file.content_type.startswith('audio/'):
                    file_info['type'] = 'audio'
                else:
                    file_info['type'] = 'file'
                
                # 고유 id 생성 (더 정확한 타임스탬프 사용)
                import time
                file_id = f'f{int(time.time()*1000000)}'  # 마이크로초 단위로 더 정확하게
                
                # order 필드 추가 (기존 아이템 개수 + 1)
                existing_count = len(value_dict.get("data", {}))
                file_info['order'] = existing_count
                
                value_dict["data"][file_id] = file_info
                attr_value.value = json.dumps(value_dict, ensure_ascii=False)
                attr_value.save()
                
                # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
                if attr.cascade:
                    print(f"=== Cascade 동기화 시작 (upload_note_file) ===")
                    print(f"속성 '음성파일'의 cascade 값: {attr.cascade}")
                    print(f"수정된 행 ID: {row_id}")
                    print(f"새 값: {json.dumps(value_dict, ensure_ascii=False)}")
                    
                    synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(value_dict, ensure_ascii=False))
                    if synced_count > 0:
                        print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                    else:
                        print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                    print(f"=== Cascade 동기화 종료 (upload_note_file) ===")
                else:
                    print(f"속성 '음성파일'의 cascade 값: {attr.cascade} - 동기화하지 않음")
                
                return JsonResponse({'success': True, 'file_info': file_info, 'file_id': file_id})
                
        except Exception as e:
            print(f"파일 업로드 중 오류: {e}")
            return JsonResponse({'success': False, 'error': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def delete_note_file(request):
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        file_id = request.POST.get('file_id')
        s3_key = request.POST.get('s3_key')
        
        if not row_id or not file_id or not s3_key:
            return JsonResponse({'success': False, 'error': 'row_id, file_id, s3_key 모두 필요합니다'})
        
        try:
            # 사용자와 행 조회
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            row = Row.objects.get(id=row_id, user=user)
            audio_attr = Attribute.objects.get(name='음성파일', user=user)
            attr_value = AttributeValue.objects.get(row=row, attribute=audio_attr)
            
            # 기존 데이터 파싱
            try:
                current_data = json.loads(attr_value.value) if attr_value.value else {}
            except json.JSONDecodeError:
                current_data = {}
            
            # 'data' 키가 없으면 생성
            if 'data' not in current_data:
                current_data['data'] = {}
            
            # 해당 file_id가 존재하는지 확인
            if file_id not in current_data['data']:
                return JsonResponse({'success': False, 'error': '해당 파일을 찾을 수 없습니다'})
            
            # S3에서 파일 삭제
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            try:
                s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
                print(f"S3 파일 삭제 완료: {s3_key}")
            except Exception as e:
                print(f"S3 파일 삭제 실패 (계속 진행): {str(e)}")
                # S3 삭제 실패해도 DB에서 삭제는 진행
            
            # DB에서 해당 파일 데이터 삭제
            del current_data['data'][file_id]
            
            # 업데이트된 데이터 저장
            attr_value.value = json.dumps(current_data, ensure_ascii=False)
            attr_value.save()
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attr.cascade:
                print(f"=== Cascade 동기화 시작 (delete_note_file) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(current_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(current_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (delete_note_file) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade} - 동기화하지 않음")
            
            print(f"노트 파일 삭제 완료 - Row: {row_id}, File: {file_id}")
            
            return JsonResponse({
                'success': True,
                'message': '파일이 성공적으로 삭제되었습니다.',
                'remaining_files': len(current_data['data'])
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        except AttributeValue.DoesNotExist:
            return JsonResponse({'success': False, 'error': '속성 값을 찾을 수 없습니다.'})
        except Exception as e:
            print(f"노트 파일 삭제 중 오류: {e}")
            return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})

@csrf_exempt
def update_note_order_and_notes(request):
    """노트 순서와 텍스트 노트를 업데이트하는 API"""
    if request.method == 'POST':
        try:
            row_id = request.POST.get('row_id')
            notes_data = request.POST.get('notes')
            
            if not row_id or not notes_data:
                return JsonResponse({
                    'success': False,
                    'error': 'row_id와 notes가 필요합니다.'
                })
            
            # 사용자 ID를 1로 고정
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            
            # Row와 음성파일 속성 조회
            row = Row.objects.get(id=row_id, user=user)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            
            # JSON 데이터 파싱
            try:
                notes = json.loads(notes_data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': '잘못된 JSON 형식입니다.'
                })
            
            # 기존 데이터 구조 생성
            existing_data = {'data': {}}
            
            # 노트 데이터 처리
            for note in notes:
                note_id = note.get('id')
                note_type = note.get('type', 'file')
                order = note.get('order', 0)
                
                if note_type == 'text':
                    # 텍스트 노트
                    existing_data['data'][note_id] = {
                        'id': note_id,
                        'type': 'text',
                        'text': note.get('text', ''),
                        'order': order,
                        'upload_date': note.get('upload_date', '')
                    }
                else:
                    # 파일 노트 (기존 파일 정보 유지)
                    existing_data['data'][note_id] = {
                        'id': note_id,
                        'type': note.get('type', 'file'),
                        'original_filename': note.get('original_filename', ''),
                        'stored_filename': note.get('stored_filename', ''),
                        's3_key': note.get('s3_key', ''),
                        'download_url': note.get('download_url', ''),
                        'preview_url': note.get('preview_url', ''),
                        'file_size': note.get('file_size', 0),
                        'content_type': note.get('content_type', ''),
                        'order': order,
                        'upload_date': note.get('upload_date', '')
                    }
            
            # 음성파일 속성에 저장
            attr_value, created = AttributeValue.objects.get_or_create(
                row=row,
                attribute=audio_attribute,
                defaults={'value': json.dumps(existing_data, ensure_ascii=False)}
            )
            
            if not created:
                attr_value.value = json.dumps(existing_data, ensure_ascii=False)
                attr_value.save()
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attribute.cascade:
                print(f"=== Cascade 동기화 시작 (update_note_order_and_notes) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(existing_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(existing_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (update_note_order_and_notes) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade} - 동기화하지 않음")
            
            return JsonResponse({
                'success': True,
                'message': '노트 순서와 텍스트 노트가 업데이트되었습니다.'
            })
            
        except Row.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 행을 찾을 수 없습니다.'
            })
        except Exception as e:
            print(f"노트 업데이트 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'처리 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'POST 요청만 허용됩니다.'
    })

@csrf_exempt
def get_file_preview_url_note(request, file_id):
    """파일 미리보기를 위한 새로운 S3 서명된 URL을 생성하는 API"""
    if request.method == 'GET':
        print(f"get_file_preview_url_note 호출됨: {file_id}")
        try:
            row_id = request.GET.get('row_id')
            if not row_id:
                return JsonResponse({'success': False, 'error': 'row_id가 필요합니다.'})
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            row = Row.objects.get(id=row_id, user=user)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            attr_value = AttributeValue.objects.filter(row=row, attribute=audio_attribute).first()
            if not attr_value or not attr_value.value:
                return JsonResponse({'success': False, 'error': '파일 데이터를 찾을 수 없습니다.'})
            try:
                audio_data = json.loads(attr_value.value)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
            file_info = None
            if 'data' in audio_data:
                for k, v in audio_data['data'].items():
                    if not isinstance(v, dict):
                        continue
                    # 정확히 key 또는 stored_filename으로만 매칭
                    if k == file_id or v.get('stored_filename') == file_id:
                        file_info = v
                        break
            if not file_info:
                return JsonResponse({'success': False, 'error': f'파일 ID {file_id}를 찾을 수 없습니다.'})
            s3_key = file_info.get('s3_key')
            if not s3_key:
                return JsonResponse({'success': False, 'error': 'S3 키가 없습니다.'})
            
            content_type = file_info.get('content_type', '')
            original_filename = file_info.get('original_filename', '')
            
            # HWP/HWPX 파일인 경우 PDF로 변환
            if (content_type in ['application/x-hwp', 'application/haansofthwp', 'application/vnd.hancom.hwp'] or
                original_filename.lower().endswith(('.hwp', '.hwpx'))):
                
                print(f"HWP/HWPX 파일 감지: {original_filename}")
                
                # LibreOffice 상태 확인
                if not check_libreoffice_status():
                    return JsonResponse({'success': False, 'error': '파일 변환에 실패했습니다.'})
                
                try:
                    # S3에서 파일 다운로드
                    temp_file_path = download_file_from_s3_for_preview(s3_key)
                    if not temp_file_path:
                        return JsonResponse({'success': False, 'error': '파일 다운로드에 실패했습니다.'})
                    
                    # HWP를 PDF로 변환
                    pdf_path = convert_hwp_to_pdf(temp_file_path)
                    if not pdf_path or not os.path.exists(pdf_path):
                        # 임시 파일 정리
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        return JsonResponse({'success': False, 'error': 'HWP 파일을 PDF로 변환하는데 실패했습니다.'})
                    
                    # 변환된 PDF를 S3에 업로드하고 미리보기 URL 생성
                    preview_url = upload_pdf_to_s3_for_preview(pdf_path, s3_key)
                    
                    # 임시 파일들 정리
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    
                    if preview_url:
                        return JsonResponse({'success': True, 'preview_url': preview_url, 'converted_to_pdf': True})
                    else:
                        return JsonResponse({'success': False, 'error': 'PDF 미리보기 URL 생성에 실패했습니다.'})
                        
                except Exception as e:
                    # 임시 파일 정리
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if 'pdf_path' in locals() and os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    return JsonResponse({'success': False, 'error': f'HWP 변환 중 오류가 발생했습니다: {str(e)}'})
            
            # 기존 로직 (HWP/HWPX가 아닌 경우)
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                if (content_type == 'application/pdf' or 
                    content_type.startswith('image/') or
                    content_type == 'text/plain' or
                    content_type == 'text/html' or
                    content_type == 'text/css' or
                    content_type == 'text/javascript' or
                    content_type == 'application/json' or
                    content_type == 'application/xml'):
                    content_disposition = 'inline'
                else:
                    content_disposition = 'attachment'
                signed_preview_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': s3_key,
                        'ResponseContentDisposition': content_disposition
                    },
                    ExpiresIn=3600
                )
                return JsonResponse({'success': True, 'preview_url': signed_preview_url})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'S3 URL 생성 실패: {str(e)}'})
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'})

def check_libreoffice_status():
    """LibreOffice 설치 및 실행 상태 확인"""
    try:
        result = subprocess.run(['libreoffice', '--version'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"LibreOffice 상태 확인 실패: {e}")
        return False

def convert_hwp_to_pdf(hwp_path):
    """HWP를 PDF로 변환"""
    output_dir = os.path.dirname(hwp_path)
    try:
        # 파일 크기 확인
        file_size = os.path.getsize(hwp_path)
        print(f"📄 HWP 파일 크기: {file_size / (1024*1024):.2f} MB")
        
        # 파일 크기에 따른 timeout 조정
        if file_size > 50 * 1024 * 1024:  # 50MB 이상
            timeout = 1800  # 30분
            print("⏰ 대용량 파일 감지, timeout을 30분으로 설정")
        elif file_size > 10 * 1024 * 1024:  # 10MB 이상
            timeout = 900   # 15분
            print("⏰ 중간 크기 파일 감지, timeout을 15분으로 설정")
        else:
            timeout = 600   # 10분 (기본값)
            print("⏰ 기본 timeout 10분 설정")
        
        print("🖥️ LibreOffice 변환 시작...")
        
        result = subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf:writer_pdf_Export",
            hwp_path,
            "--outdir", output_dir
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)

        print("🖥️ libreoffice stdout: " + result.stdout.decode())
        if result.stderr:
            print("🖥️ libreoffice stderr: " + result.stderr.decode())

        basename = os.path.splitext(os.path.basename(hwp_path))[0] + ".pdf"
        converted_pdf = os.path.join(output_dir, basename)

        if os.path.exists(converted_pdf):
            pdf_size = os.path.getsize(converted_pdf)
            print(f"✅ 변환 성공: {pdf_size / (1024*1024):.2f} MB")
            return converted_pdf
        else:
            print(f"[❌ 변환 실패] {converted_pdf} 파일이 존재하지 않습니다.")
            return ""
            
    except subprocess.TimeoutExpired:
        print(f"[⏰ Timeout 발생] {timeout}초 초과로 변환 실패")
        # LibreOffice 프로세스 강제 종료
        try:
            subprocess.run(["pkill", "-f", "libreoffice"], timeout=10)
            print("🔄 LibreOffice 프로세스 강제 종료 완료")
        except:
            print("⚠️ LibreOffice 프로세스 종료 실패")
        return ""
    except Exception as e:
        print(f"[예외 발생] HWP → PDF 변환 실패: {e}")
        return ""

def download_file_from_s3_for_preview(s3_key):
    """S3에서 파일을 임시로 다운로드하여 미리보기용으로 사용"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 임시 디렉토리에 파일 다운로드
        temp_dir = tempfile.gettempdir()
        temp_filename = f"preview_{os.path.basename(s3_key)}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        s3_client.download_file(
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            temp_path
        )
        
        return temp_path
    except Exception as e:
        print(f"S3 파일 다운로드 실패: {e}")
        return None

def upload_pdf_to_s3_for_preview(pdf_path, original_s3_key):
    """변환된 PDF를 S3에 업로드하여 미리보기용 URL 생성"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 원본 파일명에서 확장자만 PDF로 변경
        original_filename = os.path.basename(original_s3_key)
        pdf_filename = os.path.splitext(original_filename)[0] + "_preview.pdf"
        preview_s3_key = f"preview/{pdf_filename}"
        
        # PDF 파일을 S3에 업로드
        s3_client.upload_file(
            pdf_path,
            settings.AWS_STORAGE_BUCKET_NAME,
            preview_s3_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        
        # 미리보기용 presigned URL 생성
        signed_preview_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': preview_s3_key,
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=3600
        )
        
        return signed_preview_url
    except Exception as e:
        print(f"PDF S3 업로드 실패: {e}")
        return None
    
@csrf_exempt
def get_file_content_note(request, file_id):
    """텍스트 파일의 내용을 가져오는 API (CORS 문제 해결용)"""
    if request.method == 'GET':
        print(f"get_file_content_note 호출됨: {file_id}")
        try:
            row_id = request.GET.get('row_id')
            if not row_id:
                return JsonResponse({'success': False, 'error': 'row_id가 필요합니다.'})
             
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            row = Row.objects.get(id=row_id, user=user)
            audio_attribute = Attribute.objects.get(name='음성파일', user=user)
            attr_value = AttributeValue.objects.filter(row=row, attribute=audio_attribute).first()
            
            if not attr_value or not attr_value.value:
                return JsonResponse({'success': False, 'error': '파일 데이터를 찾을 수 없습니다.'})
            
            try:
                audio_data = json.loads(attr_value.value)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': '잘못된 데이터 형식입니다.'})
            
            file_info = None
            if 'data' in audio_data:
                for k, v in audio_data['data'].items():
                    if not isinstance(v, dict):
                        continue
                    # 정확히 key 또는 stored_filename으로만 매칭
                    if k == file_id or v.get('stored_filename') == file_id:
                        file_info = v
                        break
            
            if not file_info:
                return JsonResponse({'success': False, 'error': f'파일 ID {file_id}를 찾을 수 없습니다.'})
            
            s3_key = file_info.get('s3_key')
            if not s3_key:
                return JsonResponse({'success': False, 'error': 'S3 키가 없습니다.'})
            
            # 파일 확장자 확인
            filename = file_info.get('original_filename', '')
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            try:
                import boto3
                from django.conf import settings
                import chardet
                
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # S3에서 파일 내용 가져오기
                response = s3_client.get_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=s3_key
                )
                file_content = response['Body'].read()
                
                # 인코딩 감지 및 디코딩
                detected = chardet.detect(file_content)
                detected_encoding = detected['encoding']
                confidence = detected['confidence']
                
                print(f"감지된 인코딩: {detected_encoding}, 신뢰도: {confidence}")
                
                # 파일 확장자에 따른 기본 인코딩 설정
                default_encoding = 'utf-8'
                if file_ext in ['txt', 'log', 'csv']:
                    default_encoding = 'euc-kr'
                elif file_ext in ['json', 'xml', 'html', 'htm', 'css', 'js']:
                    default_encoding = 'utf-8'
                
                # 다양한 인코딩 시도
                encodings_to_try = [detected_encoding, default_encoding, 'utf-8', 'euc-kr', 'cp949', 'iso-8859-1']
                decoded_content = None
                used_encoding = None
                
                for encoding in encodings_to_try:
                    if not encoding:
                        continue
                    try:
                        decoded_content = file_content.decode(encoding)
                        used_encoding = encoding
                        
                        # 한글 파일의 경우 한글이 포함되어 있는지 확인
                        if file_ext in ['txt', 'log', 'csv']:
                            import re
                            korean_pattern = re.compile(r'[가-힣]')
                            if korean_pattern.search(decoded_content):
                                print(f"한글 텍스트 감지됨 - 인코딩: {encoding}")
                                break
                        else:
                            # 웹 파일들은 첫 번째 성공한 인코딩 사용
                            break
                    except (UnicodeDecodeError, LookupError):
                        print(f"인코딩 {encoding} 실패, 다음 시도...")
                        continue
                
                if not decoded_content:
                    # 모든 인코딩이 실패한 경우 기본값 사용
                    decoded_content = file_content.decode('utf-8', errors='replace')
                    used_encoding = 'utf-8 (fallback)'
                
                return JsonResponse({
                    'success': True, 
                    'content': decoded_content,
                    'encoding': used_encoding,
                    'detected_encoding': detected_encoding,
                    'confidence': confidence
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'파일 내용 읽기 실패: {str(e)}'})
                
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'처리 중 오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'GET 요청만 허용됩니다.'})

@require_GET
def get_file_preview_url(request, row_id, field_name):
    """단일 파일 필드(영업노트 방식) presigned URL 반환"""
    try:
        print(f'row_id: {row_id}, field_name: {field_name}')
        
        # file_id 파라미터 추가
        file_id = request.GET.get('file_id')
        print(f'file_id: {file_id}')
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        row = Row.objects.get(id=row_id, user=user)
        attr = Attribute.objects.get(name=field_name, user=user)
        attr_value = AttributeValue.objects.get(row=row, attribute=attr)
        file_data = json.loads(attr_value.value)

        print(f'file_data: {file_data}')
        
        # file_data가 리스트인 경우 file_id에 해당하는 파일 찾기
        if isinstance(file_data, list):
            if file_id:
                # file_id에 해당하는 파일 찾기
                target_file = None
                for file_info in file_data:
                    if (file_info.get('id') == file_id or 
                        file_info.get('stored_filename') == file_id or
                        file_info.get('original_filename') == file_id):
                        target_file = file_info
                        break
                
                if target_file:
                    file_info = target_file
                    print(f'찾은 파일: {file_info}')
                else:
                    print(f'file_id {file_id}에 해당하는 파일을 찾을 수 없음, 첫 번째 파일 사용')
                    if len(file_data) > 0:
                        file_info = file_data[0]
                    else:
                        return JsonResponse({'success': False, 'error': '파일 정보가 없습니다.'})
            else:
                # file_id가 없으면 첫 번째 파일 사용
                if len(file_data) > 0:
                    file_info = file_data[0]
                else:
                    return JsonResponse({'success': False, 'error': '파일 정보가 없습니다.'})
        else:
            # 단일 파일인 경우
            file_info = file_data
        
        s3_key = file_info.get('s3_key')
        if not s3_key:
            return JsonResponse({'success': False, 'error': 'S3 키가 없습니다.'})
        
        content_type = file_info.get('content_type', '')
        original_filename = file_info.get('original_filename', '')
        
        # HWP/HWPX 파일인 경우 PDF로 변환
        if (content_type in ['application/x-hwp', 'application/haansofthwp', 'application/vnd.hancom.hwp'] or
            original_filename.lower().endswith(('.hwp', '.hwpx'))):
            
            print(f"HWP/HWPX 파일 감지: {original_filename}")
            
            # LibreOffice 상태 확인
            if not check_libreoffice_status():
                return JsonResponse({'success': False, 'error': '파일 변환에 실패했습니다.'})
            
            try:
                # S3에서 파일 다운로드
                temp_file_path = download_file_from_s3_for_preview(s3_key)
                if not temp_file_path:
                    return JsonResponse({'success': False, 'error': '파일 다운로드에 실패했습니다.'})
                
                # HWP를 PDF로 변환
                pdf_path = convert_hwp_to_pdf(temp_file_path)
                if not pdf_path or not os.path.exists(pdf_path):
                    # 임시 파일 정리
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return JsonResponse({'success': False, 'error': 'HWP 파일을 PDF로 변환하는데 실패했습니다.'})
                
                # 변환된 PDF를 S3에 업로드하고 미리보기 URL 생성
                preview_url = upload_pdf_to_s3_for_preview(pdf_path, s3_key)
                
                # 임시 파일들 정리
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                if preview_url:
                    return JsonResponse({'success': True, 'preview_url': preview_url, 'converted_to_pdf': True})
                else:
                    return JsonResponse({'success': False, 'error': 'PDF 미리보기 URL 생성에 실패했습니다.'})
                    
            except Exception as e:
                # 임시 파일 정리
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if 'pdf_path' in locals() and os.path.exists(pdf_path):
                    os.remove(pdf_path)
                return JsonResponse({'success': False, 'error': f'HWP 변환 중 오류가 발생했습니다: {str(e)}'})
        
        # 기존 로직 (HWP/HWPX가 아닌 경우)
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        if (content_type == 'application/pdf' or 
            content_type.startswith('image/') or
            content_type == 'text/plain' or
            content_type == 'text/html' or
            content_type == 'text/css' or
            content_type == 'text/javascript' or
            content_type == 'application/json' or
            content_type == 'application/xml'):
            content_disposition = 'inline'
        else:
            content_disposition = 'attachment'
        signed_preview_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': content_disposition
            },
            ExpiresIn=3600
        )
        return JsonResponse({'success': True, 'preview_url': signed_preview_url})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@csrf_exempt
def update_audio_text(request):
    """
    음성파일의 변환된 텍스트를 업데이트하는 함수
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청 방법입니다.'})
    
    try:
        # 파라미터 검증
        row_id = request.POST.get('row_id')
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        converted_text = request.POST.get('converted_text', '')
        
        if not all([row_id, date, file_id]):
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 객체 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attribute = Attribute.objects.get(user=user, name='음성파일')
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        
        # AttributeValue 가져오기 또는 생성
        attr_value, created = AttributeValue.objects.get_or_create(
            row=row,
            attribute=audio_attribute,
            defaults={'value': '{}'}
        )
        
        # 기존 데이터 파싱
        try:
            audio_data = json.loads(attr_value.value) if attr_value.value else {}
        except json.JSONDecodeError:
            audio_data = {}
        
        # 해당 날짜의 파일 데이터 찾기 및 업데이트
        if file_id in audio_data.get('data', {}):
            audio_data['data'][file_id]['converted_text'] = converted_text
            
            # 데이터베이스에 저장
            attr_value.value = json.dumps(audio_data, ensure_ascii=False)
            attr_value.save()
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attribute.cascade:
                print(f"=== Cascade 동기화 시작 (update_audio_text) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(audio_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(audio_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (update_audio_text) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attribute.cascade} - 동기화하지 않음")
            
            logger.info(f"음성파일 텍스트 업데이트 성공 - Row ID: {row_id}, Date: {date}, File ID: {file_id}")
            
            return JsonResponse({
                'success': True,
                'message': '변환된 텍스트가 성공적으로 업데이트되었습니다.'
            })
        else:
            return JsonResponse({'success': False, 'error': '해당 음성파일을 찾을 수 없습니다.'})
            
    except Exception as e:
        logger.error(f"음성파일 텍스트 업데이트 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': f'서버 오류: {str(e)}'})

@csrf_exempt
def update_audio_memo(request):
    """음성파일 메모 업데이트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '허용되지 않은 메소드입니다.'})
    
    try:
        # 파라미터 가져오기
        row_id = request.POST.get('row_id')
        date = request.POST.get('date')
        file_id = request.POST.get('file_id')
        memo = request.POST.get('memo', '')
        
        if not all([row_id, date, file_id]):
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # 사용자 정보 가져오기 (고정 ID: 1)
        try:
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다.'})
        
        # Row 정보 가져오기
        try:
            row = Row.objects.get(id=row_id, user=user)
        except Row.DoesNotExist:
            return JsonResponse({'success': False, 'error': '해당 행을 찾을 수 없습니다.'})
        
        # 음성파일 속성 가져오기
        try:
            audio_attr = Attribute.objects.get(name='음성파일', user=user)
            audio_attr_value, created = AttributeValue.objects.get_or_create(
                row=row,
                attribute=audio_attr,
                defaults={'value': '{}'}
            )
        except Attribute.DoesNotExist:
            return JsonResponse({'success': False, 'error': '음성파일 속성을 찾을 수 없습니다.'})
        
        # 기존 음성파일 데이터 파싱
        try:
            audio_data = json.loads(audio_attr_value.value) if audio_attr_value.value else {}
        except (json.JSONDecodeError, TypeError):
            audio_data = {}
        
        # 해당 날짜와 파일 ID의 메모 업데이트
        if file_id in audio_data.get('data', {}):
            audio_data['data'][file_id]['memo'] = memo
            
            # 업데이트된 데이터 저장
            audio_attr_value.value = json.dumps(audio_data, ensure_ascii=False)
            audio_attr_value.save()
            
            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
            if audio_attr.cascade:
                print(f"=== Cascade 동기화 시작 (update_audio_memo) ===")
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade}")
                print(f"수정된 행 ID: {row_id}")
                print(f"새 값: {json.dumps(audio_data, ensure_ascii=False)}")
                
                synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(audio_data, ensure_ascii=False))
                if synced_count > 0:
                    print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
                else:
                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                print(f"=== Cascade 동기화 종료 (update_audio_memo) ===")
            else:
                print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade} - 동기화하지 않음")
            
            logger.info(f"음성파일 메모 업데이트 성공: Row {row_id}, Date {date}, File {file_id}")
            return JsonResponse({'success': True, 'message': '메모가 성공적으로 저장되었습니다.'})
        else:
            return JsonResponse({'success': False, 'error': '해당 음성파일을 찾을 수 없습니다.'})
            
    except Exception as e:
        logger.error(f"음성파일 메모 업데이트 오류: {str(e)}")
        return JsonResponse({'success': False, 'error': f'메모 저장 중 오류가 발생했습니다: {str(e)}'})



@csrf_exempt
def update_audio_text_notes(request):
    """
    음성파일 노트(텍스트) 추가/수정/순서변경
    POST: row_id, date, notes(JSON string: [{id, text, order}, ...])
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST만 허용'})
    try:
        row_id = request.POST.get('row_id')
        notes_json = request.POST.get('notes')
        target_date = request.POST.get('date')
        if not row_id or not notes_json or not target_date:
            return JsonResponse({'success': False, 'error': '필수 파라미터 누락'})
        notes = json.loads(notes_json)
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        row = Row.objects.get(id=row_id, user=user)
        audio_attr = Attribute.objects.get(name='음성파일', user=user)
        attr_value, _ = AttributeValue.objects.get_or_create(row=row, attribute=audio_attr, defaults={'value': '{}'})
        # 기존 데이터 파싱
        try:
            data = json.loads(attr_value.value) if attr_value.value else {}
        except:
            data = {}
        # 지정한 날짜가 없으면 생성
        if 'data' not in data:
            data['data'] = {}
        # 기존 텍스트 노트들 제거 (같은 날짜의 텍스트 타입만)
        keys_to_remove = []
        for key, value in data['data'].items():
            if isinstance(value, dict) and value.get('type') == 'text':
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del data['data'][key]
        # 새로운 텍스트 노트들 추가
        for note in notes:
            note_id = note.get('id')
            if note_id:
                # 텍스트 값이 undefined나 null인 경우 빈 문자열로 처리
                text_value = note.get('text', '')
                if text_value is None:
                    text_value = ''
                    
                data['data'][note_id] = {
                    'text': text_value,
                    'order': note.get('order', 0),
                    'type': 'text'
                }
        attr_value.value = json.dumps(data, ensure_ascii=False)
        attr_value.save()
        
        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if audio_attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_audio_text_notes) ===")
            print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(data, ensure_ascii=False)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(data, ensure_ascii=False))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_audio_text_notes) ===")
        else:
            print(f"속성 '음성파일'의 cascade 값: {audio_attr.cascade} - 동기화하지 않음")
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@csrf_exempt
def update_audio_file_order_and_notes(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})

    row_id = request.POST.get('row_id')
    notes_json = request.POST.get('notes')

    print(f"=== update_audio_file_order_and_notes 시작 ===")
    print(f"row_id: {row_id}")
    print(f"notes_json: {notes_json}")

    if not row_id:
        return JsonResponse({'success': False, 'error': 'row_id 누락'})

    try:
        notes = json.loads(notes_json or "[]")
        print(f"파싱된 notes: {notes}")

         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        row = Row.objects.get(id=row_id, user=user)
        attr = Attribute.objects.get(name="음성파일", user=user)
        attr_value = AttributeValue.objects.filter(row=row, attribute=attr).first()

        if not attr_value:
            # 최초 생성: 빈 dict으로 생성
            attr_value = AttributeValue.objects.create(row=row, attribute=attr, value='{}')

        value = json.loads(attr_value.value or "{}")
        print(f"기존 value: {value}")

        # 'data' 키가 없으면 생성
        if 'data' not in value:
            value['data'] = {}

        # 새로운 순서로 재구성된 데이터
        new_data = {}

        # 모든 아이템을 순서대로 저장
        for item in notes:
            item_id = item.get('id')
            if not item_id:
                continue
                
            print(f"처리 중인 아이템: {item}")
            
            if item.get('type') == 'text':
                # 텍스트 노트
                text_value = item.get('text', '')
                if text_value is None:
                    text_value = ''
                
                new_data[item_id] = {
                    'text': text_value,
                    'order': item.get('order', 0),
                    'type': 'text',
                    'upload_date': item.get('upload_date', '')
                }
                print(f"텍스트 노트 저장: {new_data[item_id]}")
            else:
                # 파일 (오디오, 이미지, 문서)
                # notes에서 받은 모든 파일 정보를 그대로 사용 (JS에서 이미 완전한 정보를 보냄)
                file_data = {
                    'order': item.get('order', 0),
                    'type': item.get('type', 'file'),
                    'original_filename': item.get('original_filename', ''),
                    'filename': item.get('filename', ''),
                    'stored_filename': item.get('stored_filename', ''),
                    's3_key': item.get('s3_key', ''),
                    'download_url': item.get('download_url', ''),
                    'preview_url': item.get('preview_url', ''),
                    'file_size': item.get('file_size', 0),
                    'content_type': item.get('content_type', ''),
                    'upload_time': item.get('upload_time', ''),
                    'upload_date': item.get('upload_date', ''),
                    'converted_text': item.get('converted_text', ''),
                    'memo': item.get('memo', ''),
                    'gpt_summary': item.get('gpt_summary', '')
                }
                
                # None 값들을 빈 문자열로 변환
                for key, val in file_data.items():
                    if val is None:
                        file_data[key] = ''
                
                new_data[item_id] = file_data
                print(f"파일 저장: {new_data[item_id]}")

        # 새로운 데이터로 교체
        value['data'] = new_data
        print(f"최종 저장할 value: {value}")

        attr_value.value = json.dumps(value, ensure_ascii=False)
        attr_value.save()

        # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
        if attr.cascade:
            print(f"=== Cascade 동기화 시작 (update_audio_file_order_and_notes) ===")
            print(f"속성 '음성파일'의 cascade 값: {attr.cascade}")
            print(f"수정된 행 ID: {row_id}")
            print(f"새 값: {json.dumps(value, ensure_ascii=False)}")
            
            synced_count = sync_cascade_attributes(request, row_id, '음성파일', json.dumps(value, ensure_ascii=False))
            if synced_count > 0:
                print(f"Cascade 동기화 완료: 음성파일 속성이 {synced_count}개 행에 동기화됨")
            else:
                print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
            print(f"=== Cascade 동기화 종료 (update_audio_file_order_and_notes) ===")
        else:
            print(f"속성 '음성파일'의 cascade 값: {attr.cascade} - 동기화하지 않음")

        print("=== update_audio_file_order_and_notes 완료 ===")
        return JsonResponse({'success': True})

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})