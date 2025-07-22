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
        
        # 파일 크기 제한 (100MB)
        max_file_size = 1024 * 1024 * 1024  # 100MB
        if audio_file.size > max_file_size:
            return JsonResponse({
                'success': False,
                'error': '파일 크기가 1GB를 초과합니다.'
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
            attr_value = AttributeValue.objects.get(row=row, attribute=audio_attribute)
            current_data = json.loads(attr_value.value) if attr_value.value else {}
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
            attr_value = AttributeValue.objects.get(row=row, attribute=audio_attribute)
            current_data = json.loads(attr_value.value) if attr_value.value else {}
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