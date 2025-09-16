from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import re
from .models import User, BaseAttribute, BaseAttributeDetail, Attribute, AttributeValue, DropdownAttribute, Row, CalendarSettings, KanbanSettings, EmailVerification, CountUser, CountUserIP
import json
from config import EMAIL_AUTH_VALID_TIME, SENDER_EMAIL
from .solapi import solapi_api


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def _get_client_ip(self, request):
        """클라이언트의 실제 IP 주소를 가져오는 메서드"""
        # 프록시 환경에서 실제 클라이언트 IP를 가져오기 위한 헤더들
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For 헤더가 있으면 첫 번째 IP가 실제 클라이언트 IP
            client_ip = x_forwarded_for.split(',')[0].strip()
            return client_ip
        
        # X-Real-IP 헤더 확인 (Nginx에서 설정)
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        
        # HTTP_CLIENT_IP 헤더 확인
        http_client_ip = request.META.get('HTTP_CLIENT_IP')
        if http_client_ip:
            return http_client_ip
        
        # 기본값으로 REMOTE_ADDR 사용
        remote_addr = request.META.get('REMOTE_ADDR')
        if remote_addr:
            return remote_addr
        
        # 모든 방법이 실패하면 기본값 반환
        return 'unknown'
    
    def get(self, request):
        # 이미 로그인된 사용자인지 확인
        if request.session.get('diary_authenticated') and request.session.get('diary_member_id'):
            # 로그인된 사용자는 다이어리 페이지로 리다이렉트
            return redirect('/sales/diary/')
        
        # 로그인되지 않은 사용자는 로그인 페이지 렌더링
        return render(request, 'diary/diary_login.html')
    
    def post(self, request):
        try:
            # JSON 데이터 파싱
            data = json.loads(request.body)
            member_id = data.get('member_id')
            member_pw = data.get('member_pw')

            print(f'member_id: {member_id}, member_pw: {member_pw}')

            # 입력값 검증
            if not member_id or not member_pw:
                return JsonResponse({
                    'success': False,
                    'error': '아이디와 비밀번호를 모두 입력해주세요.'
                })

            try:
                # 사용자 조회 (이메일로만 조회)
                member = User.objects.get(email=member_id)
                
                # 계정 활성화 상태 확인
                if not member.activate:
                    return JsonResponse({
                        'success': False,
                        'error': '비활성화된 계정입니다.'
                    })
                
                # 사용 기간 만료 확인 및 자동 비활성화
                if member.is_expired():
                    # 만료된 경우 자동으로 비활성화
                    member.activate = False
                    member.save()
                    return JsonResponse({
                        'success': False,
                        'error': '사용기간이 만료되어 계정이 비활성화되었습니다.'
                    })
                
                # 비밀번호 검증
                if check_password(member_pw, member.password):
                    # 로그인 성공 → 세션 저장
                    request.session['diary_authenticated'] = True
                    request.session['diary_member_id'] = member.id

                    # CountUser 테이블에 로그인 기록 추가
                    try:
                        count_user, created = CountUser.objects.get_or_create(
                            name=member.name,
                            defaults={'count': 1}
                        )
                        if not created:
                            count_user.count += 1
                            count_user.save()
                    except Exception as e:
                        print(f"CountUser 업데이트 중 오류: {str(e)}")

                    # IP 주소 가져오기 (프록시 환경 고려)
                    client_ip = self._get_client_ip(request)
                    print(f"Client IP: {client_ip}")
                    print(f"REMOTE_ADDR: {request.META.get('REMOTE_ADDR')}")
                    print(f"HTTP_X_FORWARDED_FOR: {request.META.get('HTTP_X_FORWARDED_FOR')}")
                    print(f"HTTP_X_REAL_IP: {request.META.get('HTTP_X_REAL_IP')}")

                    # CountUserIP 테이블에 로그인 기록 추가
                    try:
                        count_user_ip = CountUserIP.objects.create(
                            ip=client_ip,
                            user=member
                        )
                        print(f"CountUserIP 저장 성공: IP={client_ip}, User={member.name}")
                    except Exception as e:
                        print(f"CountUserIP 업데이트 중 오류: {str(e)}")

                    print(f"로그인 성공: {member.id}")


                    return JsonResponse({
                        'success': True,
                        'message': '로그인되었습니다.',
                        'redirect_url': '/sales/'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': '아이디 또는 비밀번호가 틀렸습니다.'
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
            verification_code = data.get('verification_code')
            
            if not email or not password or not manager_name or not company_name or not phone_number or not verification_code:
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
            
            # 이메일 인증 확인
            try:
                verification = EmailVerification.objects.get(
                    email=email,
                    verification_code=verification_code
                )
                
                # 만료 확인
                if verification.is_expired():
                    return JsonResponse({
                        'success': False,
                        'error': '인증번호가 만료되었습니다. 새로운 인증번호를 발송해주세요.'
                    })
                
                # 인증 완료 처리
                verification.is_verified = True
                verification.save()
                
            except EmailVerification.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '이메일 인증이 필요합니다. 인증번호를 확인해주세요.'
                })
            
            # 비밀번호 암호화
            hashed_password = make_password(password)
            
            # 사용자 생성
            user = User.objects.create(
                name=manager_name,  # 담당자명을 name으로 저장
                email=email,
                password=hashed_password,  # 암호화된 비밀번호 저장
                manager_name=manager_name,
                company_name=company_name,
                phone_number=phone_number,
                use_date=timezone.now() + timedelta(days=7)  # 한 달 사용 기간 설정
            )

            # 모든 기존 공지(Alarm)를 UserAlarm으로 추가
            from .models import Alarm, UserAlarm
            alarms = Alarm.objects.all()
            for alarm in alarms:
                UserAlarm.objects.create(user=user, alarm=alarm, is_read=False)
            
            # 기본 속성들을 사용자에게 부여
            self._create_default_attributes(user)
            
            # 샘플 데이터 생성
            sample_data_created = self._create_sample_data(user)
            
            # 인증번호 삭제
            verification.delete()
            
            success_message = '회원가입이 완료되었습니다.'


            solapi_api("signup", phone_number)

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
        """사용자에게 기본 속성들을 생성하는 메서드 (샘플 계정의 sort_order 기준)"""
        try:
            # 샘플 데이터 제공 계정 (user.id=34)
            sample_user = User.objects.get(id=34)
            
            # 샘플 계정의 속성들을 sort_order 순으로 조회
            sample_attributes = Attribute.objects.filter(user=sample_user).order_by('sort_order')
            
            # 동기화를 활성화할 속성들 정의
            cascade_enabled_attributes = {
                '회사명', '매출', '계약여부', '지역', '상세지역', 
                '주소', '이메일', '연락처', '미팅', 'TA', '신용점수', '업종', '기대출', '개업년월', '나이', '경력', '직원수', '추천자금',
                '사업자등록증', '통신사', '부가세표준증명원', '재무제표', '음성파일', '변환된 텍스트'
            }
            
            # 샘플 계정의 속성 순서대로 새 사용자에게 속성 생성
            for sample_attr in sample_attributes:
                # BaseAttribute 또는 BaseAttributeDetail에서 찾기
                base_attr = None
                is_detail = False
                
                try:
                    # BaseAttribute에서 먼저 찾기
                    base_attr = BaseAttribute.objects.get(name=sample_attr.name)
                    is_detail = False
                except BaseAttribute.DoesNotExist:
                    try:
                        # BaseAttributeDetail에서 찾기
                        base_attr = BaseAttributeDetail.objects.get(name=sample_attr.name)
                        is_detail = True
                    except BaseAttributeDetail.DoesNotExist:
                        print(f"속성 '{sample_attr.name}'을 BaseAttribute 또는 BaseAttributeDetail에서 찾을 수 없습니다.")
                        continue
                
                if base_attr:
                    # cascade 값 결정
                    cascade_value = sample_attr.name in cascade_enabled_attributes
                    
                    # 새 사용자에게 속성 생성 (샘플 계정의 sort_order 사용)
                    Attribute.objects.create(
                        name=base_attr.name,
                        user=user,
                        attributeType=base_attr.attributeType,
                        assential=True,
                        detail=is_detail,
                        sort_order=sample_attr.sort_order,  # 샘플 계정의 sort_order 사용
                        detail_sort_order=sample_attr.detail_sort_order,  # 샘플 계정의 detail_sort_order 사용
                        view_select={"0": True},
                        cascade=cascade_value,
                        width=sample_attr.width or 150  # 샘플 계정의 width도 사용, 없으면 기본값
                    )
                    print(f"속성 생성 완료: {sample_attr.name} (sort_order: {sample_attr.sort_order})")
            
            print(f"샘플 계정 기준 속성 생성 완료: {sample_attributes.count()}개 속성")
            
        except User.DoesNotExist:
            print("샘플 데이터 제공 계정(user.id=34)이 존재하지 않습니다. 기본 방식으로 속성을 생성합니다.")
            # 기본 방식으로 폴백
            self._create_default_attributes_fallback(user)
        except Exception as e:
            print(f"샘플 계정 기준 속성 생성 중 오류: {str(e)}. 기본 방식으로 속성을 생성합니다.")
            # 기본 방식으로 폴백
            self._create_default_attributes_fallback(user)
    
    def _create_default_attributes_fallback(self, user):
        """기본 방식으로 속성을 생성하는 폴백 메서드"""
        # 동기화를 활성화할 속성들 정의
        cascade_enabled_attributes = {
            '회사명', '매출', '계약여부', '지역', '상세지역', 
            '주소', '이메일', '연락처', '미팅', 'TA', '신용점수', '업종', '기대출', '개업년월', '나이', '경력', '직원수', '추천자금',
            '사업자등록증', '통신사', '부가세표준증명원', '재무제표', '음성파일', '변환된 텍스트'
        }
        
        # sort_order를 위한 카운터
        sort_order_counter = 1
        
        # BaseAttribute 속성들 생성
        base_attributes = BaseAttribute.objects.all()
        for base_attr in base_attributes:
            # cascade 값 결정
            cascade_value = base_attr.name in cascade_enabled_attributes
            Attribute.objects.create(
                name=base_attr.name,
                user=user,
                attributeType=base_attr.attributeType,
                assential=True,
                detail=False,  # BaseAttribute는 detail=0
                sort_order=sort_order_counter,
                detail_sort_order=sort_order_counter,  # detail_sort_order도 동일하게 설정
                view_select={"0": True},
                cascade=cascade_value,
                width=150  # 기본값
            )
            sort_order_counter += 1
        
        # BaseAttributeDetail 속성들 생성
        base_attribute_details = BaseAttributeDetail.objects.all()
        for base_detail_attr in base_attribute_details:
            # cascade 값 결정
            cascade_value = base_detail_attr.name in cascade_enabled_attributes
            Attribute.objects.create(
                name=base_detail_attr.name,
                user=user,
                attributeType=base_detail_attr.attributeType,
                assential=True,
                detail=True,  # BaseAttributeDetail은 detail=1
                sort_order=sort_order_counter,
                detail_sort_order=sort_order_counter,  # detail_sort_order도 동일하게 설정
                view_select={"0": True},
                cascade=cascade_value,
                width=150  # 기본값
            )
            sort_order_counter += 1
    
    def _create_sample_data(self, user):
        """샘플 데이터를 생성하는 메서드 (user.id=15 기준, FK는 새 유저 인스턴스 사용, 드롭다운 id 매핑)"""
        from django.db import transaction
        try:
            with transaction.atomic():
                sample_user = User.objects.get(id=34)
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
                    # 칸반보드 설정의 DropdownAttribute ID 매핑
                    updated_kanban_settings = self._map_kanban_dropdown_ids(
                        sample_kanban.settings, sample_user, user, dropdown_map
                    )
                    KanbanSettings.objects.create(user=user, settings=updated_kanban_settings)
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

    def _map_kanban_dropdown_ids(self, settings, old_user, new_user, dropdown_map):
        """칸반보드 설정의 DropdownAttribute ID를 새 사용자의 ID로 매핑하는 메서드"""
        if not settings:
            return {}

        import copy
        updated_settings = copy.deepcopy(settings)
        
        # filters에서 DropdownAttribute ID 매핑
        if 'filters' in updated_settings:
            for filter_rule in updated_settings['filters']:
                if isinstance(filter_rule, dict) and 'attribute' in filter_rule and 'value' in filter_rule:
                    attr_name = filter_rule['attribute']
                    old_id = filter_rule['value']
                    
                    # 이 속성이 드롭다운 속성인지 확인하고 새 ID로 매핑
                    new_id = self._map_dropdown_value_by_name(old_id, attr_name, old_user, new_user)
                    if new_id is not None:
                        filter_rule['value'] = new_id

        # custom_rules에서 DropdownAttribute ID 매핑  
        if 'custom_rules' in updated_settings:
            for rule in updated_settings['custom_rules']:
                if isinstance(rule, dict) and 'conditions' in rule:
                    for condition in rule['conditions']:
                        if isinstance(condition, dict) and 'attribute' in condition and 'value' in condition:
                            attr_name = condition['attribute']
                            old_id = condition['value']
                            
                            # 이 속성이 드롭다운 속성인지 확인하고 새 ID로 매핑
                            new_id = self._map_dropdown_value_by_name(old_id, attr_name, old_user, new_user)
                            if new_id is not None:
                                condition['value'] = new_id

        return updated_settings

    def _map_dropdown_value_by_name(self, old_id, attribute_name, old_user, new_user):
        """DropdownAttribute ID를 이름 기반으로 새 사용자의 ID로 매핑"""
        try:
            # 원본 사용자의 드롭다운 옵션 찾기
            old_dropdown = DropdownAttribute.objects.get(
                id=old_id,
                attribute__name=attribute_name,
                attribute__user=old_user
            )
            
            # 새 사용자의 같은 이름을 가진 드롭다운 옵션 찾기
            new_dropdown = DropdownAttribute.objects.filter(
                option=old_dropdown.option,
                attribute__name=attribute_name,
                attribute__user=new_user
            ).first()
            
            if new_dropdown:
                return str(new_dropdown.id)
            else:
                print(f"매핑할 수 없는 드롭다운 옵션: {old_dropdown.option} (속성: {attribute_name})")
                return str(old_id)  # 매핑 실패시 원본 ID 유지
                
        except DropdownAttribute.DoesNotExist:
            print(f"존재하지 않는 드롭다운 ID: {old_id} (속성: {attribute_name})")
            return str(old_id)  # 원본 ID 유지
        except Exception as e:
            print(f"드롭다운 ID 매핑 중 오류: {str(e)}")
            return str(old_id)  # 오류시 원본 ID 유지

class LogoutView(View):
    def get(self, request):
        # 세션에서 diary_member_id, diary_authenticated 제거
        request.session.pop('diary_member_id', None)
        request.session.pop('diary_authenticated', None)
        request.session.pop('admin_switch', None)
        request.session.save()
        
        # 로그인 페이지로 리다이렉트
        return redirect('/sales/')
    
    def post(self, request):
        try:
            # 세션에서 diary_member_id, diary_authenticated 제거
            request.session.pop('diary_member_id', None)
            request.session.pop('diary_authenticated', None)
            request.session.pop('admin_switch', None)
            request.session.save()
            
            # JSON 응답 반환
            return JsonResponse({
                'success': True,
                'message': '로그아웃되었습니다.'
            })
        except Exception as e:
            # 오류가 발생해도 로그아웃은 성공으로 처리
            return JsonResponse({
                'success': True,
                'message': '로그아웃되었습니다.'
            })

@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordView(View):
    def get(self, request):
        # 로그인 상태 확인
        if not request.session.get('diary_authenticated'):
            return redirect('/sales/login/')
        return render(request, 'diary/change_password.html')
    
    def post(self, request):
        try:
            # 로그인 상태 확인
            if not request.session.get('diary_authenticated'):
                return JsonResponse({
                    'success': False,
                    'error': '로그인이 필요합니다.'
                })
            
            # JSON 데이터 파싱
            data = json.loads(request.body)
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                return JsonResponse({
                    'success': False,
                    'error': '모든 필드를 입력해주세요.'
                })
            
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'error': '새 비밀번호가 일치하지 않습니다.'
                })
            
            if len(new_password) < 6:
                return JsonResponse({
                    'success': False,
                    'error': '새 비밀번호는 6자 이상이어야 합니다.'
                })
            
            # 현재 사용자 조회
            user_id = request.session.get('diary_member_id')
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '사용자를 찾을 수 없습니다.'
                })
            
            # 현재 비밀번호 확인
            if not check_password(current_password, user.password):
                return JsonResponse({
                    'success': False,
                    'error': '현재 비밀번호가 틀렸습니다.'
                })
            
            # 새 비밀번호 암호화 및 저장
            hashed_new_password = make_password(new_password)
            user.password = hashed_new_password
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': '비밀번호가 성공적으로 변경되었습니다.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class SendVerificationEmailView(View):
    """이메일 인증번호 발송 뷰"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'error': '이메일을 입력해주세요.'
                })
            
            # 이메일 형식 검증
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return JsonResponse({
                    'success': False,
                    'error': '올바른 이메일 형식을 입력해주세요.'
                })
            # 6자리 인증번호 생성
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # 기존 인증번호가 있다면 삭제
            EmailVerification.objects.filter(email=email).delete()
            
            # 새 인증번호 생성 (10분 후 만료)
            expires_at = timezone.now() + timedelta(minutes=10)
            EmailVerification.objects.create(
                email=email,
                verification_code=verification_code,
                expires_at=expires_at
            )
            
            # 이메일 발송
            subject = '[자금왕] 이메일 인증번호'
            message = f'''
안녕하세요. 자금왕입니다.

이메일 인증번호입니다.

인증번호: {verification_code}

이 인증번호는 10분 후에 만료됩니다.
인증번호를 입력하여 이메일 인증을 완료해주세요.

감사합니다.
            '''
            
            try:
                send_mail(
                    subject,
                    message,
                    SENDER_EMAIL,  # 발신자 이메일
                    [email],  # 수신자 이메일
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'success': True,
                    'message': '인증번호가 이메일로 발송되었습니다.',
                    'countdown_seconds': EMAIL_AUTH_VALID_TIME  # 10분
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'이메일 발송 중 오류가 발생했습니다: {str(e)}'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'인증번호 발송 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailView(View):
    """이메일 인증번호 확인 뷰"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            verification_code = data.get('verification_code')
            
            if not email or not verification_code:
                return JsonResponse({
                    'success': False,
                    'error': '이메일과 인증번호를 입력해주세요.'
                })
            
            try:
                # 인증번호 확인
                verification = EmailVerification.objects.get(
                    email=email,
                    verification_code=verification_code
                )
                
                # 만료 확인
                if verification.is_expired():
                    return JsonResponse({
                        'success': False,
                        'error': '인증번호가 만료되었습니다. 새로운 인증번호를 발송해주세요.'
                    })
                
                # 인증 완료 처리
                verification.is_verified = True
                verification.save()
                
                return JsonResponse({
                    'success': True,
                    'message': '이메일 인증이 완료되었습니다.'
                })
                
            except EmailVerification.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '인증번호가 올바르지 않습니다.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'인증 확인 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(View):
    """비밀번호 찾기 뷰"""
    def get(self, request):
        return render(request, 'diary/forgot_password.html')
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'error': '이메일을 입력해주세요.'
                })
            
            # 사용자 존재 확인
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '해당 이메일로 가입된 계정이 없습니다.'
                })
            
            # 6자리 인증번호 생성
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # 기존 인증번호가 있다면 삭제
            EmailVerification.objects.filter(email=email).delete()
            
            # 새 인증번호 생성 (10분 후 만료)
            expires_at = timezone.now() + timedelta(minutes=10)
            EmailVerification.objects.create(
                email=email,
                verification_code=verification_code,
                expires_at=expires_at
            )
            
            # 이메일 발송
            subject = '[자금왕] 비밀번호 찾기 인증번호'
            message = f'''
안녕하세요. 자금왕입니다.

이메일 인증번호입니다.

인증번호: {verification_code}

이 인증번호는 10분 후에 만료됩니다.
인증번호를 입력하여 이메일 인증을 완료해주세요.

감사합니다.
            '''
            
            try:
                send_mail(
                    subject,
                    message,
                    SENDER_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                return JsonResponse({
                    'success': True,
                    'message': '인증번호가 이메일로 발송되었습니다.'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'이메일 발송 중 오류가 발생했습니다: {str(e)}'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'비밀번호 찾기 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(View):
    """비밀번호 재설정 뷰"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            verification_code = data.get('verification_code')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            
            if not email or not verification_code or not new_password or not confirm_password:
                return JsonResponse({
                    'success': False,
                    'error': '모든 필드를 입력해주세요.'
                })
            
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'error': '새 비밀번호가 일치하지 않습니다.'
                })
            
            if len(new_password) < 6:
                return JsonResponse({
                    'success': False,
                    'error': '새 비밀번호는 6자 이상이어야 합니다.'
                })
            
            try:
                # 인증번호 확인
                verification = EmailVerification.objects.get(
                    email=email,
                    verification_code=verification_code
                )
                
                # 만료 확인
                if verification.is_expired():
                    return JsonResponse({
                        'success': False,
                        'error': '인증번호가 만료되었습니다. 새로운 인증번호를 발송해주세요.'
                    })
                
                # 사용자 조회
                user = User.objects.get(email=email)
                
                # 비밀번호 변경
                hashed_new_password = make_password(new_password)
                user.password = hashed_new_password
                user.save()
                
                # 인증번호 삭제
                verification.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': '비밀번호가 성공적으로 변경되었습니다.'
                })
                
            except EmailVerification.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '인증번호가 올바르지 않습니다.'
                })
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '사용자를 찾을 수 없습니다.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'비밀번호 재설정 중 오류가 발생했습니다: {str(e)}'
            })

@method_decorator(csrf_exempt, name='dispatch')
class CheckEmailDuplicateView(View):
    """이메일 중복 검사 뷰"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({
                    'success': False,
                    'error': '이메일을 입력해주세요.'
                })
            
            # 이메일 형식 검증
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return JsonResponse({
                    'success': False,
                    'error': '올바른 이메일 형식을 입력해주세요.'
                })
            
            # 이메일 중복 확인
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': '이미 존재하는 이메일입니다.',
                    'is_duplicate': True
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': '사용 가능한 이메일입니다.',
                    'is_duplicate': False
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 요청 형식입니다.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'중복 검사 중 오류가 발생했습니다: {str(e)}'
            })

def login_popup(request):
    return render(request, 'diary/diary_login_popup.html')