import redis
import json
import hashlib
import time
import logging
from typing import Any, Optional, Dict, List
from django.conf import settings
from django.core.cache import cache
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Redis를 사용한 고급 캐시 관리자 - 로컬 환경 fallback 지원"""
    
    def __init__(self):
        self.redis_client = None
        self.redis_available = False
        
        try:
            # Django Redis 연결 시도
            self.redis_client = get_redis_connection("default")
            # 연결 테스트
            self.redis_client.ping()
            self.redis_available = True
            # 이모지 제거하고 텍스트로 변경
            logger.info("Redis 캐시 관리자 초기화 완료")
        except Exception as e:
            logger.warning(f"Redis 연결 실패, Django 캐시로 fallback: {e}")
            self.redis_available = False
    
    def _generate_cache_key(self, prefix: str, user_id: int, *args) -> str:
        """안전한 캐시 키 생성 (사용자별 격리)"""
        # 사용자 ID를 포함하여 키 격리
        key_parts = [prefix, str(user_id)]
        key_parts.extend([str(arg) for arg in args])
        
        # 키 길이 제한 및 특수문자 처리
        cache_key = ":".join(key_parts)
        if len(cache_key) > 250:  # Redis 키 길이 제한
            # 해시를 사용하여 키 길이 단축
            hash_obj = hashlib.md5(cache_key.encode())
            cache_key = f"{prefix}:{user_id}:{hash_obj.hexdigest()}"
        
        return cache_key
    
    def _generate_session_key(self, user_id: int, session_id: str, key_name: str) -> str:
        """세션별 고유 캐시 키 생성"""
        return f"entry_table_{user_id}_{session_id}_{key_name}"
    
    def set_cache(self, key: str, value: Any, timeout: int = 300) -> bool:
        """캐시 설정 - Redis 실패 시 Django 캐시로 fallback"""
        try:
            if self.redis_available and self.redis_client:
                # Redis 사용
                self.redis_client.setex(key, timeout, json.dumps(value, ensure_ascii=False))
                logger.debug(f"Redis 캐시 설정: {key}")
                return True
            else:
                # Django 기본 캐시 사용
                cache.set(key, value, timeout)
                logger.debug(f"Django 캐시 설정: {key}")
                return True
        except Exception as e:
            logger.warning(f"Redis 캐시 설정 실패 [{key}]: {e}")
            # Django 기본 캐시로 fallback
            try:
                cache.set(key, value, timeout)
                logger.debug(f"Django 캐시 fallback 성공: {key}")
                return True
            except Exception as fallback_e:
                logger.error(f"Django 캐시 fallback도 실패: {fallback_e}")
                return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """캐시 조회 - Redis 실패 시 Django 캐시로 fallback"""
        try:
            if self.redis_available and self.redis_client:
                # Redis 사용
                value = self.redis_client.get(key)
                if value:
                    result = json.loads(value)
                    logger.debug(f"Redis 캐시 조회: {key}")
                    return result
                return None
            else:
                # Django 기본 캐시 사용
                result = cache.get(key)
                logger.debug(f"Django 캐시 조회: {key}")
                return result
        except Exception as e:
            logger.warning(f"Redis 캐시 조회 실패 [{key}]: {e}")
            # Django 기본 캐시로 fallback
            try:
                result = cache.get(key)
                logger.debug(f"Django 캐시 fallback 성공: {key}")
                return result
            except Exception as fallback_e:
                logger.error(f"Django 캐시 fallback도 실패: {fallback_e}")
                return None
    
    def delete_cache(self, key: str) -> bool:
        """캐시 삭제 - Redis 실패 시 Django 캐시로 fallback"""
        try:
            if self.redis_available and self.redis_client:
                # Redis 사용
                result = bool(self.redis_client.delete(key))
                logger.debug(f"Redis 캐시 삭제: {key}")
                return result
            else:
                # Django 기본 캐시 사용
                cache.delete(key)
                logger.debug(f"Django 캐시 삭제: {key}")
                return True
        except Exception as e:
            logger.warning(f"Redis 캐시 삭제 실패 [{key}]: {e}")
            # Django 기본 캐시로 fallback
            try:
                cache.delete(key)
                logger.debug(f"Django 캐시 fallback 성공: {key}")
                return True
            except Exception as fallback_e:
                logger.error(f"Django 캐시 fallback도 실패: {fallback_e}")
                return False
    
    def clear_user_cache(self, user_id: int) -> bool:
        """사용자별 모든 캐시 삭제"""
        try:
            if self.redis_available and self.redis_client:
                # Redis 사용
                pattern = f"*:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    result = bool(self.redis_client.delete(*keys))
                    logger.info(f"Redis 사용자 캐시 삭제: {user_id} ({len(keys)}개 키)")
                    return result
                return True
            else:
                # Django 기본 캐시 사용 (전체 캐시 삭제)
                cache.clear()
                logger.info(f"Django 캐시 전체 삭제 (사용자 {user_id})")
                return True
        except Exception as e:
            logger.error(f"사용자 캐시 삭제 실패 [{user_id}]: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        try:
            if self.redis_available and self.redis_client:
                # Redis 통계
                info = self.redis_client.info()
                return {
                    'cache_type': 'Redis',
                    'redis_version': info.get('redis_version'),
                    'connected_clients': info.get('connected_clients'),
                    'used_memory_human': info.get('used_memory_human'),
                    'keyspace_hits': info.get('keyspace_hits'),
                    'keyspace_misses': info.get('keyspace_misses'),
                    'total_keys': len(self.redis_client.keys('*')),
                }
            else:
                # Django 캐시 통계
                return {
                    'cache_type': 'Django Default Cache',
                    'status': 'Redis 연결 없음 - Django 캐시 사용 중',
                    'fallback': True
                }
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {'status': '오류', 'error': str(e)}
    
    def is_redis_available(self) -> bool:
        """Redis 사용 가능 여부 확인"""
        return self.redis_available
    
    def get_all_keys(self, pattern: str = "*") -> List[str]:
        """패턴에 맞는 모든 키 조회"""
        try:
            if self.redis_available and self.redis_client:
                keys = self.redis_client.keys(pattern)
                return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
            else:
                return []
        except Exception as e:
            logger.error(f"키 조회 실패: {e}")
            return []

# Lazy loading을 위한 전역 변수
_cache_manager_instance = None

def get_cache_manager():
    """캐시 관리자 인스턴스를 lazy loading으로 반환"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        try:
            _cache_manager_instance = RedisCacheManager()
            logger.info("Redis 캐시 관리자 초기화 완료")
        except Exception as e:
            logger.error(f"Redis 캐시 관리자 초기화 실패: {e}")
            # Django 기본 캐시만 사용하는 간단한 fallback 클래스
            class FallbackCacheManager:
                def __init__(self):
                    self.redis_available = False
                
                def _generate_session_key(self, user_id, session_id, key_name):
                    return f"entry_table_{user_id}_{session_id}_{key_name}"
                
                def set_cache(self, key, value, timeout=300):
                    try:
                        cache.set(key, value, timeout)
                        return True
                    except:
                        return False
                
                def get_cache(self, key):
                    try:
                        return cache.get(key)
                    except:
                        return None
                
                def delete_cache(self, key):
                    try:
                        cache.delete(key)
                        return True
                    except:
                        return False
                
                def clear_user_cache(self, user_id):
                    try:
                        cache.clear()
                        return True
                    except:
                        return False
                
                def get_cache_stats(self):
                    return {'cache_type': 'Django Fallback Cache', 'status': 'Redis 연결 실패'}
                
                def is_redis_available(self):
                    return False
                
                def get_all_keys(self, pattern="*"):
                    return []
            
            _cache_manager_instance = FallbackCacheManager()
            logger.warning("Fallback 캐시 관리자로 동작합니다.")
    
    return _cache_manager_instance