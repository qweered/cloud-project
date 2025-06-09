import requests
import json

print('🚀 Comprehensive Service Tests')
print('=' * 50)

services = {
    'users': 'http://users-service:8000',
    'rides': 'http://rides-service:8000', 
    'matching': 'http://matching-service:8000',
    'payments': 'http://payments-service:8000'
}

# Test 1: Health checks
print('\n🩺 Health Checks:')
for name, url in services.items():
    response = requests.get(f'{url}/health')
    status = response.json().get('status') if response.status_code == 200 else 'error'
    print(f'  {name}: {status}')

# Test 2: Metrics endpoints
print('\n📊 Metrics Endpoints:')
for name, url in services.items():
    response = requests.get(f'{url}/metrics')
    has_metrics = 'http_requests_total' in response.text if response.status_code == 200 else False
    print(f'  {name}: {"available" if has_metrics else "error"}')

# Test 3: GraphQL endpoint
print('\n🔗 GraphQL Endpoint:')
graphql_query = """
query {
    __schema {
        types {
            name
        }
    }
}
"""

response = requests.post(f'{services["users"]}/graphql', json={'query': graphql_query})
if response.status_code == 200:
    data = response.json()
    if 'errors' not in data:
        types_count = len(data.get('data', {}).get('__schema', {}).get('types', []))
        print(f'  ✅ GraphQL schema loaded: {types_count} types')
    else:
        print(f'  ❌ GraphQL errors: {data["errors"]}')
else:
    print(f'  ❌ GraphQL endpoint failed: {response.status_code}')

# Test 4: GraphiQL interface
print('\n🖥️  GraphiQL Interface:')
response = requests.get(f'{services["users"]}/graphiql')
if response.status_code == 200 and 'GraphiQL' in response.text:
    print(f'  ✅ GraphiQL interface available')
else:
    print(f'  ❌ GraphiQL interface failed: {response.status_code}')

# Test 5: User creation and management
print('\n👤 User Management:')
import time
user_data = {
    'email': f'comprehensive-test-{int(time.time())}@example.com',
    'first_name': 'Comprehensive',
    'last_name': 'Test',
    'phone_number': '+1987654321',
    'password': 'securepass123',
    'role': 'driver',
    'vehicle_model': 'Tesla Model 3',
    'license_plate': 'TEST123',
    'max_passengers': 4
}

response = requests.post(f'{services["users"]}/users/', json=user_data)
if response.status_code == 201:
    user = response.json()
    print(f'  ✅ User created: ID {user["id"]}')
    
    # Test user retrieval
    response = requests.get(f'{services["users"]}/users/{user["id"]}')
    if response.status_code == 401:  # Expected due to auth
        print(f'  ✅ Authentication protection working')
    else:
        print(f'  ⚠️  Authentication might not be working properly')
else:
    print(f'  ❌ User creation failed: {response.status_code}')

# Test 6: GraphQL User Creation
print('\n👥 GraphQL User Creation:')
graphql_user_mutation = """
mutation CreateUser($userInput: UserInput!) {
    createUser(userInput: $userInput) {
        id
        email
        firstName
        lastName
        role
    }
}
"""

graphql_variables = {
    "userInput": {
        "email": f"graphql-test-{int(time.time())}@example.com",
        "firstName": "GraphQL",
        "lastName": "User",
        "phoneNumber": "+1555123456",
        "password": "graphqlpass123",
        "role": "passenger"
    }
}

response = requests.post(
    f'{services["users"]}/graphql',
    json={
        'query': graphql_user_mutation,
        'variables': graphql_variables
    }
)

if response.status_code == 200:
    data = response.json()
    if 'errors' not in data and data.get('data', {}).get('createUser'):
        user_data = data['data']['createUser']
        print(f'  ✅ GraphQL user created: ID {user_data["id"]}')
    else:
        print(f'  ❌ GraphQL user creation failed: {data.get("errors", "Unknown error")}')
else:
    print(f'  ❌ GraphQL user creation request failed: {response.status_code}')

print('\n🚗 Ride Creation Test:')
ride_data = {
    'driver_id': 1,
    'origin_location': {'latitude': 40.7128, 'longitude': -74.0060},
    'destination_location': {'latitude': 40.7580, 'longitude': -73.9855},
    'start_time': '2023-12-01T15:00:00Z',
    'max_passengers': 3,
    'price_per_seat': 25.0
}

response = requests.post(f'{services["rides"]}/rides/', json=ride_data)
if response.status_code == 201:
    ride = response.json()
    print(f'  ✅ Ride created: ID {ride["id"]}')
else:
    print(f'  ❌ Ride creation failed: {response.status_code}')

print('\n🔍 Matching Service Test:')
match_data = {
    'passenger_id': 1,
    'pickup_location': {'latitude': 40.7128, 'longitude': -74.0060},
    'dropoff_location': {'latitude': 40.7580, 'longitude': -73.9855},
    'requested_time': '2023-12-01T15:00:00Z'
}

response = requests.post(f'{services["matching"]}/match', json=match_data)
if response.status_code in [200, 404]:  # 404 is expected for no matches
    if response.status_code == 200:
        match = response.json()
        print(f'  ✅ Match found: Ride {match["ride_id"]}')
    else:
        print(f'  ✅ Matching service working (no match found)')
else:
    print(f'  ❌ Matching failed: {response.status_code}')

print('\n💳 Payment Creation Test:')
payment_data = {
    'ride_id': 1,
    'passenger_id': 1,
    'driver_id': 1,
    'amount': 25.50,
    'payment_method': 'credit_card'
}

response = requests.post(f'{services["payments"]}/payments/', json=payment_data)
if response.status_code == 201:
    payment = response.json()
    print(f'  ✅ Payment created: ID {payment["id"]}')
else:
    print(f'  ❌ Payment creation failed: {response.status_code}')

# Test 7: GraphQL aggregated query
print('\n📈 GraphQL Aggregated Query:')
graphql_rides_query = """
query GetRides {
    rides {
        id
        status
        originLocation {
            latitude
            longitude
        }
        destinationLocation {
            latitude
            longitude
        }
        maxPassengers
        pricePerSeat
    }
}
"""

response = requests.post(f'{services["users"]}/graphql', json={'query': graphql_rides_query})
if response.status_code == 200:
    data = response.json()
    if 'errors' not in data:
        rides = data.get('data', {}).get('rides', [])
        print(f'  ✅ GraphQL rides query successful: {len(rides)} rides returned')
    else:
        print(f'  ❌ GraphQL rides query failed: {data["errors"]}')
else:
    print(f'  ❌ GraphQL rides query failed: {response.status_code}')

print('\n' + '=' * 50)
print('✅ Comprehensive tests completed!') 