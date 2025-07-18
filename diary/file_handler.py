from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from .models import DiaryEntry, Category, Region, SalesStatus, BaseAttribute, Attribute, AttributeValue, User, DropdownAttribute, Row, AttributeType
from django.db import models
import boto3
from django.conf import settings
import uuid
import os
from botocore.exceptions import ClientError
from datetime import datetime
import json
import logging
from django.http import JsonResponse
from .cascade_handlers import sync_cascade_attributes

logger = logging.getLogger(__name__)

@csrf_exempt
def upload_file(request):
    """파일 업로드 및 S3 저장 (여러 파일 지원)"""
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        field_name = request.POST.get('field_name')
        uploaded_file = request.FILES.get('file')
        
        if not row_id or not field_name:
            return JsonResponse({
                'success': False,
                'error': 'Row ID와 Field Name이 필요합니다.'
            })
        
        if uploaded_file:
            print(f"파일명: {uploaded_file.name}")
            
            try:
                # Row와 Attribute 가져오기
                 
                user_id = request.session.get('diary_member_id')

                user = User.objects.get(id=user_id)
                row = Row.objects.get(id=row_id, user=user)
                attribute = Attribute.objects.get(name=field_name, user=user)
                
                # 속성이 file 타입인지 확인
                if not attribute.attributeType or attribute.attributeType.name != 'file':
                    return JsonResponse({
                        'success': False,
                        'error': '파일 타입 속성이 아닙니다.'
                    })
                
                # S3 클라이언트 생성
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # 파일명 생성 (중복 방지를 위해 UUID 사용)
                file_extension = os.path.splitext(uploaded_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                s3_key = f"{settings.AWS_LOCATION}/{unique_filename}"
                
                # S3에 파일 업로드
                s3_client.upload_fileobj(
                    uploaded_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': uploaded_file.content_type,
                        'ContentDisposition': f'attachment; filename="{uploaded_file.name}"'
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
                except Exception as e:
                    print(f"서명된 미리보기 URL 생성 실패: {e}")
                    signed_preview_url = download_url
                
                # 파일 타입 결정 (확장자와 content_type 기반)
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                content_type = uploaded_file.content_type or ''
                
                # 파일 타입 분류
                file_type = 'file'  # 기본값
                if content_type.startswith('image/'):
                    file_type = 'img'
                elif content_type == 'application/pdf':
                    file_type = 'pdf'
                elif content_type.startswith('audio/'):
                    file_type = 'audio'
                elif content_type.startswith('video/'):
                    file_type = 'video'
                elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    file_type = 'img'
                elif file_extension == '.pdf':
                    file_type = 'pdf'
                elif file_extension in ['.mp3', '.wav', '.ogg', '.m4a']:
                    file_type = 'audio'
                elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
                    file_type = 'video'
                
                # 새 파일 정보
                new_file_data = {
                    'original_filename': uploaded_file.name,
                    'stored_filename': unique_filename,
                    's3_key': s3_key,
                    'download_url': signed_download_url,
                    'preview_url': signed_preview_url,
                    'public_url': download_url,
                    'file_size': uploaded_file.size,
                    'content_type': uploaded_file.content_type,
                    'type': file_type,  # 파일 타입 추가
                    'upload_time': datetime.now().isoformat()  # 업로드 시간 추가
                }
                
                # AttributeValue에서 기존 파일 정보 가져오기
                attr_value, created = AttributeValue.objects.get_or_create(
                    row=row,
                    attribute=attribute,
                    defaults={'value': '[]'}  # 빈 배열로 초기화
                )
                
                # 기존 파일 목록 파싱
                try:
                    if attr_value.value and attr_value.value.strip():
                        existing_files = json.loads(attr_value.value)
                        if not isinstance(existing_files, list):
                            # 기존이 단일 파일인 경우 배열로 변환
                            existing_files = [existing_files] if existing_files else []
                    else:
                        existing_files = []
                except (json.JSONDecodeError, TypeError):
                    existing_files = []
                
                # 새 파일을 배열에 추가
                existing_files.append(new_file_data)
                
                # 업데이트된 파일 목록을 데이터베이스에 저장
                updated_value = json.dumps(existing_files, ensure_ascii=False)
                attr_value.value = updated_value
                attr_value.save()
                
                # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
                if attribute.cascade:
                    print(f"=== Cascade 동기화 시작 (upload_file) ===")
                    print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade}")
                    print(f"수정된 행 ID: {row_id}")
                    print(f"새 값: {updated_value}")
                    
                    synced_count = sync_cascade_attributes(request, row_id, field_name, updated_value)
                    if synced_count > 0:
                        print(f"Cascade 동기화 완료: {field_name} 속성이 {synced_count}개 행에 동기화됨")
                    else:
                        print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                    print(f"=== Cascade 동기화 종료 (upload_file) ===")
                else:
                    print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade} - 동기화하지 않음")
                
                return JsonResponse({
                    'success': True,
                    'message': f'파일 "{uploaded_file.name}"이 성공적으로 업로드되었습니다.',
                    'file_info': new_file_data,
                    'total_files': len(existing_files)
                })
                
            except Row.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '해당 행을 찾을 수 없습니다.'
                })
            except Attribute.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '해당 속성을 찾을 수 없습니다.'
                })
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                print(f"=== S3 업로드 실패 ===")
                print(f"에러 코드: {error_code}")
                print(f"에러 메시지: {error_message}")
                
                return JsonResponse({
                    'success': False,
                    'error': f'S3 업로드 실패: {error_message}'
                })
                
            except Exception as e:
                print(f"=== 예상치 못한 오류 ===")
                print(f"오류: {str(e)}")
                
                return JsonResponse({
                    'success': False,
                    'error': f'파일 업로드 중 오류 발생: {str(e)}'
                })
        else:
            print("업로드된 파일이 없습니다.")
            return JsonResponse({
                'success': False,
                'error': '업로드된 파일이 없습니다.'
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'POST 요청만 허용됩니다.'
        })

@csrf_exempt
def delete_file(request):
    """파일 삭제 (여러 파일 지원)"""
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        field_name = request.POST.get('field_name')
        file_index = request.POST.get('file_index')  # 삭제할 파일의 인덱스
        
        # 필수 파라미터 검증
        if not row_id or not field_name:
            return JsonResponse({
                'success': False,
                'error': 'row_id와 field_name이 필요합니다.'
            })
        
        try:
            # 사용자 ID를 1로 고정
             
            user_id = request.session.get('diary_member_id')

            user = User.objects.get(id=user_id)
            
            # Row와 Attribute 조회
            row = Row.objects.get(id=row_id, user=user)
            attribute = Attribute.objects.get(name=field_name, user=user)
            
            # 파일 타입 속성인지 확인
            if attribute.attributeType.name != 'file':
                return JsonResponse({
                    'success': False,
                    'error': '파일 타입이 아닙니다.'
                })
            
            # AttributeValue 조회
            try:
                attribute_value = AttributeValue.objects.get(row=row, attribute=attribute)
                
                # 파일 정보 파싱
                if attribute_value.value:
                    try:
                        files_data = json.loads(attribute_value.value)
                        
                        # 단일 파일인 경우 배열로 변환
                        if not isinstance(files_data, list):
                            files_data = [files_data] if files_data else []
                        
                        if not files_data:
                            return JsonResponse({
                                'success': False,
                                'error': '삭제할 파일이 없습니다.'
                            })
                        
                        # file_index가 제공된 경우 특정 파일 삭제
                        if file_index is not None:
                            try:
                                file_index = int(file_index)
                                
                                if file_index < 0 or file_index >= len(files_data):
                                    return JsonResponse({
                                        'success': False,
                                        'error': f'유효하지 않은 파일 인덱스입니다. (인덱스: {file_index}, 파일 수: {len(files_data)})'
                                    })
                                
                                # 삭제할 파일 정보
                                file_to_delete = files_data[file_index]
                                s3_key = file_to_delete.get('s3_key')
                                original_filename = file_to_delete.get('original_filename', 'unknown')
                                
                                # S3에서 파일 삭제
                                if s3_key:
                                    try:
                                        s3_client = boto3.client(
                                            's3',
                                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                            region_name=settings.AWS_S3_REGION_NAME
                                        )
                                        
                                        s3_client.delete_object(
                                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                            Key=s3_key
                                        )
                                        
                                    except ClientError as e:
                                        print(f"S3 파일 삭제 실패: {e}")
                                        # S3 삭제 실패해도 계속 진행
                                
                                # 배열에서 해당 파일 제거
                                files_data.pop(file_index)
                                
                                # 남은 파일이 있으면 업데이트, 없으면 삭제
                                if files_data:
                                    updated_value = json.dumps(files_data, ensure_ascii=False)
                                    attribute_value.value = updated_value
                                    attribute_value.save()
                                    
                                    # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
                                    if attribute.cascade:
                                        print(f"=== Cascade 동기화 시작 (delete_file - 특정 파일) ===")
                                        print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade}")
                                        print(f"수정된 행 ID: {row_id}")
                                        print(f"새 값: {updated_value}")
                                        
                                        synced_count = sync_cascade_attributes(request, row_id, field_name, updated_value)
                                        if synced_count > 0:
                                            print(f"Cascade 동기화 완료: {field_name} 속성이 {synced_count}개 행에 동기화됨")
                                        else:
                                            print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                                        print(f"=== Cascade 동기화 종료 (delete_file - 특정 파일) ===")
                                    else:
                                        print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade} - 동기화하지 않음")
                                else:
                                    attribute_value.delete()
                                    
                                    # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
                                    if attribute.cascade:
                                        print(f"=== Cascade 동기화 시작 (delete_file - 모든 파일 삭제) ===")
                                        print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade}")
                                        print(f"수정된 행 ID: {row_id}")
                                        print(f"새 값: ''")
                                        
                                        synced_count = sync_cascade_attributes(request, row_id, field_name, '')
                                        if synced_count > 0:
                                            print(f"Cascade 동기화 완료: {field_name} 속성이 {synced_count}개 행에 동기화됨")
                                        else:
                                            print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                                        print(f"=== Cascade 동기화 종료 (delete_file - 모든 파일 삭제) ===")
                                    else:
                                        print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade} - 동기화하지 않음")
                                
                                return JsonResponse({
                                    'success': True,
                                    'message': f'파일 "{original_filename}"이(가) 성공적으로 삭제되었습니다.',
                                    'remaining_files': len(files_data)
                                })
                                
                            except ValueError as e:
                                print(f"ValueError converting file_index: {e}")
                                return JsonResponse({
                                    'success': False,
                                    'error': '유효하지 않은 파일 인덱스입니다.'
                                })
                        else:
                            print("No file_index provided, deleting all files")
                            # file_index가 없으면 모든 파일 삭제 (기존 동작)
                            for file_data in files_data:
                                s3_key = file_data.get('s3_key')
                                if s3_key:
                                    try:
                                        s3_client = boto3.client(
                                            's3',
                                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                            region_name=settings.AWS_S3_REGION_NAME
                                        )
                                        
                                        s3_client.delete_object(
                                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                            Key=s3_key
                                        )
                                        
                                    except ClientError as e:
                                        print(f"S3 파일 삭제 실패: {e}")
                            
                            # AttributeValue 삭제
                            attribute_value.delete()
                            
                            # Cascade 기능: cascade가 true인 속성이 수정되면 원본 행과 복제된 행들을 동기화
                            if attribute.cascade:
                                print(f"=== Cascade 동기화 시작 (delete_file - 모든 파일) ===")
                                print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade}")
                                print(f"수정된 행 ID: {row_id}")
                                print(f"새 값: ''")
                                
                                synced_count = sync_cascade_attributes(request, row_id, field_name, '')
                                if synced_count > 0:
                                    print(f"Cascade 동기화 완료: {field_name} 속성이 {synced_count}개 행에 동기화됨")
                                else:
                                    print(f"Cascade 동기화 실패 또는 동기화할 행이 없음")
                                print(f"=== Cascade 동기화 종료 (delete_file - 모든 파일) ===")
                            else:
                                print(f"속성 '{field_name}'의 cascade 값: {attribute.cascade} - 동기화하지 않음")
                            
                            return JsonResponse({
                                'success': True,
                                'message': '모든 파일이 성공적으로 삭제되었습니다.'
                            })
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        return JsonResponse({
                            'success': False,
                            'error': '파일 정보를 파싱할 수 없습니다.'
                        })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': '파일 정보가 없습니다.'
                    })
                    
            except AttributeValue.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '삭제할 파일이 없습니다.'
                })
                
        except Row.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 행을 찾을 수 없습니다.'
            })
        except Attribute.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '해당 속성을 찾을 수 없습니다.'
            })
        except Exception as e:
            print(f"파일 삭제 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'POST 요청만 허용됩니다.'
    })

@require_GET
def download_file(request, row_id, field_name):
    """S3에 저장된 파일을 다운로드하는 뷰"""
    try:
        # 사용자 ID를 1로 고정 (이미 import된 User 모델 사용)
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        
        # Row와 Attribute 조회
        row = Row.objects.get(id=row_id, user=user)
        attribute = Attribute.objects.get(name=field_name, user=user)
        
        # AttributeValue 조회
        try:
            attribute_value = AttributeValue.objects.get(row=row, attribute=attribute)
            
            if attribute_value.value:
                try:
                    file_info = json.loads(attribute_value.value)
                    s3_key = file_info.get('s3_key')
                    original_filename = file_info.get('original_filename', 'download')
                    existing_download_url = file_info.get('download_url')
                    
                    if s3_key:
                        # 항상 새로운 서명된 다운로드 URL 생성 (1시간 유효)
                        s3_client = boto3.client(
                            's3',
                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME
                        )
                        
                        try:
                            signed_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={
                                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                    'Key': s3_key
                                },
                                ExpiresIn=300  # 5분
                            )
                            
                            # 리다이렉트로 다운로드
                            from django.http import HttpResponseRedirect
                            return HttpResponseRedirect(signed_url)
                            
                        except Exception as e:
                            print(f"서명된 URL 생성 실패: {e}")
                            # 서명된 URL 생성 실패 시 기존 URL 사용
                            if existing_download_url:
                                from django.http import HttpResponseRedirect
                                return HttpResponseRedirect(existing_download_url)
                            else:
                                return JsonResponse({
                                    'success': False,
                                    'error': '다운로드 URL 생성에 실패했습니다.'
                                })
                        
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'S3 키가 없습니다.'
                        })
                        
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': '파일 정보를 파싱할 수 없습니다.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '파일 정보가 없습니다.'
                })
                
        except AttributeValue.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '파일이 존재하지 않습니다.'
            })
                
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '사용자를 찾을 수 없습니다.'
        })
    except Row.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 행을 찾을 수 없습니다.'
        })
    except Attribute.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '해당 속성을 찾을 수 없습니다.'
        })
    except Exception as e:
        print(f"파일 다운로드 중 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
        })
    
