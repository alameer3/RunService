"""
Performance monitoring and optimization utilities
أدوات مراقبة وتحسين الأداء
"""
import psutil
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
import logging
from app import db
from models import ConnectionLog

class PerformanceMonitor:
    """مراقب الأداء للنظام"""
    
    def __init__(self, history_size=100):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.response_times = deque(maxlen=history_size)
        self.request_counts = defaultdict(int)
        self.start_time = datetime.now()
        self.lock = Lock()
        
        # عدادات الأداء
        self.total_requests = 0
        self.total_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
    def record_system_metrics(self):
        """تسجيل مقاييس النظام"""
        with self.lock:
            try:
                # معلومات المعالج
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_history.append({
                    'timestamp': datetime.now(),
                    'value': cpu_percent
                })
                
                # معلومات الذاكرة
                memory = psutil.virtual_memory()
                self.memory_history.append({
                    'timestamp': datetime.now(),
                    'used': memory.percent,
                    'available': memory.available,
                    'total': memory.total
                })
                
                # معلومات القرص
                disk = psutil.disk_usage('/')
                self.disk_history.append({
                    'timestamp': datetime.now(),
                    'used': disk.used,
                    'free': disk.free,
                    'total': disk.total,
                    'percent': (disk.used / disk.total) * 100
                })
                
            except Exception as e:
                logging.error(f"Error recording system metrics: {e}")
    
    def record_request(self, endpoint, response_time, status_code):
        """تسجيل طلب جديد"""
        with self.lock:
            self.total_requests += 1
            self.request_counts[endpoint] += 1
            
            if response_time:
                self.response_times.append({
                    'timestamp': datetime.now(),
                    'endpoint': endpoint,
                    'response_time': response_time,
                    'status_code': status_code
                })
            
            if status_code >= 400:
                self.total_errors += 1
    
    def record_cache_event(self, hit=True):
        """تسجيل أحداث التخزين المؤقت"""
        with self.lock:
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
    
    def get_current_metrics(self):
        """الحصول على المقاييس الحالية"""
        with self.lock:
            try:
                # مقاييس النظام الحالية
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # مقاييس الشبكة
                network = psutil.net_io_counters()
                
                # وقت التشغيل
                uptime = datetime.now() - self.start_time
                
                return {
                    'cpu': {
                        'current': cpu_percent,
                        'average': self._calculate_average([m['value'] for m in self.cpu_history]),
                        'history': list(self.cpu_history)
                    },
                    'memory': {
                        'percent': memory.percent,
                        'used': memory.used,
                        'available': memory.available,
                        'total': memory.total,
                        'history': list(self.memory_history)
                    },
                    'disk': {
                        'percent': (disk.used / disk.total) * 100,
                        'used': disk.used,
                        'free': disk.free,
                        'total': disk.total,
                        'history': list(self.disk_history)
                    },
                    'network': {
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv,
                        'packets_sent': network.packets_sent,
                        'packets_recv': network.packets_recv
                    },
                    'application': {
                        'uptime_seconds': uptime.total_seconds(),
                        'total_requests': self.total_requests,
                        'total_errors': self.total_errors,
                        'error_rate': (self.total_errors / max(self.total_requests, 1)) * 100,
                        'avg_response_time': self._calculate_average([r['response_time'] for r in self.response_times]),
                        'cache_hit_rate': (self.cache_hits / max(self.cache_hits + self.cache_misses, 1)) * 100
                    },
                    'endpoints': dict(self.request_counts)
                }
                
            except Exception as e:
                logging.error(f"Error getting current metrics: {e}")
                return {}
    
    def _calculate_average(self, values):
        """حساب المتوسط"""
        if not values:
            return 0
        return sum(values) / len(values)
    
    def get_performance_alerts(self):
        """الحصول على تنبيهات الأداء"""
        alerts = []
        
        try:
            cpu_avg = self._calculate_average([m['value'] for m in self.cpu_history])
            if cpu_avg > 80:
                alerts.append({
                    'type': 'warning',
                    'message': f'استخدام المعالج مرتفع: {cpu_avg:.1f}%',
                    'severity': 'high' if cpu_avg > 90 else 'medium'
                })
            
            if self.memory_history:
                memory_avg = self._calculate_average([m['used'] for m in self.memory_history])
                if memory_avg > 85:
                    alerts.append({
                        'type': 'warning',
                        'message': f'استخدام الذاكرة مرتفع: {memory_avg:.1f}%',
                        'severity': 'high' if memory_avg > 95 else 'medium'
                    })
            
            if self.disk_history:
                disk_avg = self._calculate_average([m['percent'] for m in self.disk_history])
                if disk_avg > 90:
                    alerts.append({
                        'type': 'error',
                        'message': f'مساحة القرص منخفضة: {disk_avg:.1f}% مستخدمة',
                        'severity': 'critical'
                    })
            
            error_rate = (self.total_errors / max(self.total_requests, 1)) * 100
            if error_rate > 10:
                alerts.append({
                    'type': 'error',
                    'message': f'معدل الأخطاء مرتفع: {error_rate:.1f}%',
                    'severity': 'high'
                })
        
        except Exception as e:
            logging.error(f"Error generating performance alerts: {e}")
        
        return alerts
    
    def cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # تنظيف السجلات القديمة من قاعدة البيانات
            try:
                old_logs = ConnectionLog.query.filter(
                    ConnectionLog.timestamp < cutoff_time
                ).all()
                
                for log in old_logs:
                    db.session.delete(log)
                
                db.session.commit()
                logging.info(f"Cleaned up {len(old_logs)} old log entries")
                
            except Exception as e:
                logging.error(f"Error cleaning up old data: {e}")
                try:
                    db.session.rollback()
                except:
                    pass

class CacheManager:
    """مدير التخزين المؤقت"""
    
    def __init__(self, default_ttl=300):  # 5 دقائق افتراضي
        self.cache = {}
        self.ttl = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
        
    def get(self, key):
        """الحصول على قيمة من التخزين المؤقت"""
        with self.lock:
            if key in self.cache:
                if self._is_expired(key):
                    self._remove(key)
                    return None
                return self.cache[key]
            return None
    
    def set(self, key, value, ttl=None):
        """حفظ قيمة في التخزين المؤقت"""
        with self.lock:
            self.cache[key] = value
            self.ttl[key] = time.time() + (ttl or self.default_ttl)
    
    def delete(self, key):
        """حذف قيمة من التخزين المؤقت"""
        with self.lock:
            self._remove(key)
    
    def clear(self):
        """مسح جميع البيانات المؤقتة"""
        with self.lock:
            self.cache.clear()
            self.ttl.clear()
    
    def _is_expired(self, key):
        """فحص انتهاء صلاحية المفتاح"""
        return time.time() > self.ttl.get(key, 0)
    
    def _remove(self, key):
        """إزالة مفتاح من التخزين المؤقت"""
        self.cache.pop(key, None)
        self.ttl.pop(key, None)
    
    def cleanup_expired(self):
        """تنظيف البيانات منتهية الصلاحية"""
        with self.lock:
            expired_keys = [key for key in self.cache.keys() if self._is_expired(key)]
            for key in expired_keys:
                self._remove(key)
            return len(expired_keys)
    
    def get_stats(self):
        """إحصائيات التخزين المؤقت"""
        with self.lock:
            total_items = len(self.cache)
            expired_items = len([key for key in self.cache.keys() if self._is_expired(key)])
            
            return {
                'total_items': total_items,
                'active_items': total_items - expired_items,
                'expired_items': expired_items,
                'memory_usage': sum(len(str(k)) + len(str(v)) for k, v in self.cache.items())
            }

# إنشاء مثيلات عامة
performance_monitor = PerformanceMonitor()
cache_manager = CacheManager()

def cached(ttl=300):
    """decorator للتخزين المؤقت للدوال"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # إنشاء مفتاح للتخزين المؤقت
            cache_key = f"{func.__name__}:{hash((args, tuple(kwargs.items())))}"
            
            # محاولة الحصول من التخزين المؤقت
            result = cache_manager.get(cache_key)
            if result is not None:
                performance_monitor.record_cache_event(hit=True)
                return result
            
            # تنفيذ الدالة وحفظ النتيجة
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            performance_monitor.record_cache_event(hit=False)
            
            return result
        return wrapper
    return decorator

def monitor_request_performance(func):
    """decorator لمراقبة أداء الطلبات"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            # تسجيل الطلب الناجح
            endpoint = func.__name__
            performance_monitor.record_request(endpoint, response_time, 200)
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            performance_monitor.record_request(func.__name__, response_time, 500)
            raise
    
    return wrapper

def optimize_database_queries():
    """تحسين استعلامات قاعدة البيانات"""
    try:
        # إنشاء فهارس للأعمدة المستخدمة بكثرة
        db.session.execute("CREATE INDEX IF NOT EXISTS idx_connection_logs_timestamp ON connection_logs(timestamp);")
        db.session.execute("CREATE INDEX IF NOT EXISTS idx_connection_logs_action ON connection_logs(action);")
        db.session.execute("CREATE INDEX IF NOT EXISTS idx_vnc_sessions_is_active ON vnc_sessions(is_active);")
        
        # تحليل الجداول لتحسين الأداء
        db.session.execute("ANALYZE connection_logs;")
        db.session.execute("ANALYZE vnc_sessions;")
        
        db.session.commit()
        logging.info("Database optimization completed")
        
    except Exception as e:
        logging.error(f"Database optimization failed: {e}")
        try:
            db.session.rollback()
        except:
            pass