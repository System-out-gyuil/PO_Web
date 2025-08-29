from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import boto3
import logging
import base64
from .models import User

logger = logging.getLogger(__name__)

def diary_use_preview(request):
    """다이어리 사용 방법 미리보기"""
    try:
        # 사용자 인증 정보를 context에 추가
        context = {
            'user': request.user,
            'is_authenticated': request.session.get('diary_authenticated', False),
            'is_admin': request.session.get('diary_member_id') and User.objects.get(id=request.session['diary_member_id']).is_admin,
        }
        
        # S3 설정
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # S3에서 파일 정보 가져오기
        bucket_name = 'po.s3'
        file_key = 'auto_blog/자금왕_사용_설명_0822.pdf'
        
        try:
            # S3에서 파일 객체 가져오기
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = response['Body'].read()
            
            # PDF 파일을 base64로 인코딩하여 템플릿에 전달
            pdf_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # context에 PDF 관련 정보 추가
            context.update({
                'pdf_base64': pdf_base64,
                'filename': '자금왕_사용_설명_0822.pdf',
                'file_size': len(file_content),
                's3_url': f"https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_key}"
            })
            
            return render(request, 'diary/diary_use_preview.html', context)
            
        except Exception as s3_error:
            logger.error(f"S3 파일 가져오기 오류: {s3_error}")
            context.update({
                'error': f'S3에서 파일을 가져올 수 없습니다: {str(s3_error)}'
            })
            return render(request, 'diary/diary_use_preview.html', context)
            
    except Exception as e:
        logger.error(f"다이어리 사용 방법 미리보기 오류: {e}")
        context = {
            'user': request.user,
            'is_authenticated': request.session.get('diary_authenticated', False),
            'is_admin': request.session.get('diary_member_id') and User.objects.get(id=request.session['diary_member_id']).is_admin,
            'error': str(e)
        }
        return render(request, 'diary/diary_use_preview.html', context)