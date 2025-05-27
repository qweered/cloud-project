"""
Unit tests for the metrics module
"""

import time
import unittest
from unittest.mock import patch

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.metrics import (
    MetricsRegistry, CounterMetric, GaugeMetric, 
    HistogramMetric, timing_metric
)


class TestMetrics(unittest.TestCase):
    """Test suite for metrics functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = MetricsRegistry("test_service")
    
    def test_counter_metric(self):
        """Test counter metric functionality."""
        counter = self.registry.create_counter("test_counter", "Test counter")
        self.assertEqual(counter.value, 0)
        
        counter.increment()
        self.assertEqual(counter.value, 1)
        
        counter.increment(5)
        self.assertEqual(counter.value, 6)
    
    def test_gauge_metric(self):
        """Test gauge metric functionality."""
        gauge = self.registry.create_gauge("test_gauge", "Test gauge")
        self.assertEqual(gauge.value, 0.0)
        
        gauge.set(10.5)
        self.assertEqual(gauge.value, 10.5)
        
        gauge.increment(1.5)
        self.assertEqual(gauge.value, 12.0)
        
        gauge.decrement(3.0)
        self.assertEqual(gauge.value, 9.0)
    
    def test_histogram_metric(self):
        """Test histogram metric functionality."""
        histogram = self.registry.create_histogram(
            "test_histogram", "Test histogram", 
            buckets=[0.1, 0.5, 1.0]
        )
        
        self.assertEqual(histogram.count, 0)
        self.assertEqual(histogram.sum, 0.0)
        
        histogram.observe(0.2)
        self.assertEqual(histogram.count, 1)
        self.assertEqual(histogram.sum, 0.2)
        self.assertEqual(histogram.values[0.1], 0)
        self.assertEqual(histogram.values[0.5], 1)
        self.assertEqual(histogram.values[1.0], 1)
        
        histogram.observe(0.05)
        self.assertEqual(histogram.count, 2)
        self.assertEqual(histogram.sum, 0.25)
        self.assertEqual(histogram.values[0.1], 1)
        self.assertEqual(histogram.values[0.5], 2)
        self.assertEqual(histogram.values[1.0], 2)
    
    def test_timing_decorator(self):
        """Test timing decorator functionality."""
        histogram = self.registry.create_histogram("timing", "Timing test")
        
        @timing_metric(histogram)
        def test_function():
            time.sleep(0.1)
            return 42
        
        result = test_function()
        
        self.assertEqual(result, 42)
        self.assertEqual(histogram.count, 1)
        self.assertGreaterEqual(histogram.sum, 0.1)
        
    def test_prometheus_format(self):
        """Test Prometheus text format generation."""
        # Create some test metrics
        counter = self.registry.create_counter("requests", "Request count")
        counter.increment(5)
        
        gauge = self.registry.create_gauge("memory", "Memory usage")
        gauge.set(1024.5)
        
        histogram = self.registry.create_histogram(
            "latency", "Request latency", 
            buckets=[0.1, 0.5, 1.0]
        )
        histogram.observe(0.2)
        
        # Generate metrics text
        metrics_text = self.registry.generate_metrics_text()
        
        # Verify counter format
        self.assertIn("# HELP test_service_requests Request count", metrics_text)
        self.assertIn("# TYPE test_service_requests counter", metrics_text)
        self.assertIn("test_service_requests 5", metrics_text)
        
        # Verify gauge format
        self.assertIn("# HELP test_service_memory Memory usage", metrics_text)
        self.assertIn("# TYPE test_service_memory gauge", metrics_text)
        self.assertIn("test_service_memory 1024.5", metrics_text)
        
        # Verify histogram format
        self.assertIn("# HELP test_service_latency Request latency", metrics_text)
        self.assertIn("# TYPE test_service_latency histogram", metrics_text)
        self.assertIn("test_service_latency_bucket{le=\"0.1\"} 0", metrics_text)
        self.assertIn("test_service_latency_bucket{le=\"0.5\"} 1", metrics_text)
        self.assertIn("test_service_latency_bucket{le=\"1.0\"} 1", metrics_text)
        self.assertIn("test_service_latency_sum 0.2", metrics_text)
        self.assertIn("test_service_latency_count 1", metrics_text)


if __name__ == "__main__":
    unittest.main() 