from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .models import Alarm, UserAlarm, User
from django.utils import timezone
from django.conf import settings
import os
import mimetypes
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime

def diary_board(request):
    """게시판 메인 페이지"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return render(request, 'diary/diary_board.html', {
            'error': '로그인이 필요합니다.'
        })
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return render(request, 'diary/diary_board.html', {
            'error': '사용자를 찾을 수 없습니다.'
        })
    
    # 탭 파라미터 (기본값: 공고 게시판)
    tab = request.GET.get('tab', 'announcement')
    
    context = {
        'user': user,
        'current_tab': tab,
        'error': None,
        'is_admin': user.is_admin
    }
    
    return render(request, 'diary/diary_board.html', context)

def announcement_detail_page(request, announcement_id):
    """공고 상세보기 페이지"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return render(request, 'diary/diary_board_detail.html', {
            'error': '로그인이 필요합니다.'
        })
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return render(request, 'diary/diary_board_detail.html', {
            'error': '사용자를 찾을 수 없습니다.'
        })
    
    try:
        alarm = Alarm.objects.get(id=announcement_id)
    except Alarm.DoesNotExist:
        return render(request, 'diary/diary_board_detail.html', {
            'error': '공고를 찾을 수 없습니다.'
        })
    
    # 읽음 상태 업데이트
    user_alarm, created = UserAlarm.objects.get_or_create(
        user=user,
        alarm=alarm,
        defaults={'is_read': True, 'read_at': timezone.now()}
    )
    
    if not user_alarm.is_read:
        user_alarm.is_read = True
        user_alarm.read_at = timezone.now()
        user_alarm.save()
    
    context = {
        'user': user,
        'announcement': alarm,
        'error': None
    }
    
    return render(request, 'diary/diary_board_detail.html', context)

def get_announcements(request):
    """공고 목록 API"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    alarms = Alarm.objects.all()
    
    if search_query:
        alarms = alarms.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # 정렬 (최신순)
    alarms = alarms.order_by('-created_at')
    
    # 페이지네이션
    paginator = Paginator(alarms, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 사용자의 읽음 상태 확인
    user_alarms = UserAlarm.objects.filter(user=user, alarm__in=alarms)
    read_status = {ua.alarm.id: ua.is_read for ua in user_alarms}
    
    # JSON 응답을 위한 데이터 준비
    announcements_data = []
    for alarm in page_obj:
        # 텍스트 내용 추출
        text_content = alarm.get_text_content()
        # 파일 정보
        files = alarm.get_files()
        
        announcements_data.append({
            'id': alarm.id,
            'title': alarm.title,
            'content': text_content[:100] + '...' if len(text_content) > 100 else text_content,
            'full_content': text_content,
            'files': files,
            'file_count': len(files),
            'created_at': alarm.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': read_status.get(alarm.id, False)
        })
    
    pagination_data = {
        'number': page_obj.number,
        'num_pages': page_obj.paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return JsonResponse({
        'success': True,
        'announcements': announcements_data,
        'pagination': pagination_data,
        'is_admin': user.is_admin
    })

def get_announcement_detail(request, announcement_id):
    """공고 상세보기 API"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    try:
        alarm = Alarm.objects.get(id=announcement_id)
    except Alarm.DoesNotExist:
        return JsonResponse({'success': False, 'message': '공고를 찾을 수 없습니다.'})
    
    # 읽음 상태 업데이트
    user_alarm, created = UserAlarm.objects.get_or_create(
        user=user,
        alarm=alarm,
        defaults={'is_read': True, 'read_at': timezone.now()}
    )
    
    if not user_alarm.is_read:
        user_alarm.is_read = True
        user_alarm.read_at = timezone.now()
        user_alarm.save()
    
    # 파일 정보 처리
    files = alarm.get_files()
    processed_files = []
    
    for file_info in files:
        # 파일 확장자 확인
        original_name = file_info.get('original_name', '')
        file_ext = os.path.splitext(original_name)[1].lower()
        
        # 미리보기 가능한 파일 타입
        previewable_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.txt']
        can_preview = file_ext in previewable_types
        
        processed_files.append({
            'original_name': original_name,
            'saved_name': file_info.get('saved_name', ''),
            'file_size': file_info.get('file_size', 0),
            'file_type': file_info.get('file_type', ''),
            'can_preview': can_preview,
            'file_ext': file_ext,
            'download_url': file_info.get('download_url', ''),
            'preview_url': file_info.get('preview_url', '')
        })
    
    announcement_data = {
        'id': alarm.id,
        'title': alarm.title,
        'content': alarm.get_text_content(),
        'files': processed_files,
        'created_at': alarm.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': alarm.updated_at.strftime('%Y-%m-%d %H:%M')
    }
    
    return JsonResponse({
        'success': True,
        'announcement': announcement_data
    })

@csrf_exempt
def mark_as_read(request, announcement_id):
    """공고 읽음 처리 API"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    try:
        alarm = Alarm.objects.get(id=announcement_id)
    except Alarm.DoesNotExist:
        return JsonResponse({'success': False, 'message': '공고를 찾을 수 없습니다.'})
    
    user_alarm, created = UserAlarm.objects.get_or_create(
        user=user,
        alarm=alarm,
        defaults={'is_read': True, 'read_at': timezone.now()}
    )
    
    if not user_alarm.is_read:
        user_alarm.is_read = True
        user_alarm.read_at = timezone.now()
        user_alarm.save()
    
    return JsonResponse({'success': True, 'message': '읽음 처리되었습니다.'})

def download_announcement_file(request, saved_name):
    """공고 첨부파일 다운로드 - S3 사용"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 서명된 다운로드 URL 생성 (5분 유효)
        try:
            signed_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': saved_name
                },
                ExpiresIn=300  # 5분
            )
            
            # 리다이렉트로 다운로드
            return HttpResponseRedirect(signed_url)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"S3 다운로드 실패: {error_code} - {error_message}")
            return JsonResponse({
                'success': False, 
                'message': f'파일 다운로드 중 오류가 발생했습니다: {error_message}'
            })
        except Exception as e:
            print(f"서명된 URL 생성 실패: {e}")
            return JsonResponse({
                'success': False, 
                'message': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
            })
            
    except Exception as e:
        print(f"파일 다운로드 중 오류: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
        })

def get_announcement_file_url(request, saved_name, action='download'):
    """공고 파일 URL 생성 API (다운로드/미리보기)"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 서명된 URL 생성 (5분 유효)
        try:
            params = {
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': saved_name
            }
            
            # 미리보기인 경우 inline으로 설정
            if action == 'preview':
                params['ResponseContentDisposition'] = 'inline'
            
            signed_url = s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=300  # 5분
            )
            
            return JsonResponse({
                'success': True,
                'url': signed_url
            })
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"S3 URL 생성 실패: {error_code} - {error_message}")
            return JsonResponse({
                'success': False, 
                'message': f'파일 URL 생성 중 오류가 발생했습니다: {error_message}'
            })
        except Exception as e:
            print(f"서명된 URL 생성 실패: {e}")
            return JsonResponse({
                'success': False, 
                'message': f'파일 URL 생성 중 오류가 발생했습니다: {str(e)}'
            })
            
    except Exception as e:
        print(f"파일 URL 생성 중 오류: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'파일 URL 생성 중 오류가 발생했습니다: {str(e)}'
        })

def save_uploaded_files(files):
    """업로드된 파일들을 S3에 저장하고 파일 정보를 반환"""
    saved_files = []
    
    # S3 클라이언트 생성
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    
    for uploaded_file in files:
        try:
            # 파일 확장자 추출
            file_ext = os.path.splitext(uploaded_file.name)[1]
            # 고유한 파일명 생성
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            s3_key = f"alarm_files/{unique_filename}"
            
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
                    ExpiresIn=86400  # 24시간
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
                    ExpiresIn=86400  # 24시간
                )
            except Exception as e:
                print(f"서명된 미리보기 URL 생성 실패: {e}")
                signed_preview_url = download_url
            
            # 파일 정보 저장
            file_info = {
                'original_name': uploaded_file.name,
                'saved_name': s3_key,
                'file_size': uploaded_file.size,
                'file_type': 'file', # 기본값
                'download_url': signed_download_url,
                'preview_url': signed_preview_url,
                'public_url': download_url
            }
            saved_files.append(file_info)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"S3 업로드 실패: {error_code} - {error_message}")
            # 실패한 파일은 건너뛰고 계속 진행
            continue
        except Exception as e:
            print(f"파일 업로드 중 오류: {e}")
            continue
    
    return saved_files

@csrf_exempt
def create_announcement(request):
    """공고 작성 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})
    
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    # 관리자 권한 확인
    if not user.is_admin:
        return JsonResponse({'success': False, 'message': '관리자 권한이 필요합니다.'})
    
    try:
        import json
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        files = data.get('files', [])
        
        if not title:
            return JsonResponse({'success': False, 'message': '제목을 입력해주세요.'})
        
        if not content:
            return JsonResponse({'success': False, 'message': '내용을 입력해주세요.'})
        
        # content를 dict 형태로 저장
        content_data = {
            'text': content,
            'files': files
        }
        
        # 공고 생성
        alarm = Alarm.objects.create(
            title=title,
            content=content_data
        )
        
        # 모든 사용자에게 알람 생성
        users = User.objects.all()
        for user in users:
            UserAlarm.objects.create(
                user=user,
                alarm=alarm,
                is_read=False
            )
        
        return JsonResponse({
            'success': True,
            'message': '공고가 작성되었습니다.',
            'announcement_id': alarm.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '잘못된 요청 형식입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'공고 작성 중 오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def upload_announcement_file(request):
    """공고 파일 업로드 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})
    
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    # 관리자 권한 확인
    if not user.is_admin:
        return JsonResponse({'success': False, 'message': '관리자 권한이 필요합니다.'})
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'message': '파일이 없습니다.'})
    
    uploaded_file = request.FILES['file']
    
    # 파일 크기 제한 (10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'message': '파일 크기가 너무 큽니다.'})
    
    try:
        # S3에 파일 업로드
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 파일 확장자 추출
        file_ext = os.path.splitext(uploaded_file.name)[1]
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        s3_key = f"alarm_files/{unique_filename}"
        
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
                ExpiresIn=86400  # 24시간
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
                ExpiresIn=86400  # 24시간
            )
        except Exception as e:
            print(f"서명된 미리보기 URL 생성 실패: {e}")
            signed_preview_url = download_url
        
        # 파일 정보 반환
        file_info = {
            'original_name': uploaded_file.name,
            'saved_name': s3_key,
            'file_size': uploaded_file.size,
            'file_type': 'file', # 기본값
            'download_url': signed_download_url,
            'preview_url': signed_preview_url,
            'public_url': download_url
        }
        
        return JsonResponse({
            'success': True,
            'message': '파일이 업로드되었습니다.',
            'file': file_info
        })
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"S3 업로드 실패: {error_code} - {error_message}")
        return JsonResponse({
            'success': False, 
            'message': f'파일 업로드 중 오류가 발생했습니다: {error_message}'
        })
    except Exception as e:
        print(f"파일 업로드 중 오류: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'
        })
