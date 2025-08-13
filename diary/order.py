import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Attribute, User, Row

@csrf_exempt
def update_detail_sort_order(request):
    """상세보기 모달에서 속성 순서를 업데이트하는 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        user_id = request.session.get('diary_member_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'})

        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        attribute_orders = data.get('attribute_orders', [])
        
        # 트랜잭션으로 순서 업데이트
        with transaction.atomic():
            for order_data in attribute_orders:
                attribute_id = order_data.get('id')
                new_order = order_data.get('detail_sort_order')
                
                if attribute_id and new_order is not None:
                    Attribute.objects.filter(id=attribute_id, user=user).update(
                        detail_sort_order=new_order
                    )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@csrf_exempt
def save_column_order(request):
    """컬럼 순서 저장"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    try:
        data = json.loads(request.body)
        column_order = data.get('column_order', [])
        if not column_order:
            return JsonResponse({'success': False, 'error': 'column_order is required'})
         
        user_id = request.session.get('diary_member_id')

        user = User.objects.get(id=user_id)
        with transaction.atomic():
            for index, column_name in enumerate(column_order):
                try:
                    attribute = Attribute.objects.get(name=column_name, user=user)
                    attribute.sort_order = index
                    attribute.save()
                except Attribute.DoesNotExist:
                    continue
        return JsonResponse({'success': True, 'message': '컬럼 순서가 저장되었습니다.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@csrf_exempt
def reorder_entries(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('order', [])
            for idx, row_id in enumerate(ids):
                Row.objects.filter(id=row_id).update(order=idx)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})