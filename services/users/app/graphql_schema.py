"""
GraphQL Schema for Carpool System
Aggregates data from all microservices
"""

import strawberry
from typing import List, Optional
import httpx
import asyncio
from datetime import datetime
from decimal import Decimal

from fastapi import Depends
from .auth import get_current_user


# GraphQL Types
@strawberry.type
class Location:
    latitude: float
    longitude: float


@strawberry.type
class User:
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: str
    role: str
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None
    max_passengers: Optional[int] = None


@strawberry.type
class Ride:
    id: int
    driver_id: int
    status: str
    origin_location: Location
    destination_location: Location
    start_time: datetime
    end_time: Optional[datetime] = None
    max_passengers: int
    current_passengers: int
    price_per_seat: float
    driver: Optional[User] = None


@strawberry.type
class Payment:
    id: int
    ride_id: int
    passenger_id: int
    driver_id: int
    amount: float
    status: str
    payment_method: str
    transaction_id: str
    created_at: datetime


@strawberry.type
class RideMatch:
    ride_id: int
    passenger_id: int
    pickup_location: Location
    dropoff_location: Location
    estimated_pickup_time: datetime
    confidence_score: float


@strawberry.type
class UserStats:
    user_id: int
    total_rides_as_driver: int
    total_rides_as_passenger: int
    total_earnings: float
    total_spent: float
    average_rating: float


# Input Types
@strawberry.input
class LocationInput:
    latitude: float
    longitude: float


@strawberry.input
class UserInput:
    email: str
    first_name: str
    last_name: str
    phone_number: str
    password: str
    role: str
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None
    max_passengers: Optional[int] = None


@strawberry.input
class RideInput:
    driver_id: int
    origin_location: LocationInput
    destination_location: LocationInput
    start_time: datetime
    max_passengers: int
    price_per_seat: float


@strawberry.input
class MatchInput:
    passenger_id: int
    pickup_location: LocationInput
    dropoff_location: LocationInput
    requested_time: datetime


# Service URLs
SERVICES = {
    'users': 'http://users-service:8000',
    'rides': 'http://rides-service:8000',
    'matching': 'http://matching-service:8000',
    'payments': 'http://payments-service:8000'
}


# Helper functions for service communication
async def fetch_from_service(service_name: str, endpoint: str, headers: dict = None):
    """Fetch data from a microservice"""
    async with httpx.AsyncClient() as client:
        try:
            url = f"{SERVICES[service_name]}{endpoint}"
            response = await client.get(url, headers=headers or {})
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None


async def post_to_service(service_name: str, endpoint: str, data: dict, headers: dict = None):
    """Post data to a microservice"""
    async with httpx.AsyncClient() as client:
        try:
            url = f"{SERVICES[service_name]}{endpoint}"
            response = await client.post(url, json=data, headers=headers or {})
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except Exception:
            return None


# GraphQL Resolvers
@strawberry.type
class Query:
    
    @strawberry.field
    async def users(self, info) -> List[User]:
        """Get all users (admin only)"""
        # In real implementation, check admin permissions
        data = await fetch_from_service('users', '/users/')
        if data:
            return [User(**user) for user in data]
        return []
    
    @strawberry.field
    async def user(self, info, user_id: int) -> Optional[User]:
        """Get user by ID"""
        data = await fetch_from_service('users', f'/users/{user_id}')
        if data:
            return User(**data)
        return None
    
    @strawberry.field
    async def rides(self, info, status: Optional[str] = None) -> List[Ride]:
        """Get rides with optional status filter"""
        endpoint = '/rides/' if not status else f'/rides/?status={status}'
        data = await fetch_from_service('rides', endpoint)
        if data:
            rides = []
            for ride_data in data:
                # Convert location data
                origin = Location(**ride_data['origin_location'])
                destination = Location(**ride_data['destination_location'])
                
                ride = Ride(
                    id=ride_data['id'],
                    driver_id=ride_data['driver_id'],
                    status=ride_data['status'],
                    origin_location=origin,
                    destination_location=destination,
                    start_time=datetime.fromisoformat(ride_data['start_time'].replace('Z', '+00:00')),
                    end_time=datetime.fromisoformat(ride_data['end_time'].replace('Z', '+00:00')) if ride_data.get('end_time') else None,
                    max_passengers=ride_data['max_passengers'],
                    current_passengers=ride_data['current_passengers'],
                    price_per_seat=ride_data['price_per_seat']
                )
                rides.append(ride)
            return rides
        return []
    
    @strawberry.field
    async def ride(self, info, ride_id: int) -> Optional[Ride]:
        """Get ride by ID"""
        data = await fetch_from_service('rides', f'/rides/{ride_id}')
        if data:
            origin = Location(**data['origin_location'])
            destination = Location(**data['destination_location'])
            
            return Ride(
                id=data['id'],
                driver_id=data['driver_id'],
                status=data['status'],
                origin_location=origin,
                destination_location=destination,
                start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')) if data.get('end_time') else None,
                max_passengers=data['max_passengers'],
                current_passengers=data['current_passengers'],
                price_per_seat=data['price_per_seat']
            )
        return None
    
    @strawberry.field
    async def payments(self, info, user_id: Optional[int] = None) -> List[Payment]:
        """Get payments, optionally filtered by user"""
        endpoint = '/payments/' if not user_id else f'/payments/?user_id={user_id}'
        data = await fetch_from_service('payments', endpoint)
        if data:
            return [
                Payment(
                    id=payment['id'],
                    ride_id=payment['ride_id'],
                    passenger_id=payment['passenger_id'],
                    driver_id=payment['driver_id'],
                    amount=payment['amount'],
                    status=payment['status'],
                    payment_method=payment['payment_method'],
                    transaction_id=payment['transaction_id'],
                    created_at=datetime.fromisoformat(payment['created_at'].replace('Z', '+00:00'))
                )
                for payment in data
            ]
        return []
    
    @strawberry.field
    async def find_matches(self, info, match_input: MatchInput) -> List[RideMatch]:
        """Find ride matches for a passenger"""
        data = await post_to_service('matching', '/match', {
            'passenger_id': match_input.passenger_id,
            'pickup_location': {
                'latitude': match_input.pickup_location.latitude,
                'longitude': match_input.pickup_location.longitude
            },
            'dropoff_location': {
                'latitude': match_input.dropoff_location.latitude,
                'longitude': match_input.dropoff_location.longitude
            },
            'requested_time': match_input.requested_time.isoformat()
        })
        
        if data and 'matches' in data:
            return [
                RideMatch(
                    ride_id=match['ride_id'],
                    passenger_id=match['passenger_id'],
                    pickup_location=Location(**match['pickup_location']),
                    dropoff_location=Location(**match['dropoff_location']),
                    estimated_pickup_time=datetime.fromisoformat(match['estimated_pickup_time'].replace('Z', '+00:00')),
                    confidence_score=match['confidence_score']
                )
                for match in data['matches']
            ]
        return []
    
    @strawberry.field
    async def user_stats(self, info, user_id: int) -> Optional[UserStats]:
        """Get comprehensive user statistics"""
        # Aggregate data from multiple services
        tasks = [
            fetch_from_service('rides', f'/rides/?driver_id={user_id}'),
            fetch_from_service('rides', f'/rides/?passenger_id={user_id}'),
            fetch_from_service('payments', f'/payments/?user_id={user_id}')
        ]
        
        driver_rides, passenger_rides, payments = await asyncio.gather(*tasks)
        
        total_rides_as_driver = len(driver_rides) if driver_rides else 0
        total_rides_as_passenger = len(passenger_rides) if passenger_rides else 0
        
        total_earnings = 0.0
        total_spent = 0.0
        
        if payments:
            for payment in payments:
                if payment['driver_id'] == user_id:
                    total_earnings += payment['amount']
                elif payment['passenger_id'] == user_id:
                    total_spent += payment['amount']
        
        return UserStats(
            user_id=user_id,
            total_rides_as_driver=total_rides_as_driver,
            total_rides_as_passenger=total_rides_as_passenger,
            total_earnings=total_earnings,
            total_spent=total_spent,
            average_rating=4.5  # Placeholder - would come from ratings service
        )


@strawberry.type
class Mutation:
    
    @strawberry.mutation
    async def create_user(self, info, user_input: UserInput) -> Optional[User]:
        """Create a new user"""
        data = await post_to_service('users', '/users/', {
            'email': user_input.email,
            'first_name': user_input.first_name,
            'last_name': user_input.last_name,
            'phone_number': user_input.phone_number,
            'password': user_input.password,
            'role': user_input.role,
            'vehicle_model': user_input.vehicle_model,
            'license_plate': user_input.license_plate,
            'max_passengers': user_input.max_passengers
        })
        
        if data:
            return User(**data)
        return None
    
    @strawberry.mutation
    async def create_ride(self, info, ride_input: RideInput) -> Optional[Ride]:
        """Create a new ride"""
        data = await post_to_service('rides', '/rides/', {
            'driver_id': ride_input.driver_id,
            'origin_location': {
                'latitude': ride_input.origin_location.latitude,
                'longitude': ride_input.origin_location.longitude
            },
            'destination_location': {
                'latitude': ride_input.destination_location.latitude,
                'longitude': ride_input.destination_location.longitude
            },
            'start_time': ride_input.start_time.isoformat(),
            'max_passengers': ride_input.max_passengers,
            'price_per_seat': ride_input.price_per_seat
        })
        
        if data:
            origin = Location(**data['origin_location'])
            destination = Location(**data['destination_location'])
            
            return Ride(
                id=data['id'],
                driver_id=data['driver_id'],
                status=data['status'],
                origin_location=origin,
                destination_location=destination,
                start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')) if data.get('end_time') else None,
                max_passengers=data['max_passengers'],
                current_passengers=data['current_passengers'],
                price_per_seat=data['price_per_seat']
            )
        return None


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation) 