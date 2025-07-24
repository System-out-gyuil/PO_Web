from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import User, BaseAttribute, BaseAttributeDetail, Attribute, AttributeValue, DropdownAttribute, Row, CalendarSettings, KanbanSettings
import json

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def get(self, request):
        return render(request, 'diary/diary_login.html')
    
    def post(self, request):
        try:
            # JSON 데이터 파싱
            data = json.loads(request.body)
            member_id = data.get('member_id')
            member_pw = data.get('member_pw')

            print(member_id, member_pw)

            # 입력값 검증
            if not member_id or not member_pw:
                return JsonResponse({
                    'success': False,
                    'error': '아이디와 비밀번호를 모두 입력해주세요.'
                })

            try:
                member = User.objects.get(email=member_id, password=member_pw)

                # 로그인 성공 → 세션 저장
                request.session['diary_authenticated'] = True
                request.session['diary_member_id'] = member.id

                print(member.id)

                return JsonResponse({
                    'success': True,
                    'message': '로그인되었습니다.',
                    'redirect_url': '/sales/diary/'
                })

            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '아이디 또는 비밀번호가 틀렸습니다.'
                })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'로그인 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class SignupView(View):
    def post(self, request):
        try:
            # JSON 데이터 파싱
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            manager_name = data.get('manager_name')
            company_name = data.get('company_name')
            phone_number = data.get('phone_number')
            
            if not email or not password or not manager_name or not company_name or not phone_number:
                return JsonResponse({
                    'success': False,
                    'error': '모든 필드를 입력해주세요.'
                })
            
            # 이메일 중복 확인
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': '이미 존재하는 이메일입니다.'
                })
            
            # 사용자 생성
            user = User.objects.create(
                name=manager_name,  # 담당자명을 name으로 저장
                email=email,
                password=password,
                manager_name=manager_name,
                company_name=company_name,
                phone_number=phone_number
            )
            
            # 기본 속성들을 사용자에게 부여
            self._create_default_attributes(user)
            
            # 샘플 데이터 생성
            sample_data_created = self._create_sample_data(user)
            
            success_message = '회원가입이 완료되었습니다.'
            if sample_data_created:
                success_message += ' 샘플 데이터가 추가되었습니다.'
            
            return JsonResponse({
                'success': True,
                'message': success_message,
                'user_id': user.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'
            })
    
    def _create_default_attributes(self, user):
        """사용자에게 기본 속성들을 생성하는 메서드"""
        # 원하는 순서대로 속성명 정의
        desired_order = [
            '회사명',      # 1. baseattribute
            '매출',        # 3. baseattribute
            '신용점수',    # 5. baseattribute
            '업종',        # 8. baseattribute
            '지역',        # 2. baseattribute
            '기대출',      # 4. baseattributedetail
            '개업년월',    # 6. baseattribute
            '나이',        # 7. baseattribute
            '경력',        # 9. baseattribute
            '직원수',      # 10. baseattribute
            '추천자금',
        ]
        
        # sort_order를 위한 카운터
        sort_order_counter = 1
        
        # 원하는 순서대로 속성 생성
        for attr_name in desired_order:
            # BaseAttribute에서 찾기
            try:
                base_attr = BaseAttribute.objects.get(name=attr_name)
                Attribute.objects.create(
                    name=base_attr.name,
                    user=user,
                    attributeType=base_attr.attributeType,
                    assential=True,
                    detail=False,  # BaseAttribute는 detail=0
                    sort_order=sort_order_counter,
                    view_select={"0": True},
                    cascade=True,  # 기본적으로 True
                    width=150  # 기본값
                )
                sort_order_counter += 1
            except BaseAttribute.DoesNotExist:
                # BaseAttributeDetail에서 찾기
                try:
                    base_detail_attr = BaseAttributeDetail.objects.get(name=attr_name)
                    Attribute.objects.create(
                        name=base_detail_attr.name,
                        user=user,
                        attributeType=base_detail_attr.attributeType,
                        assential=True,
                        detail=True,  # BaseAttributeDetail은 detail=1
                        sort_order=sort_order_counter,
                        view_select={"0": True},
                        cascade=True,  # 기본적으로 True
                        width=150  # 기본값
                    )
                    sort_order_counter += 1
                except BaseAttributeDetail.DoesNotExist:
                    # 원하는 순서에 없는 속성은 건너뛰기
                    continue
        
        # 나머지 BaseAttribute 속성들 (원하는 순서에 없는 것들)
        base_attributes = BaseAttribute.objects.all()
        for base_attr in base_attributes:
            if base_attr.name not in desired_order:
                Attribute.objects.create(
                    name=base_attr.name,
                    user=user,
                    attributeType=base_attr.attributeType,
                    assential=True,
                    detail=False,  # BaseAttribute는 detail=0
                    sort_order=sort_order_counter,
                    view_select={"0": True},
                    cascade=True,  # 기본적으로 True
                    width=150  # 기본값
                )
                sort_order_counter += 1
        
        # 나머지 BaseAttributeDetail 속성들 (원하는 순서에 없는 것들)
        base_attribute_details = BaseAttributeDetail.objects.all()
        for base_detail_attr in base_attribute_details:
            if base_detail_attr.name not in desired_order:
                Attribute.objects.create(
                    name=base_detail_attr.name,
                    user=user,
                    attributeType=base_detail_attr.attributeType,
                    assential=True,
                    detail=True,  # BaseAttributeDetail은 detail=1
                    sort_order=sort_order_counter,
                    view_select={"0": True},
                    cascade=True,  # 기본적으로 True
                    width=150  # 기본값
                )
                sort_order_counter += 1
    
    def _create_sample_data(self, user):
        """샘플 데이터를 생성하는 메서드 (user.id=15 기준, FK는 새 유저 인스턴스 사용, 드롭다운 id 매핑)"""
        from django.db import transaction
        try:
            with transaction.atomic():
                sample_user = User.objects.get(id=15)
                user_attrs = {a.name: a for a in Attribute.objects.filter(user=user)}
                sample_rows = Row.objects.filter(user=sample_user)
                row_map = {}
                for sample_row in sample_rows:
                    new_row = Row.objects.create(
                        order=sample_row.order,
                        user=user,
                        created_at=sample_row.created_at
                    )
                    row_map[sample_row.id] = new_row
                sample_attrs = Attribute.objects.filter(user=sample_user)
                attr_name_map = {}
                dropdown_map = {}
                for sample_attr in sample_attrs:
                    if sample_attr.name in user_attrs:
                        new_attr = user_attrs[sample_attr.name]
                        attr_name_map[sample_attr.id] = new_attr
                        sample_dropdowns = DropdownAttribute.objects.filter(attribute=sample_attr)
                        for sample_dropdown in sample_dropdowns:
                            new_dropdown = DropdownAttribute.objects.create(
                                attribute=new_attr,
                                option=sample_dropdown.option,
                                color=sample_dropdown.color,
                                order=sample_dropdown.order
                            )
                            dropdown_map[sample_dropdown.id] = new_dropdown.id
                sample_values = AttributeValue.objects.filter(row__user=sample_user)
                for sample_value in sample_values:
                    new_attr = attr_name_map.get(sample_value.attribute_id)
                    new_row = row_map.get(sample_value.row_id)
                    if new_attr and new_row:
                        if new_attr.attributeType and new_attr.attributeType.name == 'dropdown':
                            v = sample_value.value
                            import json
                            try:
                                if v.startswith('[') and v.endswith(']'):
                                    old_ids = json.loads(v)
                                    new_ids = [dropdown_map.get(int(i), i) for i in old_ids]
                                    value_to_save = json.dumps(new_ids, ensure_ascii=False)
                                elif v.isdigit():
                                    value_to_save = str(dropdown_map.get(int(v), v))
                                else:
                                    value_to_save = v
                            except Exception:
                                value_to_save = v
                        else:
                            value_to_save = sample_value.value
                        AttributeValue.objects.create(
                            attribute=new_attr,
                            row=new_row,
                            value=value_to_save,
                            copy_from=sample_value.copy_from
                        )
                # CalendarSettings, KanbanSettings 복사
                sample_calendar = CalendarSettings.objects.filter(user=sample_user).first()
                if sample_calendar:
                    CalendarSettings.objects.create(user=user, settings=sample_calendar.settings)
                sample_kanban = KanbanSettings.objects.filter(user=sample_user).first()
                if sample_kanban:
                    KanbanSettings.objects.create(user=user, settings=sample_kanban.settings)
                # 상태 attribute의 DropdownAttribute id 모두 구함
                status_attr = Attribute.objects.filter(user=user, name='상태', attributeType__name='dropdown').first()
                status_dropdown_ids = []
                if status_attr:
                    status_dropdowns = DropdownAttribute.objects.filter(attribute=status_attr)
                    status_dropdown_ids = [str(d.id) for d in status_dropdowns]
                # 모든 Attribute의 view_select에 상태 드롭다운 id를 true로 추가
                for attr in Attribute.objects.filter(user=user):
                    view_select = {"0": True}
                    for did in status_dropdown_ids:
                        view_select[did] = True
                    attr.view_select = view_select
                    attr.save()
            print(f"샘플 데이터 생성 완료: {user.id}번 사용자")
            return True
        except User.DoesNotExist:
            print("user.id=15인 사용자가 존재하지 않습니다.")
            return False
        except Exception as e:
            print(f"샘플 데이터 생성 중 오류: {str(e)}")
            return False

class LogoutView(View):
    def get(self, request):
        return render(request, 'diary/logout.html')
    
    def post(self, request):
        try:
            # 세션에서 diary_member_id 제거
            if 'diary_member_id' in request.session:
                del request.session['diary_member_id']
            
            # diary_authenticated도 제거
            if 'diary_authenticated' in request.session:
                del request.session['diary_authenticated']
            
            # 세션 저장
            request.session.save()
            
            return JsonResponse({
                'success': True,
                'message': '로그아웃되었습니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
