#!/usr/bin/env python3
"""
Test script to verify RabbitMQ messaging between services
"""

import requests
import time
import json


def test_messaging_flow():
    """Test the complete messaging flow between services"""
    
    base_urls = {
        'users': 'http://users-service:8000',
        'rides': 'http://rides-service:8000', 
        'matching': 'http://matching-service:8000',
        'payments': 'http://payments-service:8000'
    }
    
    print("=== Testing RabbitMQ Messaging Flow ===\n")
    
    # 1. Create a user first
    print("1. Creating a user...")
    user_data = {
        "email": f"test{int(time.time())}@example.com",
        "first_name": "Test",
        "last_name": "User", 
        "phone_number": "+1234567890",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{base_urls['users']}/users/", json=user_data)
        if response.status_code == 201:
            user = response.json()
            print(f"✅ User created: {user['id']} - {user['first_name']} {user['last_name']}")
        else:
            print(f"❌ Failed to create user: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    time.sleep(1)
    
    # 2. Create a ride (this should publish a message to matching service)
    print("\n2. Creating a ride...")
    ride_data = {
        "driver_id": user['id'],
        "origin_location": {
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        "destination_location": {
            "latitude": 40.7589,
            "longitude": -73.9851
        },
        "start_time": "2023-12-01T14:30:00",
        "max_passengers": 3,
        "price_per_seat": 15.50
    }
    
    try:
        response = requests.post(f"{base_urls['rides']}/rides/", json=ride_data)
        if response.status_code == 201:
            ride = response.json()
            print(f"✅ Ride created: {ride['id']} - Driver {ride['driver_id']}")
        else:
            print(f"❌ Failed to create ride: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating ride: {e}")
        return
    
    # Wait for message to be processed
    time.sleep(2)
    
    # 3. Check if matching service received the ride
    print("\n3. Checking if matching service received the ride...")
    try:
        response = requests.get(f"{base_urls['matching']}/available-rides")
        if response.status_code == 200:
            data = response.json()
            available_rides = data['available_rides']
            print(f"✅ Matching service has {len(available_rides)} available rides")
            
            # Find our ride
            our_ride = None
            for r in available_rides:
                if r['ride_id'] == ride['id']:
                    our_ride = r
                    break
            
            if our_ride:
                print(f"✅ Our ride {ride['id']} is available in matching service")
                print(f"   - Driver: {our_ride['driver_id']}")
                print(f"   - Max passengers: {our_ride['max_passengers']}")
                print(f"   - Current passengers: {our_ride['current_passengers']}")
            else:
                print(f"❌ Our ride {ride['id']} not found in matching service")
        else:
            print(f"❌ Failed to get available rides: {response.text}")
    except Exception as e:
        print(f"❌ Error checking available rides: {e}")
    
    # 4. Test matching
    print("\n4. Testing ride matching...")
    match_request = {
        "passenger_id": user['id'] + 1,  # Different user
        "pickup_location": {
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        "dropoff_location": {
            "latitude": 40.7589,
            "longitude": -73.9851
        },
        "requested_time": "2023-12-01T14:30:00"
    }
    
    try:
        response = requests.post(f"{base_urls['matching']}/match", json=match_request)
        if response.status_code == 200:
            match = response.json()
            print(f"✅ Match found: Ride {match['ride_id']} with driver {match['driver_id']}")
        else:
            print(f"❌ Failed to find match: {response.text}")
    except Exception as e:
        print(f"❌ Error during matching: {e}")
    
    # 5. Create a payment and test payment messaging
    print("\n5. Creating a payment...")
    payment_data = {
        "passenger_id": user['id'],
        "driver_id": ride['driver_id'], 
        "ride_id": ride['id'],
        "amount": ride['price_per_seat'],
        "payment_method": "credit_card",
        "description": "Payment for carpool ride"
    }
    
    try:
        response = requests.post(f"{base_urls['payments']}/payments/", json=payment_data)
        if response.status_code == 201:
            payment = response.json()
            print(f"✅ Payment created: {payment['id']} - Amount: ${payment['amount']}")
            
            # Complete the payment (this should send a message to users service)
            print("\n6. Completing payment...")
            update_data = {"status": "completed"}
            response = requests.put(f"{base_urls['payments']}/payments/{payment['id']}", json=update_data)
            
            if response.status_code == 200:
                print(f"✅ Payment completed successfully")
                
                # Wait for message processing
                time.sleep(2)
                
                # Check user payment stats
                print("\n7. Checking user payment statistics...")
                
                # First login to get a valid token
                login_data = {
                    "username": user_data["email"],
                    "password": user_data["password"]
                }
                
                token_response = requests.post(f"{base_urls['users']}/token", data=login_data)
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    access_token = token_data["access_token"]
                    
                    response = requests.get(f"{base_urls['users']}/users/{user['id']}/payment-stats", 
                                         headers={"Authorization": f"Bearer {access_token}"})
                else:
                    print(f"❌ Failed to get authentication token: {token_response.text}")
                    response = None
                
                if response and response.status_code == 200:
                    stats = response.json()
                    print(f"✅ User payment stats updated:")
                    print(f"   - Total spent: ${stats['payment_statistics']['total_spent']}")
                    print(f"   - Successful payments: {stats['payment_statistics']['successful_payments']}")
                elif response:
                    print(f"❌ Failed to get payment stats: {response.text}")
                else:
                    print(f"❌ Could not access payment stats due to authentication failure")
            else:
                print(f"❌ Failed to complete payment: {response.text}")
        else:
            print(f"❌ Failed to create payment: {response.text}")
    except Exception as e:
        print(f"❌ Error with payment: {e}")
    
    print("\n=== Messaging Test Complete ===")


if __name__ == "__main__":
    test_messaging_flow() 