# repository/common/metrics.py
from typing import Dict, Any
from datetime import datetime
import logging
from collections import defaultdict

class MetricsCollector:
    """
    Collector for repository performance metrics.
    
    Tracks query performance, cache efficiency, and error rates
    for monitoring and optimization.
    """
    
    def __init__(self, namespace: str):
        """
        Initialize metrics collector.
        
        Args:
            namespace: Metrics namespace for grouping
        """
        self.namespace = namespace
        self.logger = logging.getLogger(f"{__name__}.{namespace}")
        
        self._counters = defaultdict(int)
        self._histograms = defaultdict(list)
        self._gauges = {}
        self._timestamps = {}

    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric."""
        self._counters[metric] += value
        self._timestamps[metric] = datetime.now()

    def observe(self, metric: str, value: float):
        """Record an observation for a histogram metric."""
        self._histograms[metric].append(value)
        self._timestamps[metric] = datetime.now()

    def set_gauge(self, metric: str, value: float):
        """Set a gauge metric value."""
        self._gauges[metric] = value
        self._timestamps[metric] = datetime.now()

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            'counters': dict(self._counters),
            'histograms': {
                name: {
                    'count': len(values),
                    'sum': sum(values),
                    'avg': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0
                }
                for name, values in self._histograms.items()
            },
            'gauges': dict(self._gauges),
            'timestamps': {
                metric: ts.isoformat()
                for metric, ts in self._timestamps.items()
            }
        }

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._histograms.clear()
        self._gauges.clear()
        self._timestamps.clear()

