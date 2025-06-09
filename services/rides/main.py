"""
Rides Service - Main entry point
"""

import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import Depends, HTTPException, status
import uvicorn

from common.base_service import BaseService
from common.metrics import timing_metric
from common.messaging import MessageBroker, RideMessage, EXCHANGES, ROUTING_KEYS
from app.models import (
    RideCreate, RideResponse, RideUpdate,
    PassengerRideCreate, PassengerRideResponse, PassengerRideUpdate,
    RideStatus, PassengerStatus
)


# Create the service
service = BaseService("Rides Service", "Ride management for carpooling application")
app = service.app

# Initialize message broker
message_broker = MessageBroker()
message_broker.declare_exchange(EXCHANGES['RIDES'])

# Setup cleanup for message broker
@app.on_event("shutdown")
async def shutdown_event():
    message_broker.close()

# Add custom metrics
ride_creation_counter = service.metrics.create_counter(
    "ride_creations_total", "Total number of rides created"
)
ride_completion_counter = service.metrics.create_counter(
    "ride_completions_total", "Total number of completed rides"
)
ride_cancellation_counter = service.metrics.create_counter(
    "ride_cancellations_total", "Total number of cancelled rides"
)
passenger_request_counter = service.metrics.create_counter(
    "passenger_requests_total", "Total number of passenger ride requests"
)
ride_operations_duration = service.metrics.create_histogram(
    "ride_operations_duration_seconds", "Duration of ride operations in seconds"
)
active_rides_gauge = service.metrics.create_gauge(
    "active_rides", "Number of active rides"
)

# Mock databases for demonstration
rides_db = {}
passenger_rides_db = {}


@app.post("/rides/", response_model=RideResponse, status_code=status.HTTP_201_CREATED, tags=["Rides"])
@timing_metric(ride_operations_duration)
async def create_ride(ride: RideCreate):
    """Create a new ride offer."""
    ride_id = len(rides_db) + 1
    
    now = datetime.now()
    ride_dict = ride.model_dump()
    ride_dict["id"] = ride_id
    ride_dict["status"] = RideStatus.SCHEDULED
    ride_dict["current_passengers"] = 0
    ride_dict["created_at"] = now
    ride_dict["updated_at"] = now
    
    # Store in mock DB
    rides_db[ride_id] = ride_dict
    
    # Increment metrics
    ride_creation_counter.inc()
    active_rides_gauge.inc()
    
    # Publish ride creation message
    try:
        ride_message = RideMessage.ride_created(
            ride_id=ride_id,
            driver_id=ride.driver_id,
            pickup_location={'lat': ride.origin_location.latitude, 'lng': ride.origin_location.longitude},
            dropoff_location={'lat': ride.destination_location.latitude, 'lng': ride.destination_location.longitude},
            departure_time=ride.start_time.isoformat(),
            max_passengers=ride.max_passengers
        )
        message_broker.publish_message(
            EXCHANGES['RIDES'],
            ROUTING_KEYS['RIDE_CREATED'],
            ride_message
        )
    except Exception as e:
        logging.error(f"Failed to publish ride creation message: {e}")
    
    return ride_dict


@app.get("/rides/{ride_id}", response_model=RideResponse, tags=["Rides"])
@timing_metric(ride_operations_duration)
async def read_ride(ride_id: int):
    """Get ride details by ID."""
    if ride_id not in rides_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    return rides_db[ride_id]


@app.get("/rides/", response_model=List[RideResponse], tags=["Rides"])
@timing_metric(ride_operations_duration)
async def list_rides(status: Optional[RideStatus] = None, driver_id: Optional[int] = None):
    """List available rides with optional filters."""
    filtered_rides = []
    
    for ride_id, ride in rides_db.items():
        if status and ride["status"] != status:
            continue
        if driver_id and ride["driver_id"] != driver_id:
            continue
        filtered_rides.append(ride)
    
    return filtered_rides


@app.put("/rides/{ride_id}", response_model=RideResponse, tags=["Rides"])
@timing_metric(ride_operations_duration)
async def update_ride(ride_id: int, ride_update: RideUpdate):
    """Update ride details."""
    if ride_id not in rides_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    ride = rides_db[ride_id]
    
    update_data = ride_update.model_dump(exclude_unset=True)
    
    # Update ride dictionary with new values
    for field, value in update_data.items():
        ride[field] = value
    
    ride["updated_at"] = datetime.now()
    
    # Update metrics based on status changes
    if "status" in update_data:
        if update_data["status"] == RideStatus.COMPLETED:
            ride_completion_counter.inc()
            active_rides_gauge.dec()
        elif update_data["status"] == RideStatus.CANCELLED:
            ride_cancellation_counter.inc()
            active_rides_gauge.dec()
        
        # Publish ride update message
        try:
            ride_message = RideMessage.ride_updated(
                ride_id=ride_id,
                status=update_data["status"],
                current_passengers=ride["current_passengers"]
            )
            message_broker.publish_message(
                EXCHANGES['RIDES'],
                ROUTING_KEYS['RIDE_UPDATED'],
                ride_message
            )
        except Exception as e:
            logging.error(f"Failed to publish ride update message: {e}")
    
    return ride


@app.post("/rides/{ride_id}/passengers/", response_model=PassengerRideResponse, status_code=status.HTTP_201_CREATED, tags=["Passengers"])
@timing_metric(ride_operations_duration)
async def request_ride(ride_id: int, passenger_ride: PassengerRideCreate):
    """Request to join a ride as a passenger."""
    if ride_id not in rides_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    ride = rides_db[ride_id]
    
    if ride["status"] != RideStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride is not available for booking"
        )
    
    if ride["current_passengers"] >= ride["max_passengers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride is already full"
        )
    
    # Create passenger ride request
    passenger_ride_id = len(passenger_rides_db) + 1
    now = datetime.now()
    
    passenger_ride_dict = passenger_ride.model_dump()
    passenger_ride_dict["id"] = passenger_ride_id
    passenger_ride_dict["status"] = PassengerStatus.REQUESTED
    passenger_ride_dict["created_at"] = now
    passenger_ride_dict["updated_at"] = now
    
    # Store in mock DB
    passenger_rides_db[passenger_ride_id] = passenger_ride_dict
    
    # Increment metrics
    passenger_request_counter.inc()
    
    return passenger_ride_dict


@app.put("/rides/passengers/{passenger_ride_id}", response_model=PassengerRideResponse, tags=["Passengers"])
@timing_metric(ride_operations_duration)
async def update_passenger_ride_status(passenger_ride_id: int, update: PassengerRideUpdate):
    """Update the status of a passenger's ride request."""
    if passenger_ride_id not in passenger_rides_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger ride request not found"
        )
    
    passenger_ride = passenger_rides_db[passenger_ride_id]
    ride_id = passenger_ride["ride_id"]
    
    if ride_id not in rides_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated ride not found"
        )
    
    ride = rides_db[ride_id]
    
    update_data = update.model_dump(exclude_unset=True)
    
    # Update passenger ride with new values
    for field, value in update_data.items():
        passenger_ride[field] = value
    
    passenger_ride["updated_at"] = datetime.now()
    
    # Update ride's current_passengers count based on status change
    if "status" in update_data:
        if update_data["status"] == PassengerStatus.ACCEPTED:
            ride["current_passengers"] += 1
            
            # Publish passenger joined message
            try:
                passenger_message = RideMessage.passenger_joined(
                    ride_id=ride_id,
                    passenger_id=passenger_ride["passenger_id"]
                )
                message_broker.publish_message(
                    EXCHANGES['RIDES'],
                    ROUTING_KEYS['PASSENGER_JOINED'],
                    passenger_message
                )
            except Exception as e:
                logging.error(f"Failed to publish passenger joined message: {e}")
                
        elif passenger_ride["status"] == PassengerStatus.ACCEPTED and update_data["status"] in [PassengerStatus.CANCELLED, PassengerStatus.REJECTED]:
            ride["current_passengers"] -= 1
    
    return passenger_ride


@app.get("/rides/statistics", tags=["Statistics"])
async def get_statistics():
    """Get ride service statistics."""
    total_rides = len(rides_db)
    active_rides = sum(1 for ride in rides_db.values() if ride["status"] in [RideStatus.SCHEDULED, RideStatus.IN_PROGRESS])
    completed_rides = sum(1 for ride in rides_db.values() if ride["status"] == RideStatus.COMPLETED)
    cancelled_rides = sum(1 for ride in rides_db.values() if ride["status"] == RideStatus.CANCELLED)
    
    total_passenger_requests = len(passenger_rides_db)
    accepted_requests = sum(1 for pr in passenger_rides_db.values() if pr["status"] == PassengerStatus.ACCEPTED)
    
    return {
        "total_rides": total_rides,
        "active_rides": active_rides,
        "completed_rides": completed_rides,
        "cancelled_rides": cancelled_rides,
        "total_passenger_requests": total_passenger_requests,
        "accepted_requests": accepted_requests,
        "average_passengers_per_ride": 0 if total_rides == 0 else accepted_requests / total_rides
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 