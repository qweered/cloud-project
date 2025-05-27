"""
Payment model definitions
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethodType(str, Enum):
    """Payment method type enum."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"


class PaymentBase(BaseModel):
    """Base payment model."""
    ride_id: int
    passenger_id: int
    driver_id: int
    amount: float
    payment_method: str


class PaymentCreate(PaymentBase):
    """Payment creation model."""
    pass


class PaymentUpdate(BaseModel):
    """Payment update model."""
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None


class PaymentResponse(PaymentBase):
    """Payment response model."""
    id: int
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PaymentMethodBase(BaseModel):
    """Base payment method model."""
    user_id: int
    type: PaymentMethodType
    card_number: Optional[str] = None
    card_holder: Optional[str] = None
    expiry_date: Optional[str] = None
    is_default: bool = False


class PaymentMethodCreate(PaymentMethodBase):
    """Payment method creation model."""
    pass


class PaymentMethodUpdate(BaseModel):
    """Payment method update model."""
    card_holder: Optional[str] = None
    expiry_date: Optional[str] = None
    is_default: Optional[bool] = None


class PaymentMethodResponse(PaymentMethodBase):
    """Payment method response model."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True 