"""
Users Service - Main entry point
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import uvicorn

from common.base_service import BaseService
from common.metrics import timing_metric
from common.messaging import MessageBroker, EXCHANGES, ROUTING_KEYS, QUEUES
from app.models import UserCreate, UserResponse, UserUpdate
from app.auth import get_current_user, get_password_hash, verify_password, create_access_token, Token


# Create the service
service = BaseService("Users Service", "User management for carpooling application")
app = service.app

# Initialize message broker
message_broker = MessageBroker()
message_broker.declare_exchange(EXCHANGES['PAYMENTS'])
message_broker.declare_queue(QUEUES['USER_PAYMENT_UPDATES'])
message_broker.bind_queue(QUEUES['USER_PAYMENT_UPDATES'], EXCHANGES['PAYMENTS'], ROUTING_KEYS['PAYMENT_COMPLETED'])
message_broker.bind_queue(QUEUES['USER_PAYMENT_UPDATES'], EXCHANGES['PAYMENTS'], ROUTING_KEYS['PAYMENT_FAILED'])

# Mock user balance tracking (in real app, would be in database)
user_balances = {}

# Message handlers
def handle_payment_messages(message):
    """Handle incoming payment messages"""
    try:
        event_type = message.get('event_type')
        user_id = message.get('user_id')
        amount = message.get('amount', 0)
        
        if event_type == 'payment_completed':
            # Update user's spending/payment history
            if user_id not in user_balances:
                user_balances[user_id] = {'total_spent': 0, 'successful_payments': 0}
            
            user_balances[user_id]['total_spent'] += amount
            user_balances[user_id]['successful_payments'] += 1
            
            logging.info(f"Payment completed for user {user_id}: ${amount}")
            
        elif event_type == 'payment_failed':
            # Track failed payments for user
            if user_id not in user_balances:
                user_balances[user_id] = {'total_spent': 0, 'successful_payments': 0, 'failed_payments': 0}
            
            if 'failed_payments' not in user_balances[user_id]:
                user_balances[user_id]['failed_payments'] = 0
                
            user_balances[user_id]['failed_payments'] += 1
            
            logging.info(f"Payment failed for user {user_id}: ${amount}")
            
        return True  # Message processed successfully
        
    except Exception as e:
        logging.error(f"Error processing payment message: {e}")
        return False  # Requeue message

# Setup message consumer
message_broker.add_consumer(QUEUES['USER_PAYMENT_UPDATES'], handle_payment_messages)
message_broker.start_consuming()

# Setup cleanup for message broker
@app.on_event("shutdown")
async def shutdown_event():
    message_broker.close()

# Add custom metrics
user_creation_counter = service.metrics.create_counter(
    "user_creations_total", "Total number of users created"
)
user_auth_counter = service.metrics.create_counter(
    "user_auth_total", "Total number of user authentication attempts"
)
auth_failure_counter = service.metrics.create_counter(
    "auth_failures_total", "Total number of authentication failures"
)
user_operations_duration = service.metrics.create_histogram(
    "user_operations_duration_seconds", "Duration of user operations in seconds"
)

# Mock user database for demonstration
users_db = {}


@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
@timing_metric(user_operations_duration)
async def create_user(user: UserCreate):
    """Create a new user."""
    if user.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create user with hashed password
    user_dict = user.model_dump()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    user_dict["id"] = len(users_db) + 1
    
    # Store in mock DB
    users_db[user.email] = user_dict
    
    # Increment metrics
    user_creation_counter.inc()
    
    return user_dict


@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token."""
    user = users_db.get(form_data.username)
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        auth_failure_counter.inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_auth_counter.inc()
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse, tags=["Users"])
@timing_metric(user_operations_duration)
async def read_users_me(current_user=Depends(get_current_user)):
    """Get current user details."""
    return current_user


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
@timing_metric(user_operations_duration)
async def read_user(user_id: int, current_user=Depends(get_current_user)):
    """Get user by ID."""
    for email, user in users_db.items():
        if user["id"] == user_id:
            return user
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@app.put("/users/me", response_model=UserResponse, tags=["Users"])
@timing_metric(user_operations_duration)
async def update_user(user_update: UserUpdate, current_user=Depends(get_current_user)):
    """Update current user details."""
    user = users_db[current_user["email"]]
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Update user dictionary with new values
    for field, value in update_data.items():
        if field == "password":
            user["hashed_password"] = get_password_hash(value)
        else:
            user[field] = value
    
    return user


@app.get("/users/{user_id}/payment-stats", tags=["Users"])
@timing_metric(user_operations_duration)
async def get_user_payment_stats(user_id: int, current_user=Depends(get_current_user)):
    """Get user's payment statistics."""
    # In a real app, you'd verify the user has permission to view this data
    stats = user_balances.get(user_id, {
        'total_spent': 0,
        'successful_payments': 0,
        'failed_payments': 0
    })
    
    return {
        'user_id': user_id,
        'payment_statistics': stats
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 