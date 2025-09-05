from django.shortcuts import render
from .models import User, TossPaymentBillingKey
from config import TOSS_PAYMENTS_CLIENT_KEY
import uuid
from datetime import datetime, timedelta
from django.utils import timezone

def diary_pay(request):

    is_admin = request.session.get('is_admin', False),
    is_authenticated = request.session.get('is_authenticated', False),
    user_id = request.session.get('diary_member_id')
    user = User.objects.get(id=user_id)
    user_name = user.name
    user_email = user.email
    client_key = TOSS_PAYMENTS_CLIENT_KEY
    customer_key = f"customer_{uuid.uuid4().hex[:16]}"

    billing_type = None
    last_billing_date = None
    rebill_date = None
    billing_activate = None
    has_active_subscription = False
    current_use_date = None
    remaining_days = 0
    has_billing = False
    card_info = None

    try:
        # 활성화된 빌링키 조회
        billing_key = TossPaymentBillingKey.objects.filter(user=user).first()
        if billing_key:
            print(f'true')
            billing_type = billing_key.billing_type
            last_billing_date = billing_key.last_billing_date
            rebill_date = billing_key.rebill_date
            billing_activate = billing_key.billing_activate
            has_billing = True

            print(f'billing_type: {billing_type}')
            print(f'billing_activate: {billing_activate}')
            print(f'has_active_subscription: {has_active_subscription}')
            
            # 카드 정보 추출
            billing_data = billing_key.billing_data
            if billing_data and 'card' in billing_data:
                card_info = {
                    'number': billing_data['card'].get('number', '****'),
                    'company': billing_data.get('cardCompany', ''),
                    'ownerType': billing_data['card'].get('ownerType', ''),
                    'acquireStatus': billing_data['card'].get('acquireStatus', '')
                }
            else:
                card_info = None
            
            # 1개월 구독이 활성화된 경우에만 has_active_subscription = True
            if billing_type == '1' and billing_activate:
                has_active_subscription = True
            else:
                has_active_subscription = False
        else:
            print(f'false')
            has_billing = False


        # 사용자의 현재 사용 기간 확인
        if user.use_date:
            # use_date가 datetime인 경우 date로 변환
            if hasattr(user.use_date, 'date'):
                current_use_date = user.use_date.date()
            else:
                current_use_date = user.use_date
            
            # 현재 날짜와 비교하여 남은 일수 계산
            today = timezone.now().date()
            remaining_days = (current_use_date - today).days
            if remaining_days < 0:
                remaining_days = 0
        else:
            current_use_date = timezone.now().date()
            remaining_days = 0

    except Exception as e:
        print(f"빌링키 조회 오류: {e}")
        pass

    context = {
      'is_authenticated': is_authenticated,
      'is_admin': is_admin,
      'user_name': user_name,
      'user_email': user_email,
      'client_key': client_key,
      'customer_key': customer_key,
      'billing_type': billing_type,
      'last_billing_date': last_billing_date,
      'rebill_date': rebill_date,
      'billing_activate': billing_activate,
      'has_active_subscription': has_active_subscription,
      'current_use_date': current_use_date,
      'remaining_days': remaining_days,
      'has_billing': has_billing,
      'card_info': card_info
    }

    return render(request, 'diary/diary_pay.html', context)
