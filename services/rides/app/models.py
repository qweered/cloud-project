"""
Ride model definitions
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class RideStatus(str, Enum):
    """Ride status enum."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PassengerStatus(str, Enum):
    """Passenger status enum."""
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Location(BaseModel):
    """Location model with latitude and longitude."""
    latitude: float
    longitude: float


class RideBase(BaseModel):
    """Base ride model."""
    driver_id: int
    origin_location: Location
    destination_location: Location
    start_time: datetime
    end_time: Optional[datetime] = None
    max_passengers: int = 4
    price_per_seat: float


class RideCreate(RideBase):
    """Ride creation model."""
    pass


class RideUpdate(BaseModel):
    """Ride update model."""
    status: Optional[RideStatus] = None
    current_passengers: Optional[int] = None
    end_time: Optional[datetime] = None


class RideResponse(RideBase):
    """Ride response model."""
    id: int
    status: RideStatus = RideStatus.SCHEDULED
    current_passengers: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PassengerRideBase(BaseModel):
    """Base passenger ride model."""
    ride_id: int
    passenger_id: int
    pickup_location: Location
    dropoff_location: Location


class PassengerRideCreate(PassengerRideBase):
    """Passenger ride creation model."""
    pass


class PassengerRideUpdate(BaseModel):
    """Passenger ride update model."""
    status: Optional[PassengerStatus] = None


class PassengerRideResponse(PassengerRideBase):
    """Passenger ride response model."""
    id: int
    status: PassengerStatus = PassengerStatus.REQUESTED
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True 