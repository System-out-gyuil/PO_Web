from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from diary.models import TossPaymentBillingKey, User, PayAmount, PayHistory
from diary.toss_payments import get_toss_auth_header, update_user_use_date
from diary.solapi import solapi_api
import json
import logging
import requests
import uuid

logger = logging.getLogger(__name__)

# 토스페이먼츠 API 설정
TOSS_API_URL = "https://api.tosspayments.com"

class Command(BaseCommand):
  help = 'Toss Payments 자동 결제 처리'

  def handle(self, *args, **options):
    try:
      # 현재 시간
      now = timezone.now()
      current_minute = now.replace(second=0, microsecond=0)
      
      print(f"자동 결제 처리 시작 - 현재 시간: {now}")
      print(f"현재 시간 (분 단위): {current_minute}")
      logger.info(f"자동 결제 처리 시작 - 현재 시간: {now}")
      logger.info(f"현재 시간 (분 단위): {current_minute}")
      
      # 현재 분부터 다음 분까지의 시간 범위에서 rebill_date가 있는 빌링키 조회
      next_minute = current_minute + timedelta(minutes=1)
      
      print(f"조회 시간 범위: {current_minute} ~ {next_minute}")
      logger.info(f"조회 시간 범위: {current_minute} ~ {next_minute}")
      
      # billing_type이 1이고 billing_activate가 True인 빌링키들 조회
      billing_keys = TossPaymentBillingKey.objects.filter(
        billing_type='1',
        billing_activate=True,
        rebill_date__gte=current_minute,
        rebill_date__lt=next_minute
      )
      
      print(f"처리할 빌링키 개수: {billing_keys.count()}")
      logger.info(f"처리할 빌링키 개수: {billing_keys.count()}")
      
      # 모든 빌링키의 rebill_date 출력
      all_billing_keys = TossPaymentBillingKey.objects.filter(
        billing_type='1',
        billing_activate=True
      )
      print(f"전체 활성화된 1개월 구독 빌링키 개수: {all_billing_keys.count()}")
      logger.info(f"전체 활성화된 1개월 구독 빌링키 개수: {all_billing_keys.count()}")
      for bk in all_billing_keys:
        print(f"빌링키 ID: {bk.id}, user: {bk.user.id}, rebill_date: {bk.rebill_date}")
        logger.info(f"빌링키 ID: {bk.id}, user: {bk.user.id}, rebill_date: {bk.rebill_date}")
      
      success_count = 0
      fail_count = 0
      
      for billing_key in billing_keys:
        try:
          logger.info(f"빌링키 자동 결제 시작 - user: {billing_key.user.id}, billing_key: {billing_key.billing_key}")
          
          # 1개월 결제 금액 설정
          amount = 150000
          order_name = "1개월 이용권"
          
          # 토스페이먼츠 빌링키 결제 API 호출
          url = f"{TOSS_API_URL}/v1/billing/{billing_key.billing_key}"
          headers = {
            'Authorization': get_toss_auth_header(),
            'Content-Type': 'application/json'
          }
          
          # 고유한 주문 ID 생성
          order_id = f"auto_order_{uuid.uuid4().hex[:16]}"
          
          payload = {
            "customerKey": billing_key.billing_data.get('customerKey'),
            "amount": amount,
            "orderId": order_id,
            "orderName": order_name,
            "customerEmail": billing_key.user.email,
            "customerName": billing_key.user.name,
            "taxFreeAmount": 0,
          }
          
          response = requests.post(url, json=payload, headers=headers)
          
          if response.status_code == 200:
            payment_data_json = response.json()
            
            # billing_success_data에 response 텍스트 저장
            billing_key.billing_success_data = response.text
            billing_key.last_billing_date = timezone.now()
            
            # 다음 결제일 설정 (30일 후)
            if billing_key.user.use_date:
              if hasattr(billing_key.user.use_date, 'date'):
                current_use_date = billing_key.user.use_date.date()
              else:
                current_use_date = billing_key.user.use_date
              
              # 남은 기간 + 30일 후를 다음 결제일로 설정
              next_billing_date = current_use_date + timedelta(days=30)
              billing_key.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
            else:
              # use_date가 없는 경우 오늘 + 30일
              next_billing_date = timezone.now().date() + timedelta(days=30)
              billing_key.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
            
            billing_key.save()
            
            # 사용자 use_date 업데이트 (1개월 추가)
            if billing_key.user.use_date:
              if hasattr(billing_key.user.use_date, 'date'):
                current_use_date = billing_key.user.use_date.date()
              else:
                current_use_date = billing_key.user.use_date
              
              # 남은 기간 + 30일로 업데이트
              new_use_date = current_use_date + timedelta(days=30)
              billing_key.user.use_date = new_use_date
              billing_key.user.save()
            else:
              # use_date가 없는 경우 오늘 + 30일
              new_use_date = timezone.now().date() + timedelta(days=30)
              billing_key.user.use_date = new_use_date
              billing_key.user.save()
            
            # 결제 성공 기록 저장
            PayHistory.objects.create(
              user=billing_key.user,
              payment_data={
                'success': True,
                'billing_key_data': {
                  'billing_key': billing_key.billing_key,
                  'billing_type': '1',
                  'amount': amount,
                  'order_id': order_id,
                  'order_name': order_name,
                  'payment_key': payment_data_json.get('paymentKey'),
                  'toss_response': payment_data_json,
                  'auto_payment': True
                }
              },
              billing_success_data=response.text
            )
            
            success_count += 1
            logger.info(f"자동 결제 성공 - user: {billing_key.user.id}, order_id: {order_id}")
            
          else:
            error_data = response.json()
            
            # 결제 실패 기록 저장
            PayHistory.objects.create(
              user=billing_key.user,
              payment_data={
                'success': False,
                'error_info': {
                  'billing_type': '1',
                  'amount': amount,
                  'order_id': order_id,
                  'order_name': order_name,
                  'error_code': error_data.get('code'),
                  'error_message': error_data.get('message'),
                  'toss_error_response': error_data,
                  'http_status': response.status_code,
                  'auto_payment': True
                }
              }
            )
            
            fail_count += 1
            logger.error(f"자동 결제 실패 - user: {billing_key.user.id}, status: {response.status_code}, error: {error_data}")
            
        except Exception as e:
          fail_count += 1
          logger.error(f"자동 결제 처리 중 오류 - user: {billing_key.user.id}, error: {str(e)}")
          
          # 서버 오류 기록 저장
          try:
            PayHistory.objects.create(
              user=billing_key.user,
              payment_data={
                'success': False,
                'error_info': {
                  'billing_type': '1',
                  'error_code': 'AUTO_PAYMENT_SERVER_ERROR',
                  'error_message': f'자동 결제 서버 오류: {str(e)}',
                  'error_type': type(e).__name__,
                  'error_details': str(e),
                  'auto_payment': True
                }
              }
            )
          except:
            pass
      
      logger.info(f"자동 결제 처리 완료 - 성공: {success_count}, 실패: {fail_count}")
      self.stdout.write(
        self.style.SUCCESS(f'자동 결제 처리 완료 - 성공: {success_count}, 실패: {fail_count}')
      )
      
    except Exception as e:
      logger.error(f"자동 결제 시스템 오류: {str(e)}")
      self.stdout.write(
        self.style.ERROR(f'자동 결제 시스템 오류: {str(e)}')
      ) 