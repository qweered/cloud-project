"""
User model definitions
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enum."""
    DRIVER = "driver"
    PASSENGER = "passenger"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str
    role: UserRole = UserRole.PASSENGER


class UserCreate(UserBase):
    """User creation model."""
    password: str
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None
    max_passengers: Optional[int] = None


class UserUpdate(BaseModel):
    """User update model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None
    max_passengers: Optional[int] = None


class UserResponse(UserBase):
    """User response model."""
    id: int
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None
    max_passengers: Optional[int] = None

    class Config:
        """Pydantic configuration."""
        from_attributes = True 