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
import json
import logging
import base64
import requests
from config import TOSS_PAYMENTS_CLIENT_KEY, TOSS_PAYMENTS_SECRET_KEY
from .models import TossPaymentBillingKey

logger = logging.getLogger(__name__)

# 토스페이먼츠 API 설정
TOSS_API_URL = "https://api.tosspayments.com"

def get_toss_auth_header():
    """토스페이먼츠 API 인증 헤더 생성"""
    secret_key_with_colon = f"{TOSS_PAYMENTS_SECRET_KEY}:"
    encoded_key = base64.b64encode(secret_key_with_colon.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded_key}"

def issue_billing_key(auth_key, customer_key):
    """빌링키 발급 API 호출"""
    try:
        url = f"{TOSS_API_URL}/v1/billing/authorizations/issue"
        headers = {
            'Authorization': get_toss_auth_header(),
            'Content-Type': 'application/json'
        }
        payload = {
            "authKey": auth_key,
            "customerKey": customer_key
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
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

class TossPaymentsView(View):
  def get(self, request):
    return render(request, 'toss_payments/toss_payments.html')

class TossPaymentsSuccessView(View):
  def get(self, request):
    # 성공 시 쿼리 파라미터 추출
    customer_key = request.GET.get('customerKey')
    auth_key = request.GET.get('authKey')
    
    # 로깅
    logger.info(f"결제 인증 성공 - customerKey: {customer_key}, authKey: {auth_key}")
    
    # 컨텍스트에 데이터 전달
    context = {
      'customer_key': customer_key,
      'auth_key': auth_key,
    }
    
    return render(request, 'toss_payments/success.html', context)

class TossPaymentsFailView(View):
  def get(self, request):
    # 실패 시 쿼리 파라미터 추출
    error_code = request.GET.get('code')
    error_message = request.GET.get('message')
    
    # 로깅
    logger.error(f"결제 인증 실패 - code: {error_code}, message: {error_message}")
    
    # 컨텍스트에 데이터 전달
    context = {
      'error_code': error_code,
      'error_message': error_message,
    }
    
    return render(request, 'toss_payments/fail.html', context)

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
class IssueBillingKeyView(View):
  """빌링키 발급 API"""
  
  def post(self, request):
    try:
      data = json.loads(request.body)
      customer_key = data.get('customerKey')
      auth_key = data.get('authKey')
      
      if not customer_key or not auth_key:
        return JsonResponse({
          'status': 'error',
          'message': 'customerKey와 authKey가 필요합니다.'
        }, status=400)
      
      # 토스페이먼츠 API로 빌링키 발급 요청
      result = issue_billing_key(auth_key, customer_key)
      
      if result['success']:
        billing_data = result['data']
        
        # 데이터베이스에 빌링키 저장
        try:
          # 기존 빌링키가 있는지 확인
          existing_billing = TossPaymentBillingKey.objects.filter(
            user=request.user,
            billing_key=billing_data.get('billingKey')
          ).first()
          
          if not existing_billing:
            # 새로운 빌링키 저장
            TossPaymentBillingKey.objects.create(
              user=request.user,
              billing_key=billing_data.get('billingKey'),
              billing_data=billing_data,
              billing_type="1",  # 기본값: 1개월
              billing_status="0",  # 아직 결제 안됨
              billing_activate=True
            )
            logger.info(f"새로운 빌링키 저장 완료 - user: {request.user.id}, billingKey: {billing_data.get('billingKey')}")
          else:
            logger.info(f"이미 존재하는 빌링키 - user: {request.user.id}, billingKey: {billing_data.get('billingKey')}")
            
        except Exception as e:
          logger.error(f"빌링키 저장 중 오류: {str(e)}")
          # 저장 실패해도 API 응답은 성공으로 처리
        
        return JsonResponse({
          'status': 'success',
          'message': '빌링키가 성공적으로 발급되었습니다.',
          'data': {
            'customerKey': billing_data.get('customerKey'),
            'billingKey': billing_data.get('billingKey'),
            'cardCompany': billing_data.get('cardCompany'),
            'cardNumber': billing_data.get('cardNumber'),
            'authenticatedAt': billing_data.get('authenticatedAt')
          }
        })
      else:
        return JsonResponse({
          'status': 'error',
          'message': '빌링키 발급에 실패했습니다.',
          'error': result['error']
        }, status=400)
        
    except json.JSONDecodeError:
      return JsonResponse({
        'status': 'error',
        'message': '잘못된 JSON 형식입니다.'
      }, status=400)
    except Exception as e:
      logger.error(f"빌링키 발급 처리 중 오류: {str(e)}")
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
      
      # TODO: 데이터베이스에 에러 로그 저장하는 로직 추가
      # 예: PaymentError.objects.create(
      #     error_code=error_code,
      #     error_message=error_message,
      #     status='fail'
      # )
      
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
class CancelSubscriptionView(LoginRequiredMixin, View):
  """구독 취소 API"""
  
  def post(self, request):
    try:
      data = json.loads(request.body)
      billing_key_id = data.get('billingKeyId')
      
      if not billing_key_id:
        return JsonResponse({
          'status': 'error',
          'message': '빌링키 ID가 필요합니다.'
        }, status=400)
      
      # 빌링키 조회 및 비활성화
      try:
        billing_key = TossPaymentBillingKey.objects.get(
          id=billing_key_id,
          user=request.user
        )
        billing_key.billing_activate = False
        billing_key.save()
        
        logger.info(f"구독 취소 완료 - user: {request.user.id}, billingKeyId: {billing_key_id}")
        
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

