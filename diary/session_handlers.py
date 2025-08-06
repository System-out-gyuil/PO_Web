from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
import json

def cleanup_session_cache(session_id):
    """세션별 캐시 정리"""
    try:
        cache_key = f"blog_status_{session_id}_blog_status"
        cache.delete(cache_key)
        print(f"🧹 세션 {session_id} 캐시 정리 완료")
        return True
    except Exception as e:
        print(f"⚠️ 세션 {session_id} 캐시 정리 실패: {str(e)}")
        return False

def get_active_sessions():
    """활성 세션 목록 조회"""
    try:
        # Redis에서 blog_status로 시작하는 모든 키 조회
        from django_redis import get_redis_connection
        redis_client = get_redis_connection("default")
        
        # 패턴 매칭으로 세션 키 찾기
        pattern = "blog_status_*"
        keys = redis_client.keys(pattern)
        
        active_sessions = []
        for key in keys:
            # 키에서 세션 ID 추출
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if '_blog_status_' in key_str:
                session_id = key_str.split('_blog_status_')[1]
                # 세션 데이터 조회
                session_data = cache.get(key_str)
                if session_data:
                    active_sessions.append({
                        'session_id': session_id,
                        'step': session_data.get('step', 'unknown'),
                        'timestamp': session_data.get('timestamp', ''),
                        'progress': session_data.get('progress', 0)
                    })
        
        return active_sessions
    except Exception as e:
        print(f"⚠️ 활성 세션 조회 실패: {str(e)}")
        return []

@csrf_exempt
@require_http_methods(["POST"])
def cleanup_session_cache_api(request):
    """세션 캐시 정리 API"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': '세션 ID가 필요합니다.'
            })
        
        success = cleanup_session_cache(session_id)
        
        return JsonResponse({
            'success': success,
            'message': '세션 캐시가 정리되었습니다.' if success else '세션 캐시 정리 중 오류가 발생했습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def get_active_sessions_api(request):
    """활성 세션 목록 조회 API"""
    try:
        active_sessions = get_active_sessions()
        
        return JsonResponse({
            'success': True,
            'sessions': active_sessions,
            'count': len(active_sessions)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 