"""
Performance monitoring and metrics collection system.
Provides decorators, context managers, and utilities for tracking performance.
"""

import time
import functools
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import json

from .logger import get_logger


@dataclass
class PerformanceMetric:
    """Represents a single performance metric."""
    operation: str
    component: str
    duration: float
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary for serialization."""
        return {
            'operation': self.operation,
            'component': self.component,
            'duration': self.duration,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'metadata': self.metadata
        }


class PerformanceTracker:
    """Thread-safe performance metrics tracker."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'error_count': 0,
            'success_rate': 0.0
        })
        self._lock = threading.Lock()
        self.logger = get_logger('performance')
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)
            self._update_stats(metric)
            
        # Log significant performance events
        if metric.duration > 10.0:  # Log operations taking more than 10 seconds
            self.logger.warning(
                f"Slow operation detected: {metric.operation}",
                operation='performance_monitoring',
                extra_data={
                    'component': metric.component,
                    'duration': metric.duration,
                    'metadata': metric.metadata
                }
            )
    
    def _update_stats(self, metric: PerformanceMetric):
        """Update running statistics for an operation."""
        key = f"{metric.component}:{metric.operation}"
        stats = self.stats[key]
        
        stats['count'] += 1
        stats['total_time'] += metric.duration
        stats['min_time'] = min(stats['min_time'], metric.duration)
        stats['max_time'] = max(stats['max_time'], metric.duration)
        
        if not metric.success:
            stats['error_count'] += 1
        
        stats['success_rate'] = ((stats['count'] - stats['error_count']) / stats['count']) * 100
        stats['avg_time'] = stats['total_time'] / stats['count']
    
    def get_stats(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            if component:
                return {k: v for k, v in self.stats.items() if k.startswith(f"{component}:")}
            return dict(self.stats)
    
    def get_recent_metrics(self, minutes: int = 60) -> List[PerformanceMetric]:
        """Get metrics from the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self._lock:
            return [m for m in self.metrics if m.timestamp >= cutoff]
    
    def export_metrics(self, file_path: str):
        """Export metrics to a JSON file."""
        with self._lock:
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'metrics': [m.to_dict() for m in self.metrics],
                'stats': dict(self.stats)
            }
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def clear_metrics(self):
        """Clear all stored metrics and reset statistics."""
        with self._lock:
            self.metrics.clear()
            self.stats.clear()


# Global performance tracker
_performance_tracker = PerformanceTracker()


@contextmanager
def track_performance(operation: str, component: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for tracking operation performance."""
    start_time = time.time()
    success = True
    error = None
    
    try:
        yield
    except Exception as e:
        success = False
        error = e
        raise
    finally:
        duration = time.time() - start_time
        metric = PerformanceMetric(
            operation=operation,
            component=component,
            duration=duration,
            timestamp=datetime.now(),
            success=success,
            metadata=metadata or {}
        )
        
        if error:
            metric.metadata['error'] = str(error)
            metric.metadata['error_type'] = type(error).__name__
        
        _performance_tracker.record_metric(metric)


def performance_monitor(operation: Optional[str] = None, component: Optional[str] = None):
    """Decorator for monitoring function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            comp_name = component or func.__module__.split('.')[-1]
            
            metadata = {
                'function': func.__name__,
                'module': func.__module__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            }
            
            with track_performance(op_name, comp_name, metadata):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class PerformanceReporter:
    """Generates performance reports and summaries."""
    
    def __init__(self, tracker: Optional[PerformanceTracker] = None):
        self.tracker = tracker or _performance_tracker
        self.logger = get_logger('performance_reporter')
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance summary."""
        stats = self.tracker.get_stats()
        recent_metrics = self.tracker.get_recent_metrics(60)  # Last hour
        
        summary = {
            'report_timestamp': datetime.now().isoformat(),
            'total_operations': len(self.tracker.metrics),
            'recent_operations': len(recent_metrics),
            'components': self._analyze_components(stats),
            'slowest_operations': self._find_slowest_operations(stats),
            'error_analysis': self._analyze_errors(stats),
            'performance_trends': self._analyze_trends(recent_metrics)
        }
        
        return summary
    
    def _analyze_components(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance by component."""
        components = defaultdict(lambda: {
            'operation_count': 0,
            'total_time': 0.0,
            'error_count': 0,
            'avg_time': 0.0
        })
        
        for key, stat in stats.items():
            component = key.split(':')[0]
            comp_stats = components[component]
            comp_stats['operation_count'] += stat['count']
            comp_stats['total_time'] += stat['total_time']
            comp_stats['error_count'] += stat['error_count']
        
        # Calculate averages
        for comp_stats in components.values():
            if comp_stats['operation_count'] > 0:
                comp_stats['avg_time'] = comp_stats['total_time'] / comp_stats['operation_count']
        
        return dict(components)
    
    def _find_slowest_operations(self, stats: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Find the slowest operations."""
        operations = []
        for key, stat in stats.items():
            if stat['count'] > 0:
                operations.append({
                    'operation': key,
                    'avg_time': stat['avg_time'],
                    'max_time': stat['max_time'],
                    'count': stat['count']
                })
        
        return sorted(operations, key=lambda x: x['avg_time'], reverse=True)[:limit]
    
    def _analyze_errors(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error patterns."""
        total_operations = sum(stat['count'] for stat in stats.values())
        total_errors = sum(stat['error_count'] for stat in stats.values())
        
        error_prone_operations = []
        for key, stat in stats.items():
            if stat['error_count'] > 0:
                error_rate = (stat['error_count'] / stat['count']) * 100
                error_prone_operations.append({
                    'operation': key,
                    'error_count': stat['error_count'],
                    'total_count': stat['count'],
                    'error_rate': error_rate
                })
        
        error_prone_operations.sort(key=lambda x: x['error_rate'], reverse=True)
        
        return {
            'total_operations': total_operations,
            'total_errors': total_errors,
            'overall_error_rate': (total_errors / total_operations * 100) if total_operations > 0 else 0,
            'error_prone_operations': error_prone_operations[:10]
        }
    
    def _analyze_trends(self, recent_metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance trends."""
        if not recent_metrics:
            return {'message': 'No recent metrics available'}
        
        # Group by 5-minute intervals
        intervals = defaultdict(list)
        for metric in recent_metrics:
            interval = metric.timestamp.replace(minute=(metric.timestamp.minute // 5) * 5, second=0, microsecond=0)
            intervals[interval].append(metric)
        
        trends = []
        for interval, metrics in sorted(intervals.items()):
            avg_duration = sum(m.duration for m in metrics) / len(metrics)
            success_rate = (sum(1 for m in metrics if m.success) / len(metrics)) * 100
            
            trends.append({
                'timestamp': interval.isoformat(),
                'operation_count': len(metrics),
                'avg_duration': avg_duration,
                'success_rate': success_rate
            })
        
        return {
            'interval_count': len(trends),
            'trends': trends
        }
    
    def log_performance_summary(self):
        """Log a performance summary."""
        summary = self.generate_summary_report()
        
        self.logger.info(
            f"Performance Summary: {summary['total_operations']} total operations, "
            f"{summary['recent_operations']} in last hour",
            operation='performance_summary',
            extra_data=summary
        )


# Convenience functions
def get_performance_stats(component: Optional[str] = None) -> Dict[str, Any]:
    """Get performance statistics."""
    return _performance_tracker.get_stats(component)


def export_performance_data(file_path: str):
    """Export performance data to file."""
    _performance_tracker.export_metrics(file_path)


def generate_performance_report() -> Dict[str, Any]:
    """Generate a performance report."""
    reporter = PerformanceReporter()
    return reporter.generate_summary_report()


def log_performance_summary():
    """Log current performance summary."""
    reporter = PerformanceReporter()
    reporter.log_performance_summary() 