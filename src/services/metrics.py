"""
Performance monitoring and metrics for coffee brewing services
"""

import time
import functools
from typing import Dict, Any, Callable
from collections import defaultdict, deque
import logging


class ServiceMetrics:
    """Track performance metrics for services"""
    
    def __init__(self):
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.logger = logging.getLogger(f"{__name__}.ServiceMetrics")
    
    def record_call(self, service_method: str, execution_time: float):
        """Record a service method call"""
        self.call_counts[service_method] += 1
        self.execution_times[service_method].append(execution_time)
    
    def record_error(self, service_method: str):
        """Record a service method error"""
        self.error_counts[service_method] += 1
    
    def get_stats(self, service_method: str) -> Dict[str, Any]:
        """Get statistics for a service method"""
        times = list(self.execution_times[service_method])
        
        if not times:
            return {
                'calls': 0,
                'errors': self.error_counts[service_method],
                'avg_time': 0,
                'min_time': 0,
                'max_time': 0,
                'error_rate': 0
            }
        
        total_calls = self.call_counts[service_method]
        total_errors = self.error_counts[service_method]
        
        return {
            'calls': total_calls,
            'errors': total_errors,
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'error_rate': (total_errors / total_calls) * 100 if total_calls > 0 else 0
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tracked methods"""
        all_methods = set(self.call_counts.keys()) | set(self.error_counts.keys())
        return {method: self.get_stats(method) for method in all_methods}
    
    def log_performance_summary(self):
        """Log a performance summary"""
        stats = self.get_all_stats()
        
        if not stats:
            self.logger.info("No service metrics to report")
            return
        
        self.logger.info("=== Service Performance Summary ===")
        
        for method, data in stats.items():
            if data['calls'] > 0:
                self.logger.info(
                    f"{method}: {data['calls']} calls, "
                    f"avg {data['avg_time']:.3f}s, "
                    f"error rate {data['error_rate']:.1f}%"
                )


# Global metrics instance
_service_metrics = ServiceMetrics()


def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor service method performance"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        method_name = f"{func.__qualname__}"
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            _service_metrics.record_call(method_name, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            _service_metrics.record_call(method_name, execution_time)
            _service_metrics.record_error(method_name)
            raise
    
    return wrapper


def get_service_metrics() -> ServiceMetrics:
    """Get the global metrics instance"""
    return _service_metrics