#!/usr/bin/env python3
"""
Basic tests for matching service API endpoints
"""

import requests
import time
import json


def test_basic_matching_service():
    """Test basic matching service functionality"""
    
    base_url = 'http://matching-service:8000'
    
    print("=== Basic Matching Service Tests ===\n")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f'{base_url}/health')
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check passed: {health_data['status']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Available rides endpoint
    print("\n2. Testing available rides endpoint...")
    try:
        response = requests.get(f'{base_url}/available-rides')
        if response.status_code == 200:
            rides_data = response.json()
            ride_count = len(rides_data.get('available_rides', []))
            print(f"   ✅ Available rides endpoint working: {ride_count} rides available")
        else:
            print(f"   ❌ Available rides failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Available rides error: {e}")
    
    # Test 3: Statistics endpoint
    print("\n3. Testing statistics endpoint...")
    try:
        response = requests.get(f'{base_url}/statistics')
        if response.status_code == 200:
            stats_data = response.json()
            print(f"   ✅ Statistics endpoint working")
            print(f"      - Available rides: {stats_data.get('available_rides', 'N/A')}")
            print(f"      - Total matches: {stats_data.get('total_matches', 'N/A')}")
        else:
            print(f"   ❌ Statistics failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Statistics error: {e}")
    
    # Test 4: Match request (expecting 404 since no rides available initially)
    print("\n4. Testing match request...")
    try:
        match_request = {
            "passenger_id": 999,
            "pickup_location": {
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "dropoff_location": {
                "latitude": 40.7589,
                "longitude": -73.9851
            },
            "requested_time": "2023-12-01T14:30:00Z"
        }
        
        response = requests.post(f'{base_url}/match', json=match_request)
        if response.status_code == 404:
            print(f"   ✅ Match request handled correctly (no rides available)")
        elif response.status_code == 200:
            match_data = response.json()
            print(f"   ✅ Match found: Ride {match_data['ride_id']} with driver {match_data['driver_id']}")
        else:
            print(f"   ❌ Match request failed unexpectedly: {response.status_code}")
            print(f"       Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Match request error: {e}")
    
    print("\n=== Basic Matching Service Tests Complete ===")


if __name__ == "__main__":
    test_basic_matching_service() 