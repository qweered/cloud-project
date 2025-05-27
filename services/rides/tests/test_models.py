"""
Unit tests for ride models
"""

import unittest
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.models import (
    RideStatus, PassengerStatus, Location,
    RideCreate, RideResponse, RideUpdate
)


class TestRideModels(unittest.TestCase):
    """Test suite for ride model functionality."""
    
    def test_location_model(self):
        """Test location model initialization."""
        location = Location(latitude=52.5200, longitude=13.4050)
        self.assertEqual(location.latitude, 52.5200)
        self.assertEqual(location.longitude, 13.4050)
    
    def test_ride_status_enum(self):
        """Test ride status enum values."""
        self.assertEqual(RideStatus.SCHEDULED, "scheduled")
        self.assertEqual(RideStatus.IN_PROGRESS, "in_progress")
        self.assertEqual(RideStatus.COMPLETED, "completed")
        self.assertEqual(RideStatus.CANCELLED, "cancelled")
    
    def test_passenger_status_enum(self):
        """Test passenger status enum values."""
        self.assertEqual(PassengerStatus.REQUESTED, "requested")
        self.assertEqual(PassengerStatus.ACCEPTED, "accepted")
        self.assertEqual(PassengerStatus.REJECTED, "rejected")
        self.assertEqual(PassengerStatus.CANCELLED, "cancelled")
        self.assertEqual(PassengerStatus.COMPLETED, "completed")
    
    def test_ride_create_model(self):
        """Test ride create model."""
        start_time = datetime.now()
        origin = Location(latitude=52.5200, longitude=13.4050)
        destination = Location(latitude=53.5511, longitude=9.9937)
        
        ride = RideCreate(
            driver_id=1,
            origin_location=origin,
            destination_location=destination,
            start_time=start_time,
            max_passengers=3,
            price_per_seat=15.50
        )
        
        self.assertEqual(ride.driver_id, 1)
        self.assertEqual(ride.origin_location, origin)
        self.assertEqual(ride.destination_location, destination)
        self.assertEqual(ride.start_time, start_time)
        self.assertEqual(ride.max_passengers, 3)
        self.assertEqual(ride.price_per_seat, 15.50)
    
    def test_ride_update_model(self):
        """Test ride update model."""
        update = RideUpdate(status=RideStatus.COMPLETED, current_passengers=2)
        
        self.assertEqual(update.status, RideStatus.COMPLETED)
        self.assertEqual(update.current_passengers, 2)
        self.assertIsNone(update.end_time)
        
        # Test optional fields
        empty_update = RideUpdate()
        self.assertIsNone(empty_update.status)
        self.assertIsNone(empty_update.current_passengers)
        self.assertIsNone(empty_update.end_time)


if __name__ == "__main__":
    unittest.main() 