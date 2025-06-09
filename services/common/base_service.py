"""
Base service class for all microservices
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from typing import Optional
import time


class Metrics:
    """Prometheus metrics collection"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
    def create_counter(self, name: str, description: str, labels: list = None):
        """Create a new counter metric"""
        return Counter(name, description, labels or [])
    
    def create_histogram(self, name: str, description: str, labels: list = None):
        """Create a new histogram metric"""
        return Histogram(name, description, labels or [])
        
    def create_gauge(self, name: str, description: str, labels: list = None):
        """Create a new gauge metric"""
        return Gauge(name, description, labels or [])


class BaseService:
    """Base class for all microservices"""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        
        # Create FastAPI app
        self.app = FastAPI(
            title=name,
            description=description,
            version=version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize metrics
        self.metrics = Metrics(name)
        
        # Add middleware for metrics
        self.app.middleware("http")(self._metrics_middleware)
        
        # Add health endpoints
        self._add_health_endpoints()
        
    async def _metrics_middleware(self, request: Request, call_next):
        """Middleware to collect metrics"""
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record metrics
        process_time = time.time() - start_time
        self.metrics.request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)
        
        self.metrics.request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        return response
    
    def _add_health_endpoints(self):
        """Add standard health check endpoints"""
        
        @self.app.get("/health", tags=["Health"])
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": self.name,
                "version": self.version
            }
        
        @self.app.get("/metrics", tags=["Metrics"])
        async def get_metrics():
            """Prometheus metrics endpoint"""
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                generate_latest(),
                media_type="text/plain"
            ) 