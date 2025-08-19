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
from django.http import HttpResponse

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
                        if attr and attr.attributeType and attr.attributeType.name == 'dropdown':
                            dropdown_options = DropdownAttribute.objects.filter(attribute=attr).values('id', 'option')
                            dropdown_info[attr_name] = list(dropdown_options)
                    except Exception as e:
                        print(f"속성 '{attr_name}' 처리 중 오류: {str(e)}")
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
                                        
                                        if dropdown_attr:
                                            value_to_save = str(dropdown_attr.id)
                                            print(f"    Dropdown 매핑: {excel_value} -> ID {dropdown_attr.id}")
                                        else:
                                            # 해당 옵션이 없으면 원본 값 그대로 저장
                                            value_to_save = excel_value
                                            print(f"    Dropdown 옵션 없음: {excel_value} (원본 값 저장)")
                                    except Exception as e:
                                        # 오류 발생 시 원본 값 그대로 저장
                                        value_to_save = excel_value
                                        print(f"    Dropdown 처리 오류: {excel_value} (원본 값 저장) - {str(e)}")
                                elif attribute.attributeType and attribute.attributeType.name == 'datetime':
                                    # datetime 타입인 경우 날짜만 추출 (YYYY-MM-DD 형식)
                                    try:
                                        # pandas에서 datetime 객체로 변환된 경우
                                        if hasattr(row_data[excel_column], 'strftime'):
                                            value_to_save = row_data[excel_column].strftime('%Y-%m-%d')
                                        else:
                                            # 문자열인 경우 datetime으로 파싱 후 날짜만 추출
                                            from datetime import datetime
                                            parsed_date = pd.to_datetime(excel_value)
                                            value_to_save = parsed_date.strftime('%Y-%m-%d')
                                        print(f"    Datetime 변환: {excel_value} -> {value_to_save}")
                                    except (ValueError, TypeError) as e:
                                        # 날짜 파싱에 실패한 경우 원본 값 사용
                                        value_to_save = excel_value
                                        print(f"    Datetime 파싱 실패: {excel_value} (원본 값 저장)")
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

@require_GET
def download_excel_template(request):
    """엑셀 양식 다운로드 API"""
    try:
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # S3에 업로드된 엑셀 양식 파일 정보
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        s3_key = 'excel_sample/엑셀양식.xlsx'
        
        # 서명된 URL 생성 (1시간 유효)
        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=3600  # 1시간
        )
        
        # 서명된 URL로 리다이렉트
        from django.shortcuts import redirect
        return redirect(signed_url)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'양식 다운로드 실패: {str(e)}'
        })

def create_sample_excel_template(request):
    """샘플 데이터가 포함된 엑셀 양식 생성"""
    try:
        user_id = request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': '로그인이 필요합니다.'
            })
        
        user = User.objects.get(id=user_id)
        
        # 사용자의 모든 속성 가져오기
        attributes = Attribute.objects.filter(user=user).order_by('order')
        
        # 샘플 데이터 생성
        sample_data = {}
        
        for attr in attributes:
            attr_name = attr.name
            
            if attr.attributeType and attr.attributeType.name == 'dropdown':
                # 드롭다운 타입인 경우 첫 번째 옵션 사용
                dropdown_options = DropdownAttribute.objects.get(attribute=attr)
                if dropdown_options:
                    sample_data[attr_name] = dropdown_options.option
                else:
                    sample_data[attr_name] = "옵션1"
            elif attr.attributeType and attr.attributeType.name == 'datetime':
                # 날짜 타입인 경우
                sample_data[attr_name] = "2024-01-01"
            else:
                # 텍스트 타입인 경우
                if '회사명' in attr_name or '업체명' in attr_name:
                    sample_data[attr_name] = "샘플회사"
                elif '매출' in attr_name or '금액' in attr_name:
                    sample_data[attr_name] = "1000"
                elif '담당자' in attr_name:
                    sample_data[attr_name] = "홍길동"
                elif '연락처' in attr_name or '전화' in attr_name:
                    sample_data[attr_name] = "010-1234-5678"
                elif '주소' in attr_name:
                    sample_data[attr_name] = "서울시 강남구"
                elif '메모' in attr_name:
                    sample_data[attr_name] = "샘플 메모입니다"
                else:
                    sample_data[attr_name] = f"샘플_{attr_name}"
        
        # 여러 행의 샘플 데이터 생성 (3개 행)
        sample_rows = []
        for i in range(3):
            row_data = {}
            for attr_name, value in sample_data.items():
                if '회사명' in attr_name or '업체명' in attr_name:
                    row_data[attr_name] = f"샘플회사{i+1}"
                elif '매출' in attr_name or '금액' in attr_name:
                    row_data[attr_name] = str((i+1) * 1000)
                else:
                    row_data[attr_name] = value
            sample_rows.append(row_data)
        
        # 데이터프레임 생성
        df = pd.DataFrame(sample_rows)
        
        # 메모리 내에서 엑셀 파일 생성
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='샘플데이터')
        
        output.seek(0)
        
        # HTTP 응답 생성
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="양식_샘플.xlsx"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'양식 생성 실패: {str(e)}'
        }) 