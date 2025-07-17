from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import User, BaseAttribute, BaseAttributeDetail, Attribute
import json

class LoginView(View):
    def get(self, request):
        return render(request, 'diary/diary_login.html')
    
    def post(self, request):
        member_id = request.POST.get('member_id')
        member_pw = request.POST.get('member_pw')

        print(member_id, member_pw)

        try:
            member = User.objects.get(email=member_id, password=member_pw)

            # 로그인 성공 → 세션 저장
            request.session['diary_authenticated'] = True
            request.session['diary_member_id'] = member.id  # 👉 해당 행의 id 저장

            print(member.id)

            if member.id:
                return redirect('diary_list')

        except User.DoesNotExist:
            return render(request, 'diary/diary_login.html', {
                'error': '아이디 또는 비밀번호가 틀렸습니다.'
            })

@method_decorator(csrf_exempt, name='dispatch')
class SignupView(View):
    def post(self, request):
        try:
            # JSON 데이터 파싱
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({
                    'success': False,
                    'error': '이메일과 비밀번호를 모두 입력해주세요.'
                })
            
            # 이메일 중복 확인
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': '이미 존재하는 이메일입니다.'
                })
            
            # 사용자 생성 (테스트용으로 name은 email과 동일하게 설정)
            user = User.objects.create(
                name=email,
                email=email,
                password=password
            )
            
            # 기본 속성들을 사용자에게 부여
            self._create_default_attributes(user)
            
            return JsonResponse({
                'success': True,
                'message': '회원가입이 완료되었습니다.',
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
            '지역',        # 2. baseattribute
            '매출',        # 3. baseattribute
            '기대출',      # 4. baseattributedetail
            '신용점수',    # 5. baseattribute
            '개업년월',    # 6. baseattribute
            '나이',        # 7. baseattribute
            '업종',        # 8. baseattribute
            '경력',        # 9. baseattribute
            '직원수'       # 10. baseattribute
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
    
class LogoutView(View):
    def get(self, request):
        return render(request, 'diary/logout.html')
