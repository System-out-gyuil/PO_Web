from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import User, Board, NomalBoardCategory
import json

@csrf_exempt
def board_list_view(request):
    """게시판 목록 페이지"""
    if not request.session.get('diary_authenticated'):
        return redirect('login')
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect('login')
    
    context = {
        'is_authenticated': True,
        'is_admin': user.is_admin,
        'user': user,
    }
    
    return render(request, 'diary/board_list.html', context)
        
@csrf_exempt
def board_list_api(request):
    """게시판 목록 API - 본인이 작성한 게시글만 조회"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    try:
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '').strip()
        category_id = request.GET.get('category', None)  # category_id로 변경
        
        # 본인이 작성한 게시글만 조회
        boards = Board.objects.filter(author=user)
        
        # 카테고리별 필터링
        if category_id and category_id != 'all':
            try:
                category = NomalBoardCategory.objects.get(id=category_id, user=user)
                boards = boards.filter(category=category)
            except NomalBoardCategory.DoesNotExist:
                pass
        
        # 검색어가 있으면 필터링
        if search:
            boards = boards.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        
        # 페이지네이션
        paginator = Paginator(boards, 10)  # 페이지당 10개
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # 게시글 데이터 준비
        board_list = []
        for board in page_obj:
            board_data = {
                'id': board.id,
                'title': board.title,
                'content': board.content,
                'author_name': board.author.name,
                'category_id': board.category.id if board.category else None,  # 카테고리 ID 추가
                'category_name': board.category.category_name if board.category else '일반',  # 카테고리명 추가
                'files': board.files or [],
                'created_at': board.created_at.isoformat(),
                'updated_at': board.updated_at.isoformat(),
            }
            board_list.append(board_data)
        
        # 페이지네이션 정보
        pagination_data = {
            'number': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        }
        
        return JsonResponse({
            'success': True,
            'boards': board_list,
            'pagination': pagination_data,
            'category_id': category_id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'게시글을 불러오는데 실패했습니다: {str(e)}'
        })

@csrf_exempt
def board_create(request):
    """게시글 작성"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '사용자를 찾을 수 없습니다.'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            category_id = data.get('category_id', None)  # category_id로 변경
            files = data.get('files', [])
            
            if not title:
                return JsonResponse({'success': False, 'message': '제목을 입력해주세요.'})
            
            if not content:
                return JsonResponse({'success': False, 'message': '내용을 입력해주세요.'})
            
            # 카테고리 확인
            category = None
            if category_id:
                try:
                    category = NomalBoardCategory.objects.get(id=category_id, user=user)
                except NomalBoardCategory.DoesNotExist:
                    return JsonResponse({'success': False, 'message': '유효하지 않은 카테고리입니다.'})
            
            # 게시글 생성
            board = Board.objects.create(
                title=title,
                content=content,
                author=user,
                category=category,  # 카테고리 FK 설정
                files=files
            )
            
            return JsonResponse({
                'success': True,
                'message': '게시글이 작성되었습니다.',
                'board_id': board.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'게시글 작성에 실패했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

@csrf_exempt
def board_detail_view(request, board_id):
    """게시글 상세 페이지 - 본인이 작성한 게시글만 조회 가능"""
    if not request.session.get('diary_authenticated'):
        return redirect('login')
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        # 본인이 작성한 게시글만 조회 가능
        board = Board.objects.get(id=board_id, author=user)
    except (User.DoesNotExist, Board.DoesNotExist):
        return redirect('board_list')
    
    context = {
        'is_authenticated': True,
        'is_admin': user.is_admin,
        'user': user,
        'board': board,
    }
    
    return render(request, 'diary/board_detail.html', context)

@csrf_exempt
def board_detail_api(request, board_id):
    """게시글 상세 API - 본인이 작성한 게시글만 조회 가능"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
        # 본인이 작성한 게시글만 조회 가능
        board = Board.objects.get(id=board_id, author=user)
        
        board_data = {
            'id': board.id,
            'title': board.title,
            'content': board.content,
            'author_name': board.author.name,
            'category_id': board.category.id if board.category else None,  # 카테고리 ID 추가
            'category_name': board.category.category_name if board.category else '일반',  # 카테고리명 추가
            'files': board.files or [],
            'created_at': board.created_at.isoformat(),
            'updated_at': board.updated_at.isoformat(),
        }
        
        return JsonResponse({
            'success': True,
            'board': board_data
        })
        
    except (User.DoesNotExist, Board.DoesNotExist):
        return JsonResponse({'success': False, 'message': '게시글을 찾을 수 없습니다.'})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'게시글을 불러오는데 실패했습니다: {str(e)}'
        })

@csrf_exempt
def board_edit(request, board_id):
    """게시글 수정 API - 본인이 작성한 게시글만 수정 가능"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
        # 본인이 작성한 게시글만 수정 가능
        board = Board.objects.get(id=board_id, author=user)
    except (User.DoesNotExist, Board.DoesNotExist):
        return JsonResponse({'success': False, 'message': '게시글을 찾을 수 없습니다.'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            category_id = data.get('category_id', None)  # 카테고리 ID 추가
            files = data.get('files', [])
            
            if not title:
                return JsonResponse({'success': False, 'message': '제목을 입력해주세요.'})
            
            if not content:
                return JsonResponse({'success': False, 'message': '내용을 입력해주세요.'})
            
            # 카테고리 확인
            category = None
            if category_id:
                try:
                    category = NomalBoardCategory.objects.get(id=category_id, user=user)
                except NomalBoardCategory.DoesNotExist:
                    return JsonResponse({'success': False, 'message': '유효하지 않은 카테고리입니다.'})
            
            # 게시글 수정
            board.title = title
            board.content = content
            board.category = category  # 카테고리 변경 추가
            board.files = files
            board.save()
            
            return JsonResponse({
                'success': True,
                'message': '게시글이 수정되었습니다.',
                'board_id': board.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'게시글 수정에 실패했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

@csrf_exempt
def board_delete(request, board_id):
    """게시글 삭제 API - 본인이 작성한 게시글만 삭제 가능"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
        # 본인이 작성한 게시글만 삭제 가능
        board = Board.objects.get(id=board_id, author=user)
    except (User.DoesNotExist, Board.DoesNotExist):
        return JsonResponse({'success': False, 'message': '게시글을 찾을 수 없습니다.'})
    
    if request.method == 'POST':
        try:
            # 게시글 삭제
            board.delete()
            
            return JsonResponse({
                'success': True,
                'message': '게시글이 삭제되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'게시글 삭제에 실패했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

@csrf_exempt
def board_file_upload(request):
    """게시판 파일 업로드"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return JsonResponse({'success': False, 'message': '파일이 선택되지 않았습니다.'})
            
            # 파일 크기 제한 (10MB)
            if uploaded_file.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'message': '파일 크기는 10MB를 초과할 수 없습니다.'})
            
            import uuid
            import os
            from django.conf import settings
            import boto3
            
            # 고유한 파일명 생성
            file_ext = os.path.splitext(uploaded_file.name)[1]
            saved_name = f"board/{uuid.uuid4()}{file_ext}"
            
            # S3에 업로드
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            s3_client.upload_fileobj(
                uploaded_file,
                settings.AWS_STORAGE_BUCKET_NAME,
                saved_name,
                ExtraArgs={'ContentType': uploaded_file.content_type}
            )
            
            # 파일 정보 반환
            file_info = {
                'original_name': uploaded_file.name,
                'saved_name': saved_name,
                'file_size': uploaded_file.size,
                'file_type': uploaded_file.content_type,
                's3_key': saved_name,
            }
            
            return JsonResponse({
                'success': True,
                'file': file_info
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'파일 업로드에 실패했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

@csrf_exempt
def board_file_preview(request, saved_name):
    """게시판 파일 미리보기"""
    print(f"=== board_file_preview 시작 ===")
    print(f"원본 saved_name: {saved_name}")
    
    # board/ 접두사가 없으면 추가
    if not saved_name.startswith('board/'):
        saved_name = f"board/{saved_name}"
        print(f"board/ 접두사 추가됨: {saved_name}")
    
    print(f"최종 saved_name: {saved_name}")
    print(f"session diary_authenticated: {request.session.get('diary_authenticated')}")
    
    if not request.session.get('diary_authenticated'):
        print("로그인 필요")
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        from django.conf import settings
        import boto3
        import os
        from .audio_handler import download_file_from_s3_for_preview, convert_hwp_to_pdf
        
        print(f"AWS 설정 확인: BUCKET={settings.AWS_STORAGE_BUCKET_NAME}, REGION={settings.AWS_S3_REGION_NAME}")
        
        # S3에서 파일 가져오기
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 파일 확장자 확인
        file_ext = os.path.splitext(saved_name)[1].lower()
        print(f"파일 확장자: {file_ext}")
        
        # HWP 파일인 경우 PDF로 변환
        if file_ext == '.hwp':
            print("HWP 파일 감지, PDF 변환 시도")
            
            # PDF 변환된 파일이 있는지 확인
            pdf_key = saved_name.replace('.hwp', '_converted.pdf')
            try:
                s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=pdf_key)
                saved_name = pdf_key  # PDF 파일 사용
                print(f"기존 PDF 파일 사용: {pdf_key}")
            except:
                # PDF 변환 수행
                print("PDF 변환 수행")
                try:
                    import tempfile
                    import os
                    
                    # S3에서 HWP 파일 다운로드 (board/ 접두사 포함)
                    print(f"HWP 파일 다운로드 시도: {saved_name}")
                    temp_hwp = download_file_from_s3_for_preview(saved_name)
                    if temp_hwp:
                        print(f"HWP 파일 다운로드 성공: {temp_hwp}")
                        
                        # 기존 convert_hwp_to_pdf 함수 사용
                        temp_pdf = convert_hwp_to_pdf(temp_hwp)
                        if temp_pdf:
                            print(f"PDF 변환 성공: {temp_pdf}")
                            
                            # 변환된 PDF를 S3에 직접 업로드
                            pdf_s3_key = f"converted_pdfs/board_{os.path.basename(saved_name).replace('.hwp', '')}_{os.path.basename(temp_pdf)}"
                            
                            print(f"PDF S3 업로드 시도: {pdf_s3_key}")
                            
                            with open(temp_pdf, 'rb') as pdf_file:
                                s3_client.upload_fileobj(
                                    pdf_file,
                                    settings.AWS_STORAGE_BUCKET_NAME,
                                    pdf_s3_key,
                                    ExtraArgs={'ContentType': 'application/pdf'}
                                )
                            
                            saved_name = pdf_s3_key
                            print(f"PDF 변환 및 업로드 성공: {pdf_s3_key}")
                            
                            # 임시 파일 정리
                            os.unlink(temp_pdf)
                        else:
                            print("PDF 변환 실패")
                            raise Exception("PDF conversion failed")
                        
                        # 임시 파일 정리
                        os.unlink(temp_hwp)
                    else:
                        print("HWP 파일 다운로드 실패")
                        raise Exception("HWP file download failed")
                        
                except Exception as e:
                    print(f"HWP to PDF conversion failed: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': f'HWP 파일을 PDF로 변환하는데 실패했습니다: {str(e)}'
                    })
        else:
            print(f"{file_ext} 파일은 변환 없이 직접 처리")
        
        print(f"최종 saved_name: {saved_name}")
        
        # S3에서 파일 존재 여부 확인
        try:
            s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=saved_name)
            print(f"S3에서 파일 확인됨: {saved_name}")
        except Exception as e:
            print(f"S3에서 파일을 찾을 수 없음: {saved_name}, 오류: {e}")
            return JsonResponse({
                'success': False,
                'message': f'파일을 찾을 수 없습니다: {saved_name}'
            })
        
        # 파일 URL 생성
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': saved_name},
            ExpiresIn=3600  # 1시간
        )
        
        print(f"생성된 presigned_url: {presigned_url[:100]}...")
        
        response_data = {
            'success': True,
            'preview_url': presigned_url
        }
        print(f"응답 데이터: {response_data}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'파일 미리보기에 실패했습니다: {str(e)}'
        })

@csrf_exempt
def board_file_download(request, saved_name):
    """게시판 파일 다운로드"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        from django.conf import settings
        import boto3
        
        # S3에서 파일 URL 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # 원본 파일명 찾기 (Board 모델에서 검색)
        original_name = saved_name.split('/')[-1]  # 기본값
        
        try:
            # 게시글에서 파일 정보 찾기
            for board in Board.objects.all():
                if board.files:
                    for file_info in board.files:
                        if file_info.get('saved_name') == saved_name:
                            original_name = file_info.get('original_name', original_name)
                            break
        except:
            pass
        
        # 다운로드 URL 생성
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': saved_name,
                'ResponseContentDisposition': f'attachment; filename="{original_name}"'
            },
            ExpiresIn=3600  # 1시간
        )
        
        return JsonResponse({
            'success': True,
            'download_url': download_url
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'파일 다운로드에 실패했습니다: {str(e)}'
        })

@csrf_exempt
def board_categories_api(request):
    """게시판 카테고리 목록 API"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    user_id = request.session.get('diary_member_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        user = User.objects.get(id=user_id)
        
        # 사용자의 모든 카테고리 조회
        categories = NomalBoardCategory.objects.filter(user=user).order_by('created_at')

        for category in categories:
            print(category.category_name)
        
        # 기본 카테고리가 없으면 생성
        if not categories.exists():
            default_categories = ['일반']
            for cat_name in default_categories:
                NomalBoardCategory.objects.create(user=user, category_name=cat_name)
            categories = NomalBoardCategory.objects.filter(user=user).order_by('created_at')
        
        category_list = []
        for category in categories:
            category_list.append({
                'id': category.id,
                'name': category.category_name
            })
        
        return JsonResponse({
            'success': True,
            'categories': category_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'카테고리를 불러오는데 실패했습니다: {str(e)}'
        })

@csrf_exempt
def board_add_category(request):
    """새 카테고리 추가 API"""
    if not request.session.get('diary_authenticated'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_category_name = data.get('category', '').strip()
            
            if not new_category_name:
                return JsonResponse({'success': False, 'message': '카테고리명을 입력해주세요.'})
            
            # 카테고리명 길이 제한
            if len(new_category_name) > 50:
                return JsonResponse({'success': False, 'message': '카테고리명은 50자 이하여야 합니다.'})
            
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 중복 카테고리명 확인
            if NomalBoardCategory.objects.filter(user=user, category_name=new_category_name).exists():
                return JsonResponse({'success': False, 'message': '이미 존재하는 카테고리명입니다.'})
            
            # 새 카테고리 생성
            new_category = NomalBoardCategory.objects.create(
                user=user,
                category_name=new_category_name
            )
            
            return JsonResponse({
                'success': True,
                'message': '새 카테고리가 추가되었습니다.',
                'category': {
                    'id': new_category.id,
                    'name': new_category.category_name
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'카테고리 추가에 실패했습니다: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})