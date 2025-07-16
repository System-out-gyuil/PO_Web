from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Attribute, AttributeValue, User, Row
import json
import pandas as pd
from openpyxl import load_workbook
import boto3
from django.conf import settings
import uuid
import os
from botocore.exceptions import ClientError
from datetime import datetime

@csrf_exempt
def preview_excel(request):
    """엑셀 파일 미리보기 API"""
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('excel_file')
            
            if not excel_file:
                return JsonResponse({
                    'success': False,
                    'error': '엑셀 파일이 필요합니다.'
                })
            
            # 파일 확장자 확인
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return JsonResponse({
                    'success': False,
                    'error': '엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.'
                })
            
            # 파일 크기 제한 (10MB)
            max_file_size = 10 * 1024 * 1024
            if excel_file.size > max_file_size:
                return JsonResponse({
                    'success': False,
                    'error': '파일 크기가 10MB를 초과합니다.'
                })
            
            # 엑셀 파일 읽기
            try:
                if excel_file.name.endswith('.xlsx'):
                    df = pd.read_excel(excel_file, engine='openpyxl')
                else:
                    df = pd.read_excel(excel_file, engine='xlrd')
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'엑셀 파일 읽기 실패: {str(e)}'
                })
            
            # 데이터 미리보기 (처음 10행)
            preview_data = df.head(10).to_dict('records')
            columns = df.columns.tolist()
            
            return JsonResponse({
                'success': True,
                'preview': preview_data,
                'columns': columns,
                'total_rows': len(df)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def upload_excel(request):
    """엑셀 파일 업로드 및 데이터 처리 API"""
    if request.method == 'POST':
        try:
            excel_file = request.FILES.get('excel_file')
            mapping_data = json.loads(request.POST.get('mapping', '{}'))
            
            if not excel_file:
                return JsonResponse({
                    'success': False,
                    'error': '엑셀 파일이 필요합니다.'
                })
            
            user_id = request.session.get('diary_member_id')
            user = User.objects.get(id=user_id)
            
            # 엑셀 파일 읽기
            try:
                if excel_file.name.endswith('.xlsx'):
                    df = pd.read_excel(excel_file, engine='openpyxl')
                else:
                    df = pd.read_excel(excel_file, engine='xlrd')
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'엑셀 파일 읽기 실패: {str(e)}'
                })
            
            # S3에 파일 업로드
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # 고유한 파일명 생성
                file_extension = os.path.splitext(excel_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                s3_key = f"excel_files/{unique_filename}"
                
                # S3에 파일 업로드
                s3_client.upload_fileobj(
                    excel_file,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        'ContentType': excel_file.content_type,
                        'ContentDisposition': f'attachment; filename="{excel_file.name}"'
                    }
                )
                
                # 다운로드 URL 생성
                download_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'S3 업로드 실패: {str(e)}'
                })
            
            # 데이터 처리 및 행 생성
            created_rows = 0
            for index, row_data in df.iterrows():
                try:
                    # 새 행 생성
                    new_row = Row.objects.create(
                        user=user,
                        order=Row.objects.filter(user=user).count() + 1
                    )
                    
                    # 매핑된 속성들에 대해 값 설정
                    for excel_column, attribute_name in mapping_data.items():
                        if excel_column in row_data and pd.notna(row_data[excel_column]):
                            try:
                                # 속성 찾기
                                attribute = Attribute.objects.get(user=user, name=attribute_name)
                                
                                # 값 설정
                                value = str(row_data[excel_column])
                                attr_value, created = AttributeValue.objects.get_or_create(
                                    row=new_row,
                                    attribute=attribute,
                                    defaults={'value': value}
                                )
                                
                                if not created:
                                    attr_value.value = value
                                    attr_value.save()
                                
                            except Attribute.DoesNotExist:
                                # 속성이 없으면 건너뛰기
                                continue
                    
                    created_rows += 1
                    
                except Exception as e:
                    # 개별 행 처리 실패 시 로그만 남기고 계속 진행
                    print(f"행 {index} 처리 실패: {str(e)}")
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'{created_rows}개의 행이 성공적으로 생성되었습니다.',
                'created_rows': created_rows,
                'excel_file_url': download_url
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=405) 