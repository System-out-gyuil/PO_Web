import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess
from .audio_handler import check_libreoffice_status
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def convert_hwp_to_pdf(request):
    """HWP 파일을 LibreOffice를 사용하여 PDF로 변환하는 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        logger.info("=== HWP to PDF 변환 시작 ===")
        data = json.loads(request.body)
        row_id = data.get('row_id')
        field_name = data.get('field_name')
        file_id = data.get('file_id')
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        saved_name = data.get('saved_name')  # 게시판 파일용
        
        logger.info(f"요청 데이터: row_id={row_id}, field_name={field_name}, file_id={file_id}, file_name={file_name}")
        
        # 파일 URL에서 파일 다운로드
        import requests
        import tempfile
        import os
        
        try:
            # 파일 다운로드
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # 임시 디렉토리에 HWP 파일 저장
            with tempfile.TemporaryDirectory() as temp_dir:
                hwp_path = os.path.join(temp_dir, file_name)
                with open(hwp_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"HWP 파일 다운로드 완료: {hwp_path}")
                
                # LibreOffice로 PDF 변환
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, hwp_path
                ]
                
                logger.info(f"LibreOffice 명령어: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10분 타임아웃
                )
                
                logger.info(f"LibreOffice 변환 결과: returncode={result.returncode}")
                logger.info(f"LibreOffice stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"LibreOffice stderr: {result.stderr}")
                
                # 변환된 PDF 파일 확인
                pdf_name = os.path.splitext(file_name)[0] + '.pdf'
                pdf_path = os.path.join(temp_dir, pdf_name)
                
                if os.path.exists(pdf_path):
                    # PDF 파일을 S3에 업로드
                    from django.conf import settings
                    import boto3
                    
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.AWS_S3_REGION_NAME
                    )
                    
                    # S3 키 생성
                    pdf_s3_key = f"converted_pdfs/{file_id}_{pdf_name}"
                    
                    # PDF 파일을 S3에 업로드
                    with open(pdf_path, 'rb') as pdf_file:
                        s3_client.upload_fileobj(
                            pdf_file,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            pdf_s3_key,
                            ExtraArgs={'ContentType': 'application/pdf'}
                        )
                    
                    # S3 URL 생성
                    pdf_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{pdf_s3_key}"
                    
                    logger.info(f"PDF 변환 및 업로드 성공: {pdf_url}")
                    
                    return JsonResponse({
                        'success': True,
                        'pdf_url': pdf_url,
                        'message': 'HWP 파일이 PDF로 성공적으로 변환되었습니다.'
                    })
                else:
                    logger.error(f"PDF 변환 실패: {pdf_path} 파일이 존재하지 않습니다.")
                    return JsonResponse({
                        'success': False,
                        'error': 'HWP 파일 변환에 실패했습니다.',
                        'original_file_url': file_url,
                        'suggest_download': True,
                        'message': 'LibreOffice가 HWP 파일을 변환할 수 없습니다. 원본 파일을 다운로드하여 사용해주세요.'
                    })
                    
        except requests.RequestException as e:
            logger.error(f"파일 다운로드 실패: {e}")
            return JsonResponse({
                'success': False,
                'error': f'파일 다운로드 실패: {str(e)}',
                'original_file_url': file_url,
                'suggest_download': True,
                'message': '파일을 다운로드할 수 없습니다.'
            })
        except subprocess.TimeoutExpired:
            logger.error("LibreOffice 변환 타임아웃")
            return JsonResponse({
                'success': False,
                'error': '변환 시간이 초과되었습니다.',
                'original_file_url': file_url,
                'suggest_download': True,
                'message': '변환에 시간이 너무 오래 걸립니다. 원본 파일을 다운로드하여 사용해주세요.'
            })
        except Exception as e:
            logger.error(f"HWP 변환 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'변환 중 오류가 발생했습니다: {str(e)}',
                'original_file_url': file_url,
                'suggest_download': True,
                'message': '변환 중 오류가 발생했습니다. 원본 파일을 다운로드하여 사용해주세요.'
            })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return JsonResponse({'success': False, 'error': f'요청 데이터 파싱 오류: {str(e)}'})
    except Exception as e:
        logger.error(f"convert_hwp_to_pdf 함수에서 예상치 못한 오류: {e}")
        return JsonResponse({'success': False, 'error': f'오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def convert_hwp_to_pdf_board(request):
    """게시판용 HWP 파일을 LibreOffice를 사용하여 PDF로 변환하는 엔드포인트"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        logger.info("=== 게시판 HWP to PDF 변환 시작 ===")
        data = json.loads(request.body)
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        saved_name = data.get('saved_name')
        
        logger.info(f"게시판 요청 데이터: file_name={file_name}, saved_name={saved_name}")
        
        if not file_url or not file_name:
            return JsonResponse({'success': False, 'error': '필수 파라미터가 누락되었습니다.'})
        
        # LibreOffice 상태 확인
        if not check_libreoffice_status():
            return JsonResponse({'success': False, 'error': '파일 변환에 실패했습니다.'})
        
        # 파일 URL에서 파일 다운로드
        import requests
        import tempfile
        import os
        
        try:
            # 파일 다운로드
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            
            # 임시 디렉토리에 HWP 파일 저장
            with tempfile.TemporaryDirectory() as temp_dir:
                hwp_path = os.path.join(temp_dir, file_name)
                with open(hwp_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"게시판 HWP 파일 다운로드 완료: {hwp_path}")
                
                # LibreOffice로 PDF 변환
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, hwp_path
                ]
                
                logger.info(f"게시판 LibreOffice 명령어: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10분 타임아웃
                )
                
                logger.info(f"게시판 LibreOffice 변환 결과: returncode={result.returncode}")
                logger.info(f"게시판 LibreOffice stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"게시판 LibreOffice stderr: {result.stderr}")
                
                # 변환된 PDF 파일 확인
                pdf_name = os.path.splitext(file_name)[0] + '.pdf'
                pdf_path = os.path.join(temp_dir, pdf_name)
                
                if os.path.exists(pdf_path):
                    # PDF 파일을 S3에 업로드
                    from django.conf import settings
                    import boto3
                    
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.AWS_S3_REGION_NAME
                    )
                    
                    # S3 키 생성 (게시판용)
                    pdf_s3_key = f"converted_pdfs/board_{saved_name}_{pdf_name}"
                    
                    # PDF 파일을 S3에 업로드
                    with open(pdf_path, 'rb') as pdf_file:
                        s3_client.upload_fileobj(
                            pdf_file,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            pdf_s3_key,
                            ExtraArgs={'ContentType': 'application/pdf'}
                        )
                    
                    # S3 미리보기 URL 생성
                    pdf_preview_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                            'Key': pdf_s3_key,
                            'ResponseContentDisposition': 'inline'
                        },
                        ExpiresIn=3600
                    )
                    
                    logger.info(f"게시판 PDF 변환 및 업로드 성공: {pdf_preview_url}")
                    
                    return JsonResponse({
                        'success': True,
                        'url': pdf_preview_url,
                        'message': 'HWP 파일이 PDF로 성공적으로 변환되었습니다.'
                    })
                else:
                    logger.error(f"게시판 PDF 변환 실패: {pdf_path} 파일이 존재하지 않습니다.")
                    return JsonResponse({
                        'success': False,
                        'error': 'HWP 파일 변환에 실패했습니다.',
                        'message': 'LibreOffice가 HWP 파일을 변환할 수 없습니다.'
                    })
                    
        except requests.RequestException as e:
            logger.error(f"게시판 파일 다운로드 실패: {e}")
            return JsonResponse({
                'success': False,
                'error': f'파일 다운로드 실패: {str(e)}',
                'message': '파일을 다운로드할 수 없습니다.'
            })
        except subprocess.TimeoutExpired:
            logger.error("게시판 LibreOffice 변환 타임아웃")
            return JsonResponse({
                'success': False,
                'error': '변환 시간이 초과되었습니다.',
                'message': '변환에 시간이 너무 오래 걸립니다.'
            })
        except Exception as e:
            logger.error(f"게시판 HWP 변환 중 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'변환 중 오류가 발생했습니다: {str(e)}',
                'message': '변환 중 오류가 발생했습니다.'
            })
        
    except json.JSONDecodeError as e:
        logger.error(f"게시판 JSON 파싱 오류: {e}")
        return JsonResponse({'success': False, 'error': f'요청 데이터 파싱 오류: {str(e)}'})
    except Exception as e:
        logger.error(f"convert_hwp_to_pdf_board 함수에서 예상치 못한 오류: {e}")
        return JsonResponse({'success': False, 'error': f'오류가 발생했습니다: {str(e)}'})