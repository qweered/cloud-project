"""
Matching Service - Main entry point
"""

import sys
import os
import time
import random
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn
import requests

from common.base_service import BaseService
from common.metrics import timing_metric


class Location(BaseModel):
    """Location model with latitude and longitude."""
    latitude: float
    longitude: float


class RideRequest(BaseModel):
    """Ride request model."""
    passenger_id: int
    pickup_location: Location
    dropoff_location: Location
    requested_time: str
    max_wait_time: Optional[int] = 10  # minutes
    max_detour_time: Optional[int] = 15  # minutes


class MatchResponse(BaseModel):
    """Match response model."""
    ride_id: int
    driver_id: int
    passenger_id: int
    pickup_time: str
    estimated_arrival_time: str
    price: float


# Create the service
service = BaseService("Matching Service", "Matching passengers with drivers for carpooling")
app = service.app

# Add custom metrics
match_request_counter = service.metrics.create_counter(
    "match_requests_total", "Total number of match requests"
)
successful_matches_counter = service.metrics.create_counter(
    "successful_matches_total", "Total number of successful matches"
)
failed_matches_counter = service.metrics.create_counter(
    "failed_matches_total", "Total number of failed matches"
)
match_duration_histogram = service.metrics.create_histogram(
    "match_duration_seconds", "Duration of match operations in seconds"
)
active_ride_requests_gauge = service.metrics.create_gauge(
    "active_ride_requests", "Number of active ride requests"
)
available_drivers_gauge = service.metrics.create_gauge(
    "available_drivers", "Number of available drivers"
)

# Mock data for demonstration
available_drivers_gauge.set(random.randint(5, 20))


@app.post("/match", response_model=MatchResponse, tags=["Matching"])
@timing_metric(match_duration_histogram)
async def match_ride(request: RideRequest):
    """
    Match a passenger with an available driver.
    
    This is the core matching algorithm that finds the best driver
    based on location, timing, and other preferences.
    """
    # Increment metrics
    match_request_counter.inc()
    active_ride_requests_gauge.inc()
    
    try:
        # Simulate matching algorithm execution time
        time.sleep(random.uniform(0.2, 1.0))
        
        # Simulate a successful match (in a real implementation, this would query the rides service)
        match_success = random.random() > 0.2  # 80% success rate
        
        if not match_success:
            failed_matches_counter.inc()
            active_ride_requests_gauge.dec()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No suitable drivers found for your request. Please try again later."
            )
        
        # Update metrics for successful match
        successful_matches_counter.inc()
        active_ride_requests_gauge.dec()
        available_drivers_gauge.dec()
        
        # Return simulated match details
        return {
            "ride_id": random.randint(1000, 9999),
            "driver_id": random.randint(1, 100),
            "passenger_id": request.passenger_id,
            "pickup_time": "2023-09-30T14:30:00Z",
            "estimated_arrival_time": "2023-09-30T15:15:00Z",
            "price": round(random.uniform(10.0, 50.0), 2)
        }
    except Exception as e:
        # Ensure metrics are updated even if an error occurs
        active_ride_requests_gauge.dec()
        failed_matches_counter.inc()
        raise e


@app.get("/statistics", tags=["Statistics"])
async def get_statistics():
    """Get matching service statistics."""
    success_rate = 0
    
    total_requests = match_request_counter.value
    if total_requests > 0:
        success_rate = (successful_matches_counter.value / total_requests) * 100
    
    return {
        "total_match_requests": total_requests,
        "successful_matches": successful_matches_counter.value,
        "failed_matches": failed_matches_counter.value,
        "success_rate_percentage": round(success_rate, 2),
        "active_ride_requests": active_ride_requests_gauge.value,
        "available_drivers": available_drivers_gauge.value
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)