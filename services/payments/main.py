"""
Payments Service - Main entry point
"""

import sys
import os
import time
import uuid
import logging
from datetime import datetime
from typing import List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import Depends, HTTPException, status
import uvicorn

from common.base_service import BaseService
from common.metrics import timing_metric
from common.messaging import MessageBroker, PaymentMessage, EXCHANGES, ROUTING_KEYS
from app.models import (
    PaymentCreate, PaymentResponse, PaymentUpdate,
    PaymentMethodCreate, PaymentMethodResponse, PaymentMethodUpdate,
    PaymentStatus, PaymentMethodType
)


# Create the service
service = BaseService("Payments Service", "Payment processing for carpooling application")
app = service.app

# Initialize message broker
message_broker = MessageBroker()
message_broker.declare_exchange(EXCHANGES['PAYMENTS'])

# Setup cleanup for message broker
@app.on_event("shutdown")
async def shutdown_event():
    message_broker.close()

# Add custom metrics
payment_creation_counter = service.metrics.create_counter(
    "payment_creations_total", "Total number of payments created"
)
payment_completion_counter = service.metrics.create_counter(
    "payment_completions_total", "Total number of completed payments"
)
payment_refund_counter = service.metrics.create_counter(
    "payment_refunds_total", "Total number of refunded payments"
)
payment_failure_counter = service.metrics.create_counter(
    "payment_failures_total", "Total number of failed payments"
)
payment_method_counter = service.metrics.create_counter(
    "payment_methods_total", "Total number of payment methods registered"
)
payment_operations_duration = service.metrics.create_histogram(
    "payment_operations_duration_seconds", "Duration of payment operations in seconds"
)
active_payments_gauge = service.metrics.create_gauge(
    "active_payments", "Number of active/pending payments"
)

# Mock databases for demonstration
payments_db = {}
payment_methods_db = {}


@app.post("/payments/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, tags=["Payments"])
@timing_metric(payment_operations_duration)
async def create_payment(payment: PaymentCreate):
    """Create a new payment transaction."""
    payment_id = len(payments_db) + 1
    
    now = datetime.now()
    payment_dict = payment.model_dump()
    payment_dict["id"] = payment_id
    payment_dict["status"] = PaymentStatus.PENDING
    payment_dict["transaction_id"] = str(uuid.uuid4())
    payment_dict["created_at"] = now
    payment_dict["updated_at"] = now
    
    # Store in mock DB
    payments_db[payment_id] = payment_dict
    
    # Increment metrics
    payment_creation_counter.inc()
    active_payments_gauge.inc()
    
    return payment_dict


@app.get("/payments/{payment_id}", response_model=PaymentResponse, tags=["Payments"])
@timing_metric(payment_operations_duration)
async def read_payment(payment_id: int):
    """Get payment details by ID."""
    if payment_id not in payments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payments_db[payment_id]


@app.put("/payments/{payment_id}", response_model=PaymentResponse, tags=["Payments"])
@timing_metric(payment_operations_duration)
async def update_payment(payment_id: int, payment_update: PaymentUpdate):
    """Update payment details."""
    if payment_id not in payments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment = payments_db[payment_id]
    
    update_data = payment_update.model_dump(exclude_unset=True)
    
    # Update payment dictionary with new values
    for field, value in update_data.items():
        payment[field] = value
    
    payment["updated_at"] = datetime.now()
    
    # Update metrics based on status changes
    if "status" in update_data:
        if payment["status"] == PaymentStatus.PENDING:
            active_payments_gauge.dec()
            
        if update_data["status"] == PaymentStatus.COMPLETED:
            payment_completion_counter.inc()
            
            # Publish payment completed message
            try:
                payment_message = PaymentMessage.payment_completed(
                    payment_id=payment_id,
                    user_id=payment["passenger_id"],  # Assuming passenger is the one paying
                    amount=payment["amount"],
                    ride_id=payment["ride_id"]
                )
                message_broker.publish_message(
                    EXCHANGES['PAYMENTS'],
                    ROUTING_KEYS['PAYMENT_COMPLETED'],
                    payment_message
                )
            except Exception as e:
                logging.error(f"Failed to publish payment completed message: {e}")
                
        elif update_data["status"] == PaymentStatus.REFUNDED:
            payment_refund_counter.inc()
        elif update_data["status"] == PaymentStatus.FAILED:
            payment_failure_counter.inc()
            
            # Publish payment failed message
            try:
                payment_message = PaymentMessage.payment_failed(
                    payment_id=payment_id,
                    user_id=payment["passenger_id"],
                    amount=payment["amount"],
                    reason="Payment failed during processing"
                )
                message_broker.publish_message(
                    EXCHANGES['PAYMENTS'],
                    ROUTING_KEYS['PAYMENT_FAILED'],
                    payment_message
                )
            except Exception as e:
                logging.error(f"Failed to publish payment failed message: {e}")
    
    return payment


@app.get("/payments/", response_model=List[PaymentResponse], tags=["Payments"])
@timing_metric(payment_operations_duration)
async def list_payments(
    status: Optional[PaymentStatus] = None,
    passenger_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    ride_id: Optional[int] = None
):
    """List payments with optional filters."""
    filtered_payments = []
    
    for payment_id, payment in payments_db.items():
        if status and payment["status"] != status:
            continue
        if passenger_id and payment["passenger_id"] != passenger_id:
            continue
        if driver_id and payment["driver_id"] != driver_id:
            continue
        if ride_id and payment["ride_id"] != ride_id:
            continue
        filtered_payments.append(payment)
    
    return filtered_payments


@app.post("/payment-methods/", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED, tags=["Payment Methods"])
@timing_metric(payment_operations_duration)
async def create_payment_method(payment_method: PaymentMethodCreate):
    """Register a new payment method."""
    payment_method_id = len(payment_methods_db) + 1
    
    now = datetime.now()
    method_dict = payment_method.model_dump()
    method_dict["id"] = payment_method_id
    method_dict["created_at"] = now
    method_dict["updated_at"] = now
    
    # If this is the first payment method for this user or is_default is True,
    # make it the default and ensure other methods are not default
    if method_dict["is_default"] or not any(m["user_id"] == method_dict["user_id"] for m in payment_methods_db.values()):
        # Set all existing payment methods for this user to not default
        for m_id, m in payment_methods_db.items():
            if m["user_id"] == method_dict["user_id"]:
                m["is_default"] = False
        method_dict["is_default"] = True
    
    # Store in mock DB
    payment_methods_db[payment_method_id] = method_dict
    
    # Increment metrics
    payment_method_counter.inc()
    
    return method_dict


@app.get("/payment-methods/{payment_method_id}", response_model=PaymentMethodResponse, tags=["Payment Methods"])
@timing_metric(payment_operations_duration)
async def read_payment_method(payment_method_id: int):
    """Get payment method details by ID."""
    if payment_method_id not in payment_methods_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return payment_methods_db[payment_method_id]


@app.get("/payment-methods/user/{user_id}", response_model=List[PaymentMethodResponse], tags=["Payment Methods"])
@timing_metric(payment_operations_duration)
async def list_user_payment_methods(user_id: int):
    """List all payment methods for a user."""
    user_methods = [
        method for method in payment_methods_db.values()
        if method["user_id"] == user_id
    ]
    
    return user_methods


@app.get("/payments/statistics", tags=["Statistics"])
async def get_statistics():
    """Get payment service statistics."""
    total_payments = len(payments_db)
    pending_payments = sum(1 for p in payments_db.values() if p["status"] == PaymentStatus.PENDING)
    completed_payments = sum(1 for p in payments_db.values() if p["status"] == PaymentStatus.COMPLETED)
    refunded_payments = sum(1 for p in payments_db.values() if p["status"] == PaymentStatus.REFUNDED)
    failed_payments = sum(1 for p in payments_db.values() if p["status"] == PaymentStatus.FAILED)
    
    total_payment_methods = len(payment_methods_db)
    payment_methods_by_type = {}
    for method_type in PaymentMethodType:
        payment_methods_by_type[method_type.value] = sum(
            1 for m in payment_methods_db.values() if m["type"] == method_type
        )
    
    return {
        "total_payments": total_payments,
        "pending_payments": pending_payments,
        "completed_payments": completed_payments,
        "refunded_payments": refunded_payments,
        "failed_payments": failed_payments,
        "success_rate": 0 if total_payments == 0 else completed_payments / total_payments * 100,
        "total_payment_methods": total_payment_methods,
        "payment_methods_by_type": payment_methods_by_type
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 