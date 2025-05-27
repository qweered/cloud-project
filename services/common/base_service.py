"""
Base service module with common functionality for all microservices.
Includes health and metrics endpoints.
"""

import os
import time
import socket
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .metrics import MetricsRegistry


class BaseService:
    """Base class for all microservices with common functionality."""

    def __init__(self, name: str, description: str):
        """Initialize a new service with the given name and description."""
        self.name = name
        self.app = FastAPI(title=name, description=description)
        self.metrics = MetricsRegistry(name.lower().replace('-', '_'))
        self.start_time = time.time()
        self.hostname = socket.gethostname()
        
        # Register common metrics
        self.request_counter = self.metrics.create_counter(
            "requests_total", "Total number of requests received"
        )
        self.request_duration = self.metrics.create_histogram(
            "request_duration_seconds", "Request duration in seconds"
        )
        self.error_counter = self.metrics.create_counter(
            "errors_total", "Total number of errors"
        )
        self.active_requests = self.metrics.create_gauge(
            "active_requests", "Number of active requests"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register middleware
        self.app.middleware("http")(self._metrics_middleware)
        
        # Register common endpoints
        self.register_common_endpoints()
    
    async def _metrics_middleware(self, request: Request, call_next):
        """Middleware to collect request metrics."""
        self.active_requests.increment()
        self.request_counter.increment()
        
        start_time = time.time()
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            self.error_counter.increment()
            raise e
        finally:
            process_time = time.time() - start_time
            self.request_duration.observe(process_time)
            self.active_requests.decrement()
    
    def register_common_endpoints(self):
        """Register common endpoints for health and metrics."""
        
        @self.app.get("/health", tags=["Health"])
        async def health_check():
            """Health check endpoint."""
            uptime = time.time() - self.start_time
            return {
                "status": "ok",
                "service": self.name,
                "uptime_seconds": uptime,
                "hostname": self.hostname
            }
        
        @self.app.get("/ping", tags=["Health"])
        async def ping():
            """Simple ping endpoint."""
            return {"pong": True}
        
        @self.app.get("/metrics", response_class=PlainTextResponse, tags=["Metrics"])
        async def metrics():
            """Prometheus-compatible metrics endpoint."""
            return self.metrics.generate_metrics_text()
        
        @self.app.get("/info", tags=["Info"])
        async def info():
            """Service information endpoint."""
            return {
                "name": self.name,
                "description": self.app.description,
                "version": os.environ.get("SERVICE_VERSION", "0.1.0"),
                "environment": os.environ.get("ENVIRONMENT", "development")
            } 