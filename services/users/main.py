"""
Users Service - Main entry point
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
import uvicorn

from common.base_service import BaseService
from common.metrics import timing_metric
from app.models import UserCreate, UserResponse, UserUpdate
from app.auth import get_current_user, get_password_hash


# Create the service
service = BaseService("Users Service", "User management for carpooling application")
app = service.app

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 