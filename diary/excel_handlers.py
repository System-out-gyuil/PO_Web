from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Attribute, AttributeValue, User, Row, DropdownAttribute
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
            
            # NaN 값을 null로 변환
            for row in preview_data:
                for key, value in row.items():
                    if pd.isna(value):
                        row[key] = None
            
            # 기본 매핑 정보 생성 (엑셀 컬럼명과 DB 속성명 비교)
            mapping = {}
            if preview_data:
                # 사용자의 모든 속성 가져오기
                user_id = request.session.get('diary_member_id')
                user = User.objects.get(id=user_id)
                user_attributes = Attribute.objects.filter(user=user).values_list('name', flat=True)
                user_attributes = list(user_attributes)
                
                print(f"사용자 속성들: {user_attributes}")
                print(f"엑셀 컬럼들: {columns}")
                
                # 엑셀 컬럼과 DB 속성명 매핑
                for column in columns:
                    if column != "Unnamed: 0":  # 첫 번째 빈 컬럼 제외
                        # 정확히 일치하는 속성 찾기
                        if column in user_attributes:
                            mapping[column] = column
                        else:
                            # 부분 일치하는 속성 찾기
                            for attr_name in user_attributes:
                                if column.lower() in attr_name.lower() or attr_name.lower() in column.lower():
                                    mapping[column] = attr_name
                                    break
                            else:
                                # 매핑되지 않은 컬럼은 빈 값으로
                                mapping[column] = ""
                
                # dropdown 타입 속성들의 옵션 정보도 추가
                dropdown_info = {}
                for attr_name in user_attributes:
                    try:
                        attr = Attribute.objects.get(user=user, name=attr_name)
                        if attr.attributeType and attr.attributeType.name == 'dropdown':
                            dropdown_options = DropdownAttribute.objects.filter(attribute=attr).values('id', 'option')
                            dropdown_info[attr_name] = list(dropdown_options)
                    except Attribute.DoesNotExist:
                        continue
                
                print(f"Dropdown 옵션 정보: {dropdown_info}")
            
            return JsonResponse({
                'success': True,
                'preview': preview_data,
                'columns': columns,
                'total_rows': len(df),
                'mapping': mapping,
                'dropdown_info': dropdown_info
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
            
            print(f"받은 매핑 데이터: {mapping_data}")
            
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
            
            # 사용자의 모든 속성 가져오기
            user_attributes = Attribute.objects.filter(user=user).values_list('name', flat=True)
            user_attributes = list(user_attributes)
            
            # 엑셀 컬럼과 DB 속성명 자동 매핑
            auto_mapping = {}
            for column in df.columns:
                if column != "Unnamed: 0":  # 첫 번째 빈 컬럼 제외
                    # 정확히 일치하는 속성 찾기
                    if column in user_attributes:
                        auto_mapping[column] = column
                    else:
                        # 부분 일치하는 속성 찾기
                        for attr_name in user_attributes:
                            if column.lower() in attr_name.lower() or attr_name.lower() in column.lower():
                                auto_mapping[column] = attr_name
                                break
                        else:
                            # 매핑되지 않은 컬럼은 건너뛰기
                            continue
            
            print(f"자동 매핑 결과: {auto_mapping}")
            
            for index, row_data in df.iterrows():
                try:
                    # 새 행 생성
                    new_row = Row.objects.create(
                        user=user,
                        order=Row.objects.filter(user=user).count() + 1
                    )
                    
                    print(f"행 {index} 처리 중...")
                    
                    # 자동 매핑된 속성들에 대해 값 설정
                    for excel_column, attribute_name in auto_mapping.items():
                        if excel_column in row_data and pd.notna(row_data[excel_column]):
                            try:
                                # 속성 찾기
                                attribute = Attribute.objects.get(user=user, name=attribute_name)
                                
                                # 값 설정
                                excel_value = str(row_data[excel_column])
                                print(f"  {excel_column} -> {attribute_name}: {excel_value}")
                                
                                # dropdown 타입인 경우 DropdownAttribute에서 ID 찾기
                                if attribute.attributeType and attribute.attributeType.name == 'dropdown':
                                    try:
                                        # DropdownAttribute에서 해당 옵션 찾기
                                        dropdown_attr = DropdownAttribute.objects.get(
                                            attribute=attribute, 
                                            option=excel_value
                                        )
                                        value_to_save = str(dropdown_attr.id)
                                        print(f"    Dropdown 매핑: {excel_value} -> ID {dropdown_attr.id}")
                                    except DropdownAttribute.DoesNotExist:
                                        # 해당 옵션이 없으면 원본 값 그대로 저장
                                        value_to_save = excel_value
                                        print(f"    Dropdown 옵션 없음: {excel_value} (원본 값 저장)")
                                else:
                                    # 일반 텍스트 필드
                                    value_to_save = excel_value
                                
                                attr_value, created = AttributeValue.objects.get_or_create(
                                    row=new_row,
                                    attribute=attribute,
                                    defaults={'value': value_to_save}
                                )
                                
                                if not created:
                                    attr_value.value = value_to_save
                                    attr_value.save()
                                
                            except Attribute.DoesNotExist:
                                print(f"  속성 '{attribute_name}'을 찾을 수 없습니다.")
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