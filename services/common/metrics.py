"""
Common metrics module for all services.
Provides standardized metrics endpoints compatible with Prometheus.
"""

import time
from typing import Dict, List, Optional, Callable
from functools import wraps
from dataclasses import dataclass, field


@dataclass
class MetricValue:
    """Base class for a metric value."""
    name: str
    description: str
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class CounterMetric(MetricValue):
    """A counter metric that only increases."""
    value: int = 0

    def increment(self, amount: int = 1):
        """Increment the counter by the given amount."""
        self.value += amount


@dataclass
class GaugeMetric(MetricValue):
    """A gauge metric that can go up and down."""
    value: float = 0.0

    def set(self, value: float):
        """Set the gauge to a specific value."""
        self.value = value

    def increment(self, amount: float = 1.0):
        """Increment the gauge by the given amount."""
        self.value += amount

    def decrement(self, amount: float = 1.0):
        """Decrement the gauge by the given amount."""
        self.value -= amount


@dataclass
class HistogramMetric(MetricValue):
    """A histogram metric for measuring distributions."""
    buckets: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.1, 0.5, 1, 5])
    values: Dict[float, int] = field(default_factory=dict)
    sum: float = 0.0
    count: int = 0

    def __post_init__(self):
        """Initialize buckets."""
        for bucket in self.buckets:
            self.values[bucket] = 0

    def observe(self, value: float):
        """Add an observation to the histogram."""
        self.sum += value
        self.count += 1
        for bucket in self.buckets:
            if value <= bucket:
                self.values[bucket] += 1


class MetricsRegistry:
    """Registry for all metrics in a service."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.counters: Dict[str, CounterMetric] = {}
        self.gauges: Dict[str, GaugeMetric] = {}
        self.histograms: Dict[str, HistogramMetric] = {}

    def create_counter(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> CounterMetric:
        """Create and register a new counter metric."""
        full_name = f"{self.service_name}_{name}"
        counter = CounterMetric(full_name, description, labels or {})
        self.counters[full_name] = counter
        return counter

    def create_gauge(self, name: str, description: str, labels: Optional[Dict[str, str]] = None) -> GaugeMetric:
        """Create and register a new gauge metric."""
        full_name = f"{self.service_name}_{name}"
        gauge = GaugeMetric(full_name, description, labels or {})
        self.gauges[full_name] = gauge
        return gauge

    def create_histogram(
        self, name: str, description: str, buckets: Optional[List[float]] = None, 
        labels: Optional[Dict[str, str]] = None
    ) -> HistogramMetric:
        """Create and register a new histogram metric."""
        full_name = f"{self.service_name}_{name}"
        histogram = HistogramMetric(full_name, description, labels or {}, buckets or [0.01, 0.05, 0.1, 0.5, 1, 5])
        self.histograms[full_name] = histogram
        return histogram

    def generate_metrics_text(self) -> str:
        """Generate metrics in Prometheus text format."""
        lines = []

        # Add counters
        for name, counter in self.counters.items():
            labels_str = ','.join([f'{k}="{v}"' for k, v in counter.labels.items()])
            labels_fmt = f'{{{labels_str}}}' if labels_str else ''
            lines.append(f"# HELP {name} {counter.description}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name}{labels_fmt} {counter.value}")

        # Add gauges
        for name, gauge in self.gauges.items():
            labels_str = ','.join([f'{k}="{v}"' for k, v in gauge.labels.items()])
            labels_fmt = f'{{{labels_str}}}' if labels_str else ''
            lines.append(f"# HELP {name} {gauge.description}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{labels_fmt} {gauge.value}")

        # Add histograms
        for name, histogram in self.histograms.items():
            labels_str = ','.join([f'{k}="{v}"' for k, v in histogram.labels.items()])
            base_labels_fmt = f'{{{labels_str}}}' if labels_str else ''
            
            lines.append(f"# HELP {name} {histogram.description}")
            lines.append(f"# TYPE {name} histogram")
            
            # Add bucket metrics
            for bucket, count in histogram.values.items():
                bucket_labels = f'{{{labels_str + "," if labels_str else ""}le="{bucket}"}}'
                lines.append(f"{name}_bucket{bucket_labels} {count}")
            
            # Add sum and count metrics
            lines.append(f"{name}_sum{base_labels_fmt} {histogram.sum}")
            lines.append(f"{name}_count{base_labels_fmt} {histogram.count}")

        return '\n'.join(lines)


def timing_metric(histogram: HistogramMetric) -> Callable:
    """Decorator to measure execution time of a function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            histogram.observe(execution_time)
            return result
        return wrapper
    return decorator 