from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import AIClassTextElement, ClassFormTextElement
from .admin_decorators import admin_required, admin_required_json

@admin_required
def ai_class_text_management(request):
    print("=== ai_class_text_management 뷰 함수 호출됨 ===")
    print(f"요청 URL: {request.path}")
    print(f"사용자: {getattr(request, 'user_obj', 'None')}")
    """AI 클래스 텍스트 관리 페이지"""
    # 모든 텍스트 요소 가져오기
    text_elements = AIClassTextElement.objects.all().order_by('key')
    
    # 섹션별로 그룹화
    sections = {
        'hero': [],
        'stats': [],
        'barriers': [],
        'benefits': [],
        'ai_tools': [],
        'instructor': [],
        'class_info': [],
        'cta': [],
        'other': []
    }
    
    for element in text_elements:
        key = element.key
        if key.startswith(('badge_text', 'money_highlight', 'main_title', 'sub_headline', 'ai_name', 'ai_desc')):
            sections['hero'].append(element)
        elif key.startswith(('stats_title', 'current_income', 'target_income', 'comparison')):
            sections['stats'].append(element)
        elif key.startswith(('barriers', 'barrier_', 'experience_')):
            sections['barriers'].append(element)
        elif key.startswith(('benefits', 'benefit_')):
            sections['benefits'].append(element)
        elif key.startswith(('ai_tools', 'instructor_')):
            sections['ai_tools'].append(element)
        elif key.startswith(('class_info', 'class_schedule', 'class_method', 'class_capacity', 'class_benefit')):
            sections['class_info'].append(element)
        elif key.startswith(('cta_', 'urgency_')):
            sections['cta'].append(element)
        else:
            sections['other'].append(element)
    
    context = {
        'sections': sections,
        'total_elements': text_elements.count()
    }
    
    return render(request, 'ai_class/admin_text_management.html', context)

@admin_required_json
@csrf_exempt
@require_http_methods(["POST"])
def update_text_element(request):
    """텍스트 요소 업데이트 API"""
    try:
        data = json.loads(request.body)
        key = data.get('key')
        text = data.get('text')
        description = data.get('description', '')
        
        if not key or text is None:
            return JsonResponse({'error': '키와 텍스트는 필수입니다.'}, status=400)
        
        # 텍스트 요소 찾기 또는 생성
        element, created = AIClassTextElement.objects.get_or_create(
            key=key,
            defaults={'text': text, 'description': description}
        )
        
        if not created:
            element.text = text
            element.description = description
            element.save()
        
        return JsonResponse({
            'success': True,
            'message': '텍스트가 성공적으로 업데이트되었습니다.',
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'업데이트 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
@csrf_exempt
@require_http_methods(["POST"])
def create_text_element(request):
    """새 텍스트 요소 생성 API"""
    try:
        data = json.loads(request.body)
        key = data.get('key')
        text = data.get('text')
        description = data.get('description', '')
        
        if not key or not text:
            return JsonResponse({'error': '키와 텍스트는 필수입니다.'}, status=400)
        
        # 키 중복 확인
        if AIClassTextElement.objects.filter(key=key).exists():
            return JsonResponse({'error': '이미 존재하는 키입니다.'}, status=400)
        
        # 새 요소 생성
        element = AIClassTextElement.objects.create(
            key=key,
            text=text,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'message': '텍스트 요소가 성공적으로 생성되었습니다.',
            'element': {
                'id': element.id,
                'key': element.key,
                'text': element.text,
                'description': element.description
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'생성 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_text_element(request, element_id):
    """텍스트 요소 삭제 API"""
    try:
        element = AIClassTextElement.objects.get(id=element_id)
        element.delete()
        
        return JsonResponse({
            'success': True,
            'message': '텍스트 요소가 성공적으로 삭제되었습니다.'
        })
        
    except AIClassTextElement.DoesNotExist:
        return JsonResponse({'error': '텍스트 요소를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
def get_text_element(request, element_id):
    """특정 텍스트 요소 조회 API"""
    try:
        element = AIClassTextElement.objects.get(id=element_id)
        
        return JsonResponse({
            'success': True,
            'element': {
                'id': element.id,
                'key': element.key,
                'text': element.text,
                'description': element.description,
                'created_at': element.created_at.isoformat(),
                'updated_at': element.updated_at.isoformat()
            }
        })
        
    except AIClassTextElement.DoesNotExist:
        return JsonResponse({'error': '텍스트 요소를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
def get_all_text_elements(request):
    """모든 텍스트 요소 조회 API"""
    try:
        elements = AIClassTextElement.objects.all().order_by('key')
        
        elements_data = []
        for element in elements:
            elements_data.append({
                'id': element.id,
                'key': element.key,
                'text': element.text,
                'description': element.description,
                'created_at': element.created_at.isoformat(),
                'updated_at': element.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'elements': elements_data,
            'total': len(elements_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}, status=500)


# ==================== ClassForm 텍스트 관리 ====================

@admin_required
def class_form_text_management(request):
    """AI 클래스 폼 텍스트 관리 페이지"""
    # 모든 텍스트 요소 가져오기
    text_elements = ClassFormTextElement.objects.all().order_by('key')
    
    # 섹션별로 그룹화
    sections = {
        'basic_info': [],
        'class_details': [],
        'payment_info': [],
        'form_labels': [],
        'other': []
    }
    
    for element in text_elements:
        key = element.key
        if key.startswith(('form.title', 'form.subtitle')):
            sections['basic_info'].append(element)
        elif key.startswith(('form.date', 'form.location', 'form.capacity')):
            sections['class_details'].append(element)
        elif key.startswith(('form.bank', 'form.account', 'form.fee', 'form.notice')):
            sections['payment_info'].append(element)
        elif key.startswith(('form.label_', 'form.placeholder_', 'form.button')):
            sections['form_labels'].append(element)
        else:
            sections['other'].append(element)
    
    context = {
        'sections': sections,
        'total_elements': text_elements.count()
    }
    
    return render(request, 'ai_class/admin_form_text_management.html', context)

@admin_required_json
@csrf_exempt
@require_http_methods(["POST"])
def update_form_text_element(request):
    """폼 텍스트 요소 업데이트 API"""
    try:
        data = json.loads(request.body)
        key = data.get('key')
        text = data.get('text')
        description = data.get('description', '')
        
        if not key or text is None:
            return JsonResponse({'error': '키와 텍스트는 필수입니다.'}, status=400)
        
        # 텍스트 요소 찾기 또는 생성
        element, created = ClassFormTextElement.objects.get_or_create(
            key=key,
            defaults={'text': text, 'description': description}
        )
        
        if not created:
            element.text = text
            element.description = description
            element.save()
        
        return JsonResponse({
            'success': True,
            'message': '텍스트가 성공적으로 업데이트되었습니다.',
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'업데이트 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
@csrf_exempt
@require_http_methods(["POST"])
def create_form_text_element(request):
    """새 폼 텍스트 요소 생성 API"""
    try:
        data = json.loads(request.body)
        key = data.get('key')
        text = data.get('text')
        description = data.get('description', '')
        
        if not key or not text:
            return JsonResponse({'error': '키와 텍스트는 필수입니다.'}, status=400)
        
        # 키 중복 확인
        if ClassFormTextElement.objects.filter(key=key).exists():
            return JsonResponse({'error': '이미 존재하는 키입니다.'}, status=400)
        
        # 새 요소 생성
        element = ClassFormTextElement.objects.create(
            key=key,
            text=text,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'message': '텍스트 요소가 성공적으로 생성되었습니다.',
            'element': {
                'id': element.id,
                'key': element.key,
                'text': element.text,
                'description': element.description
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'생성 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_form_text_element(request, element_id):
    """폼 텍스트 요소 삭제 API"""
    try:
        element = ClassFormTextElement.objects.get(id=element_id)
        element.delete()
        
        return JsonResponse({
            'success': True,
            'message': '텍스트 요소가 성공적으로 삭제되었습니다.'
        })
        
    except ClassFormTextElement.DoesNotExist:
        return JsonResponse({'error': '텍스트 요소를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'삭제 중 오류가 발생했습니다: {str(e)}'}, status=500)

@admin_required_json
def get_form_text_element(request, element_id):
    """특정 폼 텍스트 요소 조회 API"""
    try:
        element = ClassFormTextElement.objects.get(id=element_id)
        
        return JsonResponse({
            'success': True,
            'element': {
                'id': element.id,
                'key': element.key,
                'text': element.text,
                'description': element.description,
                'created_at': element.created_at.isoformat(),
                'updated_at': element.updated_at.isoformat()
            }
        })
        
    except ClassFormTextElement.DoesNotExist:
        return JsonResponse({'error': '텍스트 요소를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}, status=500)
