from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
import uuid
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
from .models import Inquiry, Alarm, UserAlarm, User
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.forms.models import model_to_dict

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
                'file_type': uploaded_file.content_type,
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

def admin_dashboard(request):
    """어드민 대시보드"""
    # 관리자 권한 확인
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if not user.is_admin:  # is_admin 필드로 권한 확인
        return redirect('login')
    
    # 최근 문의사항 5개
    recent_inquiries = Inquiry.objects.all().order_by('-created_at')[:5]
    
    # 최근 공지사항 5개
    recent_alarms = Alarm.objects.all().order_by('-created_at')[:5]
    
    # 통계
    total_inquiries = Inquiry.objects.count()
    total_alarms = Alarm.objects.count()
    unread_inquiries = Inquiry.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7)).count()
    user_count = User.objects.count()
    
    context = {
        'recent_inquiries': recent_inquiries,
        'recent_alarms': recent_alarms,
        'total_inquiries': total_inquiries,
        'total_alarms': total_alarms,
        'unread_inquiries': unread_inquiries,
        'user_count': user_count,
    }
    
    return render(request, 'diary/diary_admin.html', context)

def inquiry_list(request):
    """문의사항 목록 - JSON 응답"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    inquiries = Inquiry.objects.all()
    
    if search_query:
        inquiries = inquiries.filter(
            Q(name__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(contact__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # 정렬
    sort_by = request.GET.get('sort', '-created_at')
    inquiries = inquiries.order_by(sort_by)
    
    # 페이지네이션
    paginator = Paginator(inquiries, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # JSON 응답을 위한 데이터 준비
    inquiries_data = []
    for inquiry in page_obj:
        inquiries_data.append({
            'id': inquiry.id,
            'name': inquiry.name,
            'company_name': inquiry.company_name,
            'contact': inquiry.contact,
            'content': inquiry.content,
            'created_at': inquiry.created_at.isoformat(),
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
        'inquiries': inquiries_data,
        'pagination': pagination_data
    })

def inquiry_detail(request, inquiry_id):
    """문의사항 상세보기 - JSON 응답"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    inquiry = get_object_or_404(Inquiry, id=inquiry_id)
    
    inquiry_data = {
        'id': inquiry.id,
        'name': inquiry.name,
        'company_name': inquiry.company_name,
        'contact': inquiry.contact,
        'content': inquiry.content,
        'created_at': inquiry.created_at.isoformat(),
    }
    
    return JsonResponse({
        'success': True,
        'inquiry': inquiry_data
    })

def alarm_list(request):
    """공지사항 목록 - JSON 응답"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    alarms = Alarm.objects.all()
    
    if search_query:
        alarms = alarms.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # 정렬
    sort_by = request.GET.get('sort', '-created_at')
    alarms = alarms.order_by(sort_by)
    
    # 페이지네이션
    paginator = Paginator(alarms, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # JSON 응답을 위한 데이터 준비
    alarms_data = []
    for alarm in page_obj:
        alarms_data.append({
            'id': alarm.id,
            'title': alarm.title,
            'content': alarm.get_text_content(),
            'files': alarm.get_files(),
            'created_at': alarm.created_at.isoformat(),
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
        'alarms': alarms_data,
        'pagination': pagination_data
    })

def alarm_create(request):
    """공지사항 작성"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return redirect('login')
    
    if request.method == 'POST':
        try:
            # JSON 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                title = data.get('title')
                content_text = data.get('content')
                files_data = data.get('files', [])
            else:
                # Form 데이터 처리
                title = request.POST.get('title')
                content_text = request.POST.get('content')
                files_data = []
                
                # 파일 처리
                uploaded_files = request.FILES.getlist('files')
                if uploaded_files:
                    files_data = save_uploaded_files(uploaded_files)
        
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 form data로 시도
            title = request.POST.get('title')
            content_text = request.POST.get('content')
            files_data = []
            
            # 파일 처리
            uploaded_files = request.FILES.getlist('files')
            if uploaded_files:
                files_data = save_uploaded_files(uploaded_files)
        
        if title and content_text is not None:
            # content를 dict 형태로 저장
            content = {
                'text': content_text,
                'files': files_data
            }
            
            alarm = Alarm.objects.create(
                title=title,
                content=content
            )
            
            # 모든 사용자에게 알람 생성
            users = User.objects.all()
            for user in users:
                UserAlarm.objects.create(
                    user=user,
                    alarm=alarm,
                    is_read=False
                )
            
            return JsonResponse({'success': True, 'message': '공지사항이 성공적으로 작성되었습니다.'})
        else:
            return JsonResponse({'success': False, 'message': '제목과 내용을 모두 입력해주세요.'})
    
    return render(request, 'diary/diary_admin.html')

def alarm_edit(request, alarm_id):
    """공지사항 수정"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    alarm = get_object_or_404(Alarm, id=alarm_id)
    
    if request.method == 'POST':
        try:
            # JSON 데이터 처리
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                title = data.get('title')
                content_text = data.get('content')
                files_data = data.get('files', [])
            else:
                # Form 데이터 처리
                title = request.POST.get('title')
                content_text = request.POST.get('content')
                files_data = []
                
                # 파일 처리
                uploaded_files = request.FILES.getlist('files')
                if uploaded_files:
                    files_data = save_uploaded_files(uploaded_files)
        
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 form data로 시도
            title = request.POST.get('title')
            content_text = request.POST.get('content')
            files_data = []
            
            # 파일 처리
            uploaded_files = request.FILES.getlist('files')
            if uploaded_files:
                files_data = save_uploaded_files(uploaded_files)
        
        if title and content_text is not None:
            # 기존 파일 정보 유지 (새 파일이 업로드되지 않은 경우)
            if not files_data:
                files_data = alarm.get_files()
            
            # content를 dict 형태로 저장
            content = {
                'text': content_text,
                'files': files_data
            }
            
            alarm.title = title
            alarm.content = content
            alarm.save()
            
            return JsonResponse({'success': True, 'message': '공지사항이 성공적으로 수정되었습니다.'})
        else:
            return JsonResponse({'success': False, 'message': '제목과 내용을 모두 입력해주세요.'})
    
    # GET 요청 시 알람 정보 반환
    alarm_data = {
        'id': alarm.id,
        'title': alarm.title,
        'content': alarm.get_text_content(),
        'files': alarm.get_files(),
        'created_at': alarm.created_at.isoformat(),
    }
    
    return JsonResponse({
        'success': True,
        'alarm': alarm_data
    })

def alarm_delete(request, alarm_id):
    """공지사항 삭제"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    alarm = get_object_or_404(Alarm, id=alarm_id)
    alarm.delete()
    
    return JsonResponse({'success': True, 'message': '공지사항이 삭제되었습니다.'})

@csrf_exempt
def inquiry_delete(request, inquiry_id):
    """문의사항 삭제"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    inquiry = get_object_or_404(Inquiry, id=inquiry_id)
    inquiry.delete()
    
    return JsonResponse({'success': True, 'message': '문의사항이 삭제되었습니다.'})

@csrf_exempt
def admin_api(request):
    """어드민 API 엔드포인트"""
    user_id = request.session.get('diary_member_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    if not user.is_admin:  # 실제로는 더 안전한 권한 체크 필요
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'create_alarm':
            title = data.get('title')
            content_text = data.get('content')
            files_data = data.get('files', [])
            
            if title and content_text:
                # content를 dict 형태로 저장
                content = {
                    'text': content_text,
                    'files': files_data
                }
                
                alarm = Alarm.objects.create(
                    title=title,
                    content=content
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
                    'message': '공지사항이 성공적으로 작성되었습니다.',
                    'alarm_id': alarm.id
                })
            else:
                return JsonResponse({'success': False, 'message': '제목과 내용을 모두 입력해주세요.'})
        
        elif action == 'delete_alarm':
            alarm_id = data.get('alarm_id')
            try:
                alarm = Alarm.objects.get(id=alarm_id)
                alarm.delete()
                return JsonResponse({'success': True, 'message': '공지사항이 삭제되었습니다.'})
            except Alarm.DoesNotExist:
                return JsonResponse({'success': False, 'message': '존재하지 않는 공지사항입니다.'})
        
        elif action == 'delete_inquiry':
            inquiry_id = data.get('inquiry_id')
            try:
                inquiry = Inquiry.objects.get(id=inquiry_id)
                inquiry.delete()
                return JsonResponse({'success': True, 'message': '문의사항이 삭제되었습니다.'})
            except Inquiry.DoesNotExist:
                return JsonResponse({'success': False, 'message': '존재하지 않는 문의사항입니다.'})
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
