"""
Redis Cache Manager for VNC Desktop
مدير التخزين المؤقت Redis لسطح مكتب VNC
"""
import redis
import json
import pickle
import logging
from datetime import timedelta
from typing import Any, Optional
from flask import current_app
import os

class RedisManager:
    """مدير Redis للتخزين المؤقت والطوابير"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        """تهيئة اتصال Redis"""
        self.redis_url = os.getenv('REDIS_URL', f'redis://{host}:{port}/{db}')
        self.client = None
        self.connected = False
        
    def connect(self):
        """الاتصال بـ Redis"""
        try:
            if os.getenv('REDIS_URL'):
                self.client = redis.from_url(self.redis_url, decode_responses=False)
            else:
                # للتطوير المحلي - استخدام Redis محلي
                self.client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=0,
                    decode_responses=False,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
            
            # فحص الاتصال
            self.client.ping()
            self.connected = True
            logging.info("Redis connected successfully")
            return True
            
        except Exception as e:
            logging.warning(f"Redis connection failed: {e}")
            self.connected = False
            return False
    
    def is_connected(self) -> bool:
        """فحص حالة الاتصال"""
        if not self.client:
            return False
            
        try:
            self.client.ping()
            return True
        except:
            self.connected = False
            return False
    
    def set_cache(self, key: str, value: Any, ttl: int = 300) -> bool:
        """حفظ في التخزين المؤقت مع انتهاء صلاحية"""
        if not self.is_connected():
            return False
            
        try:
            # تسلسل القيمة
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = str(value)
            else:
                serialized_value = pickle.dumps(value)
            
            # حفظ مع انتهاء الصلاحية
            result = self.client.setex(key, ttl, serialized_value)
            return result
            
        except Exception as e:
            logging.error(f"Redis set error for key {key}: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """استرجاع من التخزين المؤقت"""
        if not self.is_connected():
            return None
            
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # محاولة إلغاء التسلسل
            try:
                # محاولة JSON أولاً
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    # محاولة pickle
                    return pickle.loads(value)
                except:
                    # إرجاع كنص
                    return value.decode('utf-8', errors='ignore')
                    
        except Exception as e:
            logging.error(f"Redis get error for key {key}: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """حذف من التخزين المؤقت"""
        if not self.is_connected():
            return False
            
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logging.error(f"Redis delete error for key {key}: {e}")
            return False
    
    def clear_cache(self, pattern: str = "*") -> int:
        """مسح التخزين المؤقت بنمط معين"""
        if not self.is_connected():
            return 0
            
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logging.error(f"Redis clear error for pattern {pattern}: {e}")
            return 0
    
    def increment_counter(self, key: str, ttl: int = 3600) -> int:
        """زيادة عداد مع انتهاء صلاحية"""
        if not self.is_connected():
            return 0
            
        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0]
        except Exception as e:
            logging.error(f"Redis increment error for key {key}: {e}")
            return 0
    
    def get_counter(self, key: str) -> int:
        """الحصول على قيمة العداد"""
        value = self.get_cache(key)
        try:
            return int(value) if value else 0
        except:
            return 0
    
    def add_to_list(self, key: str, value: Any, max_length: int = 100) -> bool:
        """إضافة إلى قائمة مع حد أقصى للطول"""
        if not self.is_connected():
            return False
            
        try:
            # تسلسل القيمة
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            pipe = self.client.pipeline()
            pipe.lpush(key, serialized_value)
            pipe.ltrim(key, 0, max_length - 1)
            pipe.execute()
            return True
            
        except Exception as e:
            logging.error(f"Redis list add error for key {key}: {e}")
            return False
    
    def get_list(self, key: str, start: int = 0, end: int = -1) -> list:
        """الحصول على قائمة"""
        if not self.is_connected():
            return []
            
        try:
            values = self.client.lrange(key, start, end)
            result = []
            
            for value in values:
                try:
                    # محاولة JSON
                    result.append(json.loads(value.decode('utf-8')))
                except:
                    # كنص عادي
                    result.append(value.decode('utf-8', errors='ignore'))
            
            return result
            
        except Exception as e:
            logging.error(f"Redis list get error for key {key}: {e}")
            return []
    
    def publish_message(self, channel: str, message: Any) -> bool:
        """نشر رسالة على قناة"""
        if not self.is_connected():
            return False
            
        try:
            if isinstance(message, (dict, list, tuple)):
                message = json.dumps(message, ensure_ascii=False)
            elif not isinstance(message, str):
                message = str(message)
            
            result = self.client.publish(channel, message)
            return result > 0
            
        except Exception as e:
            logging.error(f"Redis publish error for channel {channel}: {e}")
            return False
    
    def get_stats(self) -> dict:
        """إحصائيات Redis"""
        if not self.is_connected():
            return {}
            
        try:
            info = self.client.info()
            return {
                'connected': True,
                'uptime_seconds': info.get('uptime_in_seconds', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'connected_clients': info.get('connected_clients', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keys_count': len(self.client.keys('*'))
            }
        except Exception as e:
            logging.error(f"Redis stats error: {e}")
            return {'connected': False, 'error': str(e)}

# مثيل عام لـ Redis
redis_manager = RedisManager()

def cached_with_redis(ttl: int = 300, key_prefix: str = "vnc"):
    """Decorator للتخزين المؤقت باستخدام Redis"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # إنشاء مفتاح فريد
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(key_parts)
            
            # محاولة الحصول من التخزين المؤقت
            cached_result = redis_manager.get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # تنفيذ الدالة وحفظ النتيجة
            result = func(*args, **kwargs)
            redis_manager.set_cache(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def init_redis(app=None):
    """تهيئة Redis مع Flask"""
    if app:
        app.redis = redis_manager
    
    # محاولة الاتصال
    if not redis_manager.connect():
        logging.warning("Redis not available, falling back to local cache")
        return False
    
    logging.info("Redis initialized successfully")
    return True