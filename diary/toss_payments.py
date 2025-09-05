from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import logging
import base64
import requests
from config import TOSS_PAYMENTS_CLIENT_KEY, TOSS_PAYMENTS_SECRET_KEY
from .models import TossPaymentBillingKey, User, PayAmount, PayHistory
import uuid

logger = logging.getLogger(__name__)

# 토스페이먼츠 API 설정
TOSS_API_URL = "https://api.tosspayments.com"

def update_user_use_date(user, billing_type):
    """사용자의 use_date를 업데이트하는 함수"""
    try:
        
        # 현재 사용 가능일 확인
        if user.use_date:
            # use_date가 datetime인 경우 date로 변환
            if hasattr(user.use_date, 'date'):
                current_use_date = user.use_date.date()
            else:
                current_use_date = user.use_date
        else:
            current_use_date = timezone.now().date()
        
        # 남은 기간 계산
        today = timezone.now().date()
        remaining_days = (current_use_date - today).days
        if remaining_days < 0:
            remaining_days = 0
        
        # 구매한 기간 추가 (날짜 기준)
        if billing_type == '2':  # 6개월
            # 현재 사용 가능일 + 6개월
            new_use_date = current_use_date + relativedelta(months=6)
        elif billing_type == '3':  # 1년
            # 현재 사용 가능일 + 1년
            new_use_date = current_use_date + relativedelta(years=1)
        else:
            new_use_date = current_use_date
        
        user.use_date = new_use_date
        user.save()
        
        logger.info(f"사용자 use_date 업데이트 완료 - user: {user.id}, current_date: {current_use_date}, new_date: {new_use_date}")
        
    except Exception as e:
        logger.error(f"use_date 업데이트 중 오류: {str(e)}")

def get_toss_auth_header():
    """토스페이먼츠 API 인증 헤더 생성"""
    secret_key_with_colon = f"{TOSS_PAYMENTS_SECRET_KEY}:"
    encoded_key = base64.b64encode(secret_key_with_colon.encode('utf-8')).decode('utf-8')
    print(f'encoded_key: {encoded_key}')
    return f"Basic {encoded_key}"

def issue_billing_key(auth_key, customer_key):
    """빌링키 발급 API 호출"""
    try:

        print(f'auth_key: {auth_key}')
        print(f'customer_key: {customer_key}')

        url = f"{TOSS_API_URL}/v1/billing/authorizations/issue"
        headers = {
            'Authorization': get_toss_auth_header(),
            'Content-Type': 'application/json'
        }
        payload = {
            "authKey": auth_key,
            "customerKey": customer_key
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f'response: {response}')
        print(f'response status: {response.status_code}')
        print(f'response headers: {response.headers}')
        print(f'response content: {response.text}')
        
        # 요청 정보도 로그에 추가
        print(f'Request URL: {url}')
        print(f'Request Headers: {headers}')
        print(f'Request Payload: {payload}')

        if response.status_code == 200:
            data = response.json()
            logger.info(f"빌링키 발급 성공 - customerKey: {customer_key}, billingKey: {data.get('billingKey')}")
            return {
                'success': True,
                'data': data
            }
        else:
            error_data = response.json()
            logger.error(f"빌링키 발급 실패 - status: {response.status_code}, error: {error_data}")
            return {
                'success': False,
                'error': error_data
            }
            
    except Exception as e:
        logger.error(f"빌링키 발급 중 오류: {str(e)}")
        return {
            'success': False,
            'error': {'message': str(e)}
        }

def payment(request):
  print("=================================== payment ===================================")
  try:
    user_id = request.session.get('diary_member_id')
    user = User.objects.get(id=user_id)
    payment_data = user.toss_payment_billing_key.payment_data
    payment_type = user.toss_payment_billing_key.payment_type
    billing_key = user.toss_payment_billing_key.billing_key

    pay_amount = PayAmount.objects.get(id=payment_type)

    amount = pay_amount.price

    print(f'payment_data: {payment_data}')
    print(f'amount: {amount}')
    print(f'payment_type: {payment_type}')

    url = f"{TOSS_API_URL}/v1/billing/{billing_key}"
    headers = {
        'Authorization': get_toss_auth_header(),
        'Content-Type': 'application/json'
    }
    
    # 고유한 주문 ID 생성
    order_id = f"order_{uuid.uuid4().hex[:16]}"
    
    payload = {
        "customerKey": payment_data.get('customerKey'),
        "amount": amount,
        "orderId": order_id,
        "orderName": pay_amount.amount_name,
        "customerEmail": user.email,
        "customerName": user.name,
        "taxFreeAmount": 0,
    }
    
    response = requests.post(url, json=payload, headers=headers)

    print(f'response: {response}')
    print(f'response status: {response.status_code}')
    print(f'response headers: {response.headers}')
    print(f'response content: {response.text}')

    if response.status_code == 200:
      payment_result_json = response.json()
      payment_result_text = response.text
      
      # billing_success_data에 response 텍스트 저장 (역슬래시 제거)
      user.toss_payment_billing_key.billing_success_data = response.text
      print(f"payment() 함수 - billing_success_data 저장: {user.toss_payment_billing_key.billing_success_data}")
      
      # 모든 결제에 대해 last_billing_date 업데이트
      user.toss_payment_billing_key.last_billing_date = timezone.now()
      print(f"payment() 함수 - last_billing_date 업데이트: {user.toss_payment_billing_key.last_billing_date}")
      
      if payment_type == '1':
        # 1개월 구독의 경우 rebill_date 업데이트 (다음 결제일)
        if user.use_date:
          if hasattr(user.use_date, 'date'):
            current_use_date = user.use_date.date()
          else:
            current_use_date = user.use_date
          
          # 남은 기간 + 30일 후를 다음 결제일로 설정
          next_billing_date = current_use_date + timedelta(days=30)
          # datetime으로 변환하여 시, 분, 초 포함
          user.toss_payment_billing_key.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
          print(f"payment() 함수 - rebill_date 설정: {user.toss_payment_billing_key.rebill_date}")
        else:
          # use_date가 없는 경우 오늘 + 30일
          next_billing_date = timezone.now().date() + timedelta(days=30)
          # datetime으로 변환하여 시, 분, 초 포함
          user.toss_payment_billing_key.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
          print(f"payment() 함수 - rebill_date 설정 (기본): {user.toss_payment_billing_key.rebill_date}")
        
        user.use_date = timezone.now() + timedelta(days=30)
        
      elif payment_type == '2':
        # 6개월 구매 - 현재 사용 가능일 + 6개월
        if user.use_date:
          if hasattr(user.use_date, 'date'):
            current_use_date = user.use_date.date()
          else:
            current_use_date = user.use_date
          new_use_date = current_use_date + relativedelta(months=6)
        else:
          new_use_date = timezone.now() + relativedelta(months=6)
        user.use_date = new_use_date
        
      elif payment_type == '3':
        # 1년 구매 - 현재 사용 가능일 + 1년
        if user.use_date:
          if hasattr(user.use_date, 'date'):
            current_use_date = user.use_date.date()
          else:
            current_use_date = user.use_date
          new_use_date = current_use_date + relativedelta(years=1)
        else:
          new_use_date = timezone.now() + relativedelta(years=1)
        user.use_date = new_use_date

      user.save()
      user.toss_payment_billing_key.save()
      
      # 결제 성공 기록 저장
      PayHistory.objects.create(
        user=user,
        payment_data={
          'success': True,
          'billing_key_data': {
            'billing_key': billing_key,
            'billing_type': payment_type,
            'amount': amount,
            'order_id': order_id,
            'order_name': pay_amount.amount_name,
            'payment_key': payment_result_json.get('paymentKey'),
            'toss_response': payment_result_json
          }
        },
        billing_success_data=response.text
      )
      
      logger.info(f"payment() 함수 결제 성공 - user: {user_id}, payment_type: {payment_type}, amount: {amount}")
      
    else:
      error_data = response.json()
      
      # 결제 실패 기록 저장
      PayHistory.objects.create(
        user=user,
        payment_data={
          'success': False,
          'error_info': {
            'billing_type': payment_type,
            'amount': amount,
            'order_id': order_id,
            'order_name': pay_amount.amount_name,
            'error_code': error_data.get('code'),
            'error_message': error_data.get('message'),
            'toss_error_response': error_data,
            'http_status': response.status_code
          }
        }
      )
      
      logger.error(f"payment() 함수 결제 실패 - status: {response.status_code}, error: {error_data}")
      
  except Exception as e:
    logger.error(f"payment() 함수 처리 중 오류: {str(e)}")
    
    # 서버 오류 기록 저장
    try:
      PayHistory.objects.create(
        user=user,
        payment_data={
          'success': False,
          'error_info': {
            'billing_type': payment_type if 'payment_type' in locals() else 'unknown',
            'error_code': 'SERVER_ERROR',
            'error_message': f'서버 오류가 발생했습니다: {str(e)}',
            'error_type': type(e).__name__,
            'error_details': str(e)
          }
        }
      )
    except:
      pass  # PayHistory 저장 실패해도 메인 로직은 계속 진행

class TossPaymentsView(View):
  def get(self, request):

    user_id = request.session.get('diary_member_id')
    if not user_id:
      logger.warning("세션에 사용자 정보가 없습니다.")
      user = None
      user_name = "로그인이 필요합니다"
      user_email = "로그인이 필요합니다"
    else:
      user = User.objects.get(id=user_id)
      user_name = user.name
      user_email = user.email

    print(f'user: {user_name}')
    print(f'user: {user_email}')

    customer_key = f"customer_{uuid.uuid4().hex[:16]}"
    print(f'customer_key: {customer_key}')

    client_key = TOSS_PAYMENTS_CLIENT_KEY
    print(f'client_key: {client_key}')

    context = {
      'user_name': user_name,
      'user_email': user_email,
      'customer_key': customer_key,
      'client_key': client_key
    }

    return render(request, 'toss_payments/toss_payments.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class TossPaymentsSuccessView(View):
  def get(self, request):
    # GET 요청 처리 (Toss Payments SDK가 자동으로 호출)
    customer_key = request.GET.get('customerKey')
    auth_key = request.GET.get('authKey')
    
    # 세션에서 billing_type 가져오기
    billing_type = request.session.get('pending_billing_type')
    if billing_type:
      # 사용 후 세션에서 제거
      del request.session['pending_billing_type']
    
    return self._process_success(request, customer_key, auth_key, billing_type)
  
  def post(self, request):
    try:
      # POST body에서 데이터 추출
      data = json.loads(request.body)
      customer_key = data.get('customerKey')
      auth_key = data.get('authKey')
      
      # 세션에서 billing_type 가져오기
      billing_type = request.session.get('pending_billing_type')
      if billing_type:
        # 사용 후 세션에서 제거
        del request.session['pending_billing_type']
      
      return self._process_success(request, customer_key, auth_key, billing_type)
      
    except Exception as e:
      logger.error(f"결제 인증 성공 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)
  
  def _process_success(self, request, customer_key, auth_key, billing_type):
    try:
      # 로깅
      logger.info(f"결제 인증 성공 - customerKey: {customer_key}, authKey: {auth_key}, billing_type: {billing_type}")
      
      # 세션에서 사용자 정보 확인
      user_id = request.session.get('diary_member_id')
      if not user_id:
        logger.warning("세션에 사용자 정보가 없습니다.")
        return JsonResponse({
          'status': 'error',
          'message': '로그인이 필요합니다.'
        }, status=401)

      user = User.objects.get(id=user_id)

      print(f'user: {user}')
      print(f'customer_key: {customer_key}')
      print(f'billing_type: {billing_type}')
      print(f'Session user_id: {user_id}')
      
      # 빌링키 발급 시도
      result = issue_billing_key(auth_key, customer_key)
      
      # 빌링키 발급 성공 시 데이터베이스에 저장
      if result['success']:
        try:
          
          billing_data = result['data']

          print(f'billing_data: {billing_data}')
          
          # 기존 빌링키가 있는지 확인
          existing_billing = TossPaymentBillingKey.objects.filter(
            user=user,
            billing_key=billing_data.get('billingKey')
          ).first()
            
          if not existing_billing:

              if billing_type == '1':
                # 새로운 빌링키 저장
                TossPaymentBillingKey.objects.create(
                  user=user,
                  billing_key=billing_data.get('billingKey'),
                  billing_data=billing_data,
                  billing_type=billing_type,
                  billing_status="1",
                  billing_activate=True,
                  last_billing_date=timezone.now(),
                  billing_success_data=json.dumps(billing_data, ensure_ascii=False, separators=(',', ':'))
                )
              else:
                # 새로운 빌링키 저장
                TossPaymentBillingKey.objects.create(
                  user=user,
                  billing_key=billing_data.get('billingKey'),
                  billing_data=billing_data,
                  billing_type=billing_type,
                  billing_status="1",
                  billing_activate=False,
                  last_billing_date=timezone.now(),
                  billing_success_data=json.dumps(billing_data, ensure_ascii=False, separators=(',', ':'))
                )
                logger.info(f"새로운 빌링키 저장 완료 - user: {user_id}, billingKey: {billing_data.get('billingKey')}")
                
              # 구매 완료 시 사용자의 use_date 업데이트
              if billing_type in ['2', '3']:  # 6개월 또는 1년 구매
                update_user_use_date(user, billing_type)
              elif billing_type == '1':  # 1개월 구독의 경우 rebill_date 설정
                billing_key = TossPaymentBillingKey.objects.get(
                  user=user,
                  billing_key=billing_data.get('billingKey')
                )
                if user.use_date:
                  if hasattr(user.use_date, 'date'):
                    current_use_date = user.use_date.date()
                  else:
                    current_use_date = user.use_date
                  next_billing_date = current_use_date + timedelta(days=30)
                else:
                  next_billing_date = timezone.now() + timedelta(days=30)
                
                # datetime으로 변환하여 시, 분, 초 포함
                if isinstance(next_billing_date, datetime):
                  billing_key.rebill_date = next_billing_date
                else:
                  billing_key.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
                billing_key.save()
                print(f"TossPaymentsSuccessView - rebill_date 설정: {billing_key.rebill_date}")
                
          else:
            logger.info(f"이미 존재하는 빌링키 - user: {user_id}, billingKey: {billing_data.get('billingKey')}")
            
            # 기존 빌링키가 있는 경우에도 결제 처리
            try:
              payment(request)
              
              # 빌링키로 결제한 결과를 billing_success_data에 저장
              existing_billing_key = TossPaymentBillingKey.objects.get(
                user=user,
                billing_key=billing_data.get('billingKey')
              )
              # payment() 함수에서 이미 billing_success_data가 업데이트되었으므로
              # existing_billing_key를 다시 조회하여 최신 데이터 가져오기
              existing_billing_key.refresh_from_db()
              
              # 결제 성공 기록 저장 (기존 빌링키 사용)
              PayHistory.objects.create(
                user=user,
                payment_data={
                  'success': True,
                  'billing_key_data': {
                    'billing_key': billing_data.get('billingKey'),
                    'billing_type': billing_type,
                    'amount': 150000 if billing_type == '1' else (720000 if billing_type == '2' else 1200000),
                    'order_id': f"order_{uuid.uuid4().hex[:16]}",
                    'order_name': "1개월 이용권" if billing_type == '1' else ("6개월 이용권" if billing_type == '2' else "1년 이용권"),
                    'payment_key': 'existing_billing_key',
                    'toss_response': billing_data
                  }
                },
                billing_success_data=existing_billing_key.billing_success_data
              )
              
              logger.info(f"기존 빌링키로 결제 성공 - user: {user_id}, billing_type: {billing_type}")
              
            except Exception as e:
              logger.error(f"기존 빌링키 결제 처리 중 오류: {str(e)}")
              
              # 결제 실패 기록 저장
              PayHistory.objects.create(
                user=user,
                payment_data={
                  'success': False,
                  'error_info': {
                    'billing_type': billing_type,
                    'error_code': 'PAYMENT_PROCESSING_ERROR',
                    'error_message': f'기존 빌링키 결제 처리 중 오류: {str(e)}',
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                  }
                }
              )
                
        except Exception as e:
          logger.error(f"빌링키 저장 중 오류: {str(e)}")
            # 저장 실패해도 API 응답은 성공으로 처리
      
      # 컨텍스트에 데이터 전달
      context = {
        'customer_key': customer_key,
        'auth_key': auth_key,
        'billing_result': result,
        'user_id': user_id
      }
      
      return render(request, 'toss_payments/success.html', context)
      
    except Exception as e:
      logger.error(f"결제 인증 성공 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TossPaymentsFailView(View):
  def get(self, request):
    # GET 요청 처리 (Toss Payments SDK가 자동으로 호출)
    error_code = request.GET.get('code')
    error_message = request.GET.get('message')
    
    # 세션에서 billing_type 가져오기
    billing_type = request.session.get('pending_billing_type')
    if billing_type:
      # 사용 후 세션에서 제거
      del request.session['pending_billing_type']
    
    return self._process_fail(request, error_code, error_message, billing_type)
  
  def post(self, request):
    try:
      # POST body에서 데이터 추출
      data = json.loads(request.body)
      error_code = data.get('code')
      error_message = data.get('message')
      
      # 세션에서 billing_type 가져오기
      billing_type = request.session.get('pending_billing_type')
      if billing_type:
        # 사용 후 세션에서 제거
        del request.session['pending_billing_type']
      
      return self._process_fail(request, error_code, error_message, billing_type)
      
    except Exception as e:
      logger.error(f"결제 인증 실패 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)
  
  def _process_fail(self, request, error_code, error_message, billing_type):
    try:
      # 로깅
      logger.error(f"결제 인증 실패 - code: {error_code}, message: {error_message}, billing_type: {billing_type}")
      
      # 세션에서 사용자 정보 확인
      user_id = request.session.get('diary_member_id')
      if user_id:
        try:
          user = User.objects.get(id=user_id)
          
          # 결제 실패 기록 저장
          PayHistory.objects.create(
            user=user,
            payment_data={
              'success': False,
              'error_info': {
                'billing_type': billing_type,
                'error_code': error_code,
                'error_message': error_message,
                'error_type': 'TOSS_PAYMENTS_AUTH_FAIL',
                'error_details': f'Toss Payments 인증 실패 - code: {error_code}, message: {error_message}'
              }
            }
          )
          
          logger.info(f"결제 인증 실패 기록 저장 완료 - user: {user_id}, billing_type: {billing_type}")
          
        except User.DoesNotExist:
          logger.warning(f"결제 인증 실패 시 사용자 조회 실패 - user_id: {user_id}")
        except Exception as e:
          logger.error(f"결제 인증 실패 기록 저장 중 오류: {str(e)}")
      
      # 컨텍스트에 데이터 전달
      context = {
        'error_code': error_code,
        'error_message': error_message,
        'billing_type': billing_type
      }
      
      return render(request, 'toss_payments/fail.html', context)
      
    except Exception as e:
      logger.error(f"결제 인증 실패 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PaymentAuthSuccessView(View):
  """결제 인증 성공 시 서버로 데이터 전송받는 API"""
  
  def post(self, request):
    try:
      data = json.loads(request.body)
      customer_key = data.get('customerKey')
      auth_key = data.get('authKey')
      
      # 여기서 데이터베이스에 저장하거나 필요한 처리 수행
      logger.info(f"서버로 전송된 인증 성공 데이터 - customerKey: {customer_key}, authKey: {auth_key}")
      
      # 세션에서 사용자 정보 확인
      user_id = request.session.get('diary_member_id')
      if user_id:
        try:
          user = User.objects.get(id=user_id)
          
          # 결제 인증 성공 기록 저장
          PayHistory.objects.create(
            user=user,
            payment_data={
              'success': True,
              'billing_key_data': {
                'billing_key': 'auth_success',
                'billing_type': 'auth',
                'amount': 0,
                'order_id': f"auth_{uuid.uuid4().hex[:16]}",
                'order_name': '카드 인증',
                'payment_key': auth_key,
                'toss_response': {
                  'customerKey': customer_key,
                  'authKey': auth_key
                }
              }
            }
          )
          
          logger.info(f"결제 인증 성공 기록 저장 완료 - user: {user_id}")
          
        except User.DoesNotExist:
          logger.warning(f"결제 인증 성공 시 사용자 조회 실패 - user_id: {user_id}")
        except Exception as e:
          logger.error(f"결제 인증 성공 기록 저장 중 오류: {str(e)}")
      
      return JsonResponse({
        'status': 'success',
        'message': '인증 정보가 성공적으로 저장되었습니다.',
        'data': {
          'customerKey': customer_key,
          'authKey': auth_key
        }
      })
      
    except json.JSONDecodeError:
      return JsonResponse({
        'status': 'error',
        'message': '잘못된 JSON 형식입니다.'
      }, status=400)
    except Exception as e:
      logger.error(f"결제 인증 성공 데이터 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class PaymentAuthFailView(View):
  """결제 인증 실패 시 서버로 데이터 전송받는 API"""
  
  def post(self, request):
    try:
      data = json.loads(request.body)
      error_code = data.get('errorCode')
      error_message = data.get('errorMessage')
      
      # 여기서 에러 로그를 저장하거나 필요한 처리 수행
      logger.error(f"서버로 전송된 인증 실패 데이터 - code: {error_code}, message: {error_message}")
      
      # 세션에서 사용자 정보 확인
      user_id = request.session.get('diary_member_id')
      if user_id:
        try:
          user = User.objects.get(id=user_id)
          
          # 결제 인증 실패 기록 저장
          PayHistory.objects.create(
            user=user,
            payment_data={
              'success': False,
              'error_info': {
                'billing_type': 'auth',
                'error_code': error_code,
                'error_message': error_message,
                'error_type': 'TOSS_PAYMENTS_AUTH_FAIL_API',
                'error_details': f'Toss Payments 인증 실패 API - code: {error_code}, message: {error_message}'
              }
            }
          )
          
          logger.info(f"결제 인증 실패 기록 저장 완료 - user: {user_id}")
          
        except User.DoesNotExist:
          logger.warning(f"결제 인증 실패 시 사용자 조회 실패 - user_id: {user_id}")
        except Exception as e:
          logger.error(f"결제 인증 실패 기록 저장 중 오류: {str(e)}")
      
      return JsonResponse({
        'status': 'success',
        'message': '에러 정보가 성공적으로 저장되었습니다.',
        'data': {
          'errorCode': error_code,
          'errorMessage': error_message
        }
      })
      
    except json.JSONDecodeError:
      return JsonResponse({
        'status': 'error',
        'message': '잘못된 JSON 형식입니다.'
      }, status=400)
    except Exception as e:
      logger.error(f"결제 인증 실패 데이터 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

class SubscriptionManagementView(LoginRequiredMixin, View):
  """구독 관리 페이지"""
  
  def get(self, request):
    # 사용자의 빌링키 목록 조회
    billing_keys = TossPaymentBillingKey.objects.filter(
      user=request.user,
      billing_activate=True
    ).order_by('-created_at')
    
    context = {
      'billing_keys': billing_keys,
    }
    
    return render(request, 'toss_payments/subscription_management.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class CancelSubscriptionView(View):
  """구독 취소 API"""
  
  def post(self, request):
    try:
      data = json.loads(request.body)
      billing_key_id = data.get('billingKeyId')
      billing_type = data.get('billingType')
      
      # 세션에서 사용자 정보 가져오기
      user_id = request.session.get('diary_member_id')
      if not user_id:
        return JsonResponse({
          'status': 'error',
          'message': '로그인이 필요합니다.'
        }, status=401)
      
      user = User.objects.get(id=user_id)
      
      if not billing_key_id and not billing_type:
        return JsonResponse({
          'status': 'error',
          'message': '빌링키 ID 또는 결제 타입이 필요합니다.'
        }, status=400)
      
      # 빌링키 조회 및 비활성화
      try:
        if billing_key_id:
          # 빌링키 ID로 조회
          billing_key = TossPaymentBillingKey.objects.get(
            id=billing_key_id,
            user=user
          )
        else:
          # 결제 타입으로 조회
          billing_key = TossPaymentBillingKey.objects.get(
            user=user,
            billing_type=billing_type,
            billing_activate=True
          )
        
        billing_key.billing_activate = False
        billing_key.rebill_date = None  # 구독 취소 시 다음 결제일 제거
        billing_key.save()
        
        logger.info(f"구독 취소 완료 - user: {user_id}, billingType: {billing_type}")
        
        return JsonResponse({
          'status': 'success',
          'message': '구독이 성공적으로 취소되었습니다.'
        })
        
      except TossPaymentBillingKey.DoesNotExist:
        return JsonResponse({
          'status': 'error',
          'message': '해당 빌링키를 찾을 수 없습니다.'
        }, status=404)
        
    except json.JSONDecodeError:
      return JsonResponse({
        'status': 'error',
        'message': '잘못된 JSON 형식입니다.'
      }, status=400)
    except Exception as e:
      logger.error(f"구독 취소 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RequestPaymentView(View):
  """빌링키로 바로 결제하는 API"""
  
  def get(self, request):
    return JsonResponse({
      'status': 'success',
      'message': 'RequestPaymentView가 정상적으로 작동합니다.',
      'url': '/sales/api/payment/request-payment/'
    })
  
  def post(self, request):
    print(f"RequestPaymentView POST 요청 받음: {request.path}")
    print(f"request.method: {request.method}")
    print(f"request.body: {request.body}")
    print(f"request.META.get('HTTP_HOST'): {request.META.get('HTTP_HOST')}")
    print(f"request.META.get('PATH_INFO'): {request.META.get('PATH_INFO')}")
    try:
      data = json.loads(request.body)
      print(f"parsed data: {data}")
      billing_type = data.get('billingType')
      print(f"billing_type: {billing_type}, type: {type(billing_type)}")
      
      # 세션에서 사용자 정보 가져오기
      user_id = request.session.get('diary_member_id')
      print(f"user_id: {user_id}")
      if not user_id:
        print("사용자 ID가 없음")
        return JsonResponse({
          'status': 'error',
          'message': '로그인이 필요합니다.'
        }, status=401)
      
      user = User.objects.get(id=user_id)
      print(f"사용자 조회 성공: {user.name}")
      
      if not billing_type:
        return JsonResponse({
          'status': 'error',
          'message': '결제 타입이 필요합니다.'
        }, status=400)
      
      # 활성화된 빌링키 조회
      try:
        print(f"빌링키 조회 시작 - user: {user.id}, billing_type: {billing_type}")
        
        # 먼저 해당 사용자의 모든 빌링키 조회
        all_billing_keys = TossPaymentBillingKey.objects.filter(user=user)
        print(f"사용자의 모든 빌링키 개수: {all_billing_keys.count()}")
        for bk in all_billing_keys:
          print(f"빌링키 - ID: {bk.id}, type: {bk.billing_type}, activate: {bk.billing_activate}")
        
        # 빌링키 조회 - 사용자의 빌링키가 있는지만 확인
        billing_key_obj = TossPaymentBillingKey.objects.filter(user=user).first()
        if not billing_key_obj:
          raise TossPaymentBillingKey.DoesNotExist("사용자의 빌링키가 없습니다.")
        
        print(f"기존 빌링키 사용: {billing_key_obj.billing_key}")
        
        # billing_type을 요청된 타입으로 업데이트
        billing_key_obj.billing_type = billing_type
        billing_key_obj.save()
        print(f"빌링키 타입 업데이트: {billing_type}")
        
        # 1개월 구독인 경우 billing_activate를 True로 업데이트
        if billing_type == '1':
          billing_key_obj.billing_activate = True
          
          # 다음 결제일을 남은 사용기간 기준으로 계산
          if user.use_date:
            if hasattr(user.use_date, 'date'):
              current_use_date = user.use_date.date()
            else:
              current_use_date = user.use_date
            
            # 남은 기간 + 30일 후를 다음 결제일로 설정
            next_billing_date = current_use_date + timedelta(days=30)
            # datetime으로 변환하여 시, 분, 초 포함
            if isinstance(next_billing_date, datetime):
              billing_key_obj.rebill_date = next_billing_date
            else:
              billing_key_obj.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
            print(f"다음 결제일 설정: {billing_key_obj.rebill_date}")
          else:
            # use_date가 없는 경우 오늘 + 30일
            next_billing_date = timezone.now() + timedelta(days=30)
            billing_key_obj.rebill_date = next_billing_date
            print(f"다음 결제일 설정 (기본): {billing_key_obj.rebill_date}")
          
          billing_key_obj.save()
          print(f"1개월 구독 활성화: billing_activate = True")
        
        # 결제 금액 설정
        if billing_type == '1':  # 1개월
          amount = 150000
          order_name = "1개월 이용권"
        elif billing_type == '2':  # 6개월
          amount = 720000
          order_name = "6개월 이용권"
        elif billing_type == '3':  # 1년
          amount = 1200000
          order_name = "1년 이용권"
        else:
          return JsonResponse({
            'status': 'error',
            'message': '올바른 결제 타입이 아닙니다.'
          }, status=400)
        
        # 토스페이먼츠 빌링키 결제 API 호출
        url = f"{TOSS_API_URL}/v1/billing/{billing_key_obj.billing_key}"
        headers = {
          'Authorization': get_toss_auth_header(),
          'Content-Type': 'application/json'
        }
        
        # 고유한 주문 ID 생성
        order_id = f"order_{uuid.uuid4().hex[:16]}"
        
        payload = {
          "customerKey": billing_key_obj.billing_data.get('customerKey'),
          "amount": amount,
          "orderId": order_id,
          "orderName": order_name,
          "customerEmail": user.email,
          "customerName": user.name,
          "taxFreeAmount": 0,
        }
        
        response = requests.post(url, json=payload, headers=headers)

        print(f"response: {response}")
        print(f"response status: {response.status_code}")
        print(f"response headers: {response.headers}")
        print(f"response content: {response.text}")
        
        
        if response.status_code == 200:
          payment_data_text = response.text  # 원본 텍스트
          payment_data_json = response.json()  # JSON 객체로 파싱
          
          # billing_success_data에 response 텍스트 저장 (역슬래시 제거)
          billing_key_obj.billing_success_data = response.text
          print(f"RequestPaymentView - billing_success_data 저장: {billing_key_obj.billing_success_data}")
          
          # 모든 결제에 대해 last_billing_date 업데이트
          billing_key_obj.last_billing_date = timezone.now()
          billing_key_obj.save()
          print(f"last_billing_date 업데이트: {billing_key_obj.last_billing_date}")
          
          # 결제 성공 시 사용자 use_date 업데이트
          if billing_type in ['2', '3']:  # 6개월 또는 1년 구매
            update_user_use_date(user, billing_type)
          elif billing_type == '1':  # 1개월 구독
            # 1개월 구독의 경우 rebill_date 업데이트 (다음 결제일)
            if user.use_date:
              if hasattr(user.use_date, 'date'):
                current_use_date = user.use_date.date()
              else:
                current_use_date = user.use_date
              
              # 남은 기간 + 30일 후를 다음 결제일로 설정
              next_billing_date = current_use_date + timedelta(days=30)
              if isinstance(next_billing_date, datetime):
                billing_key_obj.rebill_date = next_billing_date
              else:
                billing_key_obj.rebill_date = datetime.combine(next_billing_date, timezone.now().time())
              print(f"rebill_date 설정: {billing_key_obj.rebill_date}")
            else:
              # use_date가 없는 경우 오늘 + 30일
              next_billing_date = timezone.now() + timedelta(days=30)
              billing_key_obj.rebill_date = next_billing_date
              print(f"rebill_date 설정 (기본): {next_billing_date}")
            
            billing_key_obj.save()
            
            # use_date 업데이트 (남은 사용기간 + 30일)
            if user.use_date:
              if hasattr(user.use_date, 'date'):
                current_use_date = user.use_date.date()
              else:
                current_use_date = user.use_date
              
              # 남은 기간 + 30일로 업데이트
              new_use_date = current_use_date + timedelta(days=30)
              if isinstance(new_use_date, datetime):
                user.use_date = new_use_date
              else:
                user.use_date = datetime.combine(new_use_date, timezone.now().time())
              user.save()
              print(f"use_date 업데이트: {current_use_date} -> {user.use_date}")
            else:
              # use_date가 없는 경우 오늘 + 30일
              new_use_date = timezone.now() + timedelta(days=30)
              user.use_date = new_use_date
              user.save()
              print(f"use_date 설정 (기본): {new_use_date}")
          
          # 결제 성공 기록 저장
          PayHistory.objects.create(
            user=user,
            payment_data={
              'success': True,
              'billing_key_data': {
                'billing_key': billing_key_obj.billing_key,
                'billing_type': billing_type,
                'amount': amount,
                'order_id': order_id,
                'order_name': order_name,
                'payment_key': payment_data_json.get('paymentKey'),
                'toss_response': payment_data_json
              }
            },
            billing_success_data=response.text
          )
          
          logger.info(f"빌링키 결제 성공 - user: {user_id}, billingType: {billing_type}, amount: {amount}")
          
          return JsonResponse({
            'status': 'success',
            'message': '결제가 성공적으로 완료되었습니다.',
            'data': {
              'paymentKey': payment_data_json.get('paymentKey'),
              'orderId': order_id,
              'amount': amount
            }
          })
        else:
          error_data = response.json()
          
          # 결제 실패 기록 저장
          PayHistory.objects.create(
            user=user,
            payment_data={
              'success': False,
              'error_info': {
                'billing_type': billing_type,
                'amount': amount,
                'order_id': order_id,
                'order_name': order_name,
                'error_code': error_data.get('code'),
                'error_message': error_data.get('message'),
                'toss_error_response': error_data,
                'http_status': response.status_code
              }
            }
          )
          
          logger.error(f"빌링키 결제 실패 - status: {response.status_code}, error: {error_data}")
          return JsonResponse({
            'status': 'error',
            'message': f'결제 실패: {error_data.get("message", "알 수 없는 오류")}'
          }, status=400)
        
      except TossPaymentBillingKey.DoesNotExist:
        # 빌링키 없음 오류 기록 저장
        PayHistory.objects.create(
          user=user,
          payment_data={
            'success': False,
            'error_info': {
              'billing_type': billing_type,
              'error_code': 'BILLING_KEY_NOT_FOUND',
              'error_message': '등록된 빌링키가 없습니다. 먼저 카드를 등록해주세요.',
              'error_type': 'TossPaymentBillingKey.DoesNotExist'
            }
          }
        )
        
        return JsonResponse({
          'status': 'error',
          'message': '등록된 빌링키가 없습니다. 먼저 카드를 등록해주세요.'
        }, status=404)
        
    except json.JSONDecodeError:
      return JsonResponse({
        'status': 'error',
        'message': '잘못된 JSON 형식입니다.'
      }, status=400)
    except Exception as e:
      # 일반적인 서버 오류 기록 저장
      try:
        PayHistory.objects.create(
          user=user,
          payment_data={
            'success': False,
            'error_info': {
              'billing_type': billing_type,
              'error_code': 'SERVER_ERROR',
              'error_message': f'서버 오류가 발생했습니다: {str(e)}',
              'error_type': type(e).__name__,
              'error_details': str(e)
            }
          }
        )
      except:
        pass  # PayHistory 저장 실패해도 메인 로직은 계속 진행
      
      logger.error(f"빌링키 결제 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RequestBillingAuthView(View):
  """빌링키 발급 요청 API"""
  
  def post(self, request):
    try:
      # 세션에서 사용자 정보 가져오기
      user_id = request.session.get('diary_member_id')
      if not user_id:
        return JsonResponse({
          'status': 'error',
          'message': '로그인이 필요합니다.'
        }, status=401)
      
      user = User.objects.get(id=user_id)
      
      # 요청 데이터 파싱
      data = json.loads(request.body)
      billing_type = data.get('billing_type')
      customer_key = data.get('customer_key')
      
      if not billing_type:
        return JsonResponse({
          'status': 'error',
          'message': '결제 타입이 필요합니다.'
        }, status=400)
      
      # 세션에 billing_type 저장
      request.session['pending_billing_type'] = billing_type
      
      logger.info(f"빌링키 발급 요청 - user: {user_id}, billing_type: {billing_type}, customer_key: {customer_key}")
      
      return JsonResponse({
        'status': 'success',
        'message': 'billing_type이 세션에 저장되었습니다.'
      })
      
    except User.DoesNotExist:
      return JsonResponse({
        'status': 'error',
        'message': '사용자를 찾을 수 없습니다.'
      }, status=404)
    except Exception as e:
      logger.error(f"빌링키 발급 요청 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UnlinkCardView(View):
  """카드 연동 해제 API"""
  
  def post(self, request):
    try:
      # 세션에서 사용자 정보 가져오기
      user_id = request.session.get('diary_member_id')
      if not user_id:
        return JsonResponse({
          'status': 'error',
          'message': '로그인이 필요합니다.'
        }, status=401)
      
      user = User.objects.get(id=user_id)
      
      # 사용자의 모든 빌링키 삭제
      deleted_count = TossPaymentBillingKey.objects.filter(user=user).delete()[0]
      
      logger.info(f"카드 연동 해제 완료 - user: {user_id}, deleted_count: {deleted_count}")
      
      return JsonResponse({
        'status': 'success',
        'message': '카드 연동이 성공적으로 해제되었습니다.',
        'deleted_count': deleted_count
      })
      
    except User.DoesNotExist:
      return JsonResponse({
        'status': 'error',
        'message': '사용자를 찾을 수 없습니다.'
      }, status=404)
    except Exception as e:
      logger.error(f"카드 연동 해제 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UpdateBillingTypeView(LoginRequiredMixin, View):
  """결제 주기 변경 API"""
  
  def post(self, request):
    try:
      data = json.loads(request.body)
      billing_key_id = data.get('billingKeyId')
      billing_type = data.get('billingType')  # 1: 1개월, 2: 6개월, 3: 12개월
      
      if not billing_key_id or not billing_type:
        return JsonResponse({
          'status': 'error',
          'message': '빌링키 ID와 결제 주기가 필요합니다.'
        }, status=400)
      
      if billing_type not in ['1', '2', '3']:
        return JsonResponse({
          'status': 'error',
          'message': '올바른 결제 주기를 선택해주세요.'
        }, status=400)
      
      # 빌링키 조회 및 업데이트
      try:
        billing_key = TossPaymentBillingKey.objects.get(
          id=billing_key_id,
          user=request.user
        )
        
        billing_key.billing_type = billing_type
        
        # 다음 결제일 계산
        if billing_type == '1':  # 1개월
          next_billing_date = timezone.now() + timedelta(days=30)
        elif billing_type == '2':  # 6개월
          next_billing_date = timezone.now() + timedelta(days=180)
        else:  # 12개월
          next_billing_date = timezone.now() + timedelta(days=365)
        
        billing_key.rebill_date = next_billing_date.date()
        billing_key.save()
        
        logger.info(f"결제 주기 변경 완료 - user: {request.user.id}, billingKeyId: {billing_key_id}, type: {billing_type}")
        
        return JsonResponse({
          'status': 'success',
          'message': '결제 주기가 성공적으로 변경되었습니다.',
          'data': {
            'billingType': billing_type,
            'nextBillingDate': next_billing_date.date().isoformat()
          }
        })
        
      except TossPaymentBillingKey.DoesNotExist:
        return JsonResponse({
          'status': 'error',
          'message': '해당 빌링키를 찾을 수 없습니다.'
        }, status=404)
        
    except json.JSONDecodeError:
      return JsonResponse({
        'status': 'error',
        'message': '잘못된 JSON 형식입니다.'
      }, status=400)
    except Exception as e:
      logger.error(f"결제 주기 변경 처리 중 오류: {str(e)}")
      return JsonResponse({
        'status': 'error',
        'message': '서버 오류가 발생했습니다.'
      }, status=500)

