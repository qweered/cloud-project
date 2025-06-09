"""
Matching Service - Main entry point
"""

import sys
import os
import time
import random
import logging
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn
import requests

from common.base_service import BaseService
from common.metrics import timing_metric
from common.messaging import MessageBroker, EXCHANGES, ROUTING_KEYS, QUEUES


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

# Mock database for available rides
available_rides = {}

# Initialize message broker
message_broker = MessageBroker()
message_broker.declare_exchange(EXCHANGES['RIDES'])
message_broker.declare_queue(QUEUES['MATCHING_RIDES'])
message_broker.bind_queue(QUEUES['MATCHING_RIDES'], EXCHANGES['RIDES'], ROUTING_KEYS['RIDE_CREATED'])
message_broker.bind_queue(QUEUES['MATCHING_RIDES'], EXCHANGES['RIDES'], ROUTING_KEYS['RIDE_UPDATED'])
message_broker.bind_queue(QUEUES['MATCHING_RIDES'], EXCHANGES['RIDES'], ROUTING_KEYS['PASSENGER_JOINED'])

# Message handlers
def handle_ride_messages(message: Dict):
    """Handle incoming ride messages"""
    try:
        event_type = message.get('event_type')
        
        if event_type == 'ride_created':
            # Add new ride to available rides
            ride_id = message['ride_id']
            available_rides[ride_id] = {
                'ride_id': ride_id,
                'driver_id': message['driver_id'],
                'pickup_location': message['pickup_location'],
                'dropoff_location': message['dropoff_location'],
                'departure_time': message['departure_time'],
                'max_passengers': message['max_passengers'],
                'current_passengers': message['current_passengers'],
                'status': 'scheduled'
            }
            available_drivers_gauge.inc()
            logging.info(f"Added new ride {ride_id} to matching service")
            
        elif event_type == 'ride_updated':
            # Update ride status
            ride_id = message['ride_id']
            if ride_id in available_rides:
                available_rides[ride_id]['status'] = message['status']
                available_rides[ride_id]['current_passengers'] = message['current_passengers']
                
                # Remove from available rides if completed or cancelled
                if message['status'] in ['completed', 'cancelled']:
                    del available_rides[ride_id]
                    available_drivers_gauge.dec()
                    
                logging.info(f"Updated ride {ride_id} status to {message['status']}")
                
        elif event_type == 'passenger_joined':
            # Update passenger count
            ride_id = message['ride_id']
            if ride_id in available_rides:
                available_rides[ride_id]['current_passengers'] += 1
                logging.info(f"Passenger {message['passenger_id']} joined ride {ride_id}")
                
        return True  # Message processed successfully
        
    except Exception as e:
        logging.error(f"Error processing ride message: {e}")
        return False  # Requeue message

# Setup message consumer
message_broker.add_consumer(QUEUES['MATCHING_RIDES'], handle_ride_messages)
message_broker.start_consuming()

# Setup cleanup for message broker
@app.on_event("shutdown")
async def shutdown_event():
    message_broker.close()

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
        
        # Find available rides with capacity
        suitable_rides = []
        for ride_id, ride in available_rides.items():
            if (ride['status'] == 'scheduled' and 
                ride['current_passengers'] < ride['max_passengers']):
                suitable_rides.append(ride)
        
        if not suitable_rides:
            failed_matches_counter.inc()
            active_ride_requests_gauge.dec()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No suitable drivers found for your request. Available rides: {len(available_rides)}"
            )
        
        # Select best ride (for now, just pick the first one)
        # In a real implementation, this would use distance, timing, preferences, etc.
        selected_ride = suitable_rides[0]
        
        # Update metrics for successful match
        successful_matches_counter.inc()
        active_ride_requests_gauge.dec()
        
        # Return match details based on actual ride
        return {
            "ride_id": selected_ride['ride_id'],
            "driver_id": selected_ride['driver_id'],
            "passenger_id": request.passenger_id,
            "pickup_time": selected_ride['departure_time'],
            "estimated_arrival_time": "2023-09-30T15:15:00Z",  # Would be calculated
            "price": round(random.uniform(10.0, 50.0), 2)  # Would be calculated based on distance
        }
    except Exception as e:
        # Ensure metrics are updated even if an error occurs
        active_ride_requests_gauge.dec()
        failed_matches_counter.inc()
        raise e


@app.get("/available-rides", tags=["Matching"])
async def get_available_rides():
    """Get all rides available for matching."""
    return {
        "available_rides": list(available_rides.values()),
        "count": len(available_rides)
    }


@app.get("/statistics", tags=["Statistics"])
async def get_statistics():
    """Get matching service statistics."""
    success_rate = 0
    
    # Get metric values using the correct prometheus_client API
    total_requests = match_request_counter._value._value
    successful_matches = successful_matches_counter._value._value
    failed_matches = failed_matches_counter._value._value
    active_requests = active_ride_requests_gauge._value._value
    available_drivers = available_drivers_gauge._value._value
    
    if total_requests > 0:
        success_rate = (successful_matches / total_requests) * 100
    
    return {
        "total_match_requests": int(total_requests),
        "successful_matches": int(successful_matches),
        "failed_matches": int(failed_matches),
        "success_rate_percentage": round(success_rate, 2),
        "active_ride_requests": int(active_requests),
        "available_drivers": int(available_drivers),
        "available_rides_count": len(available_rides)
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)