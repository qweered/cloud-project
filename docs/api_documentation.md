# API Documentation - Carpooling Microservices Platform

## 🌐 Live Production APIs

All services are currently deployed and accessible on Azure Container Instances:

**Base URLs**: `http://carpool-{service}-{build}.eastus.azurecontainer.io:8000`

- **Users Service**: `http://carpool-users-{build}.eastus.azurecontainer.io:8000`
- **Rides Service**: `http://carpool-rides-{build}.eastus.azurecontainer.io:8000`
- **Matching Service**: `http://carpool-matching-{build}.eastus.azurecontainer.io:8000`
- **Payments Service**: `http://carpool-payments-{build}.eastus.azurecontainer.io:8000`

## 📚 Interactive Documentation

Each service provides auto-generated OpenAPI/Swagger documentation:

- **Users API Docs**: `http://carpool-users-{build}.eastus.azurecontainer.io:8000/docs`
- **Rides API Docs**: `http://carpool-rides-{build}.eastus.azurecontainer.io:8000/docs`
- **Matching API Docs**: `http://carpool-matching-{build}.eastus.azurecontainer.io:8000/docs`
- **Payments API Docs**: `http://carpool-payments-{build}.eastus.azurecontainer.io:8000/docs`

## 🏥 Health Monitoring

All services expose standardized health endpoints:

```bash
# Health check endpoints
GET /health         # Service health status
GET /info          # Service version and build info
GET /metrics       # Prometheus-compatible metrics
```

**Example Health Check**:
```bash
curl http://carpool-users-{build}.eastus.azurecontainer.io:8000/health

# Response:
{
  "status": "healthy",
  "service": "users-service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "dependencies": {
    "postgresql": "healthy",
    "rabbitmq": "healthy"
  }
}
```

## 👥 Users Service API

### Database Schema
```sql
-- users_db.users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Endpoints

#### **POST /users**
Create a new user account.

```bash
curl -X POST http://carpool-users-{build}.eastus.azurecontainer.io:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "name": "John Doe",
    "phone": "+1-555-0123"
  }'
```

**Response**:
```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "name": "John Doe",
  "phone": "+1-555-0123",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### **GET /users/{user_id}**
Retrieve user profile by ID.

```bash
curl http://carpool-users-{build}.eastus.azurecontainer.io:8000/users/1
```

#### **PUT /users/{user_id}**
Update user profile.

```bash
curl -X PUT http://carpool-users-{build}.eastus.azurecontainer.io:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "phone": "+1-555-9999"
  }'
```

#### **GET /users**
List all users (with pagination).

```bash
curl "http://carpool-users-{build}.eastus.azurecontainer.io:8000/users?page=1&limit=10"
```

## 🚗 Rides Service API

### Database Schema
```sql
-- rides_db.rides table
CREATE TABLE rides (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL,
    origin VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    available_seats INTEGER DEFAULT 1,
    price DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- rides_db.bookings table
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    ride_id INTEGER REFERENCES rides(id),
    passenger_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Endpoints

#### **POST /rides**
Create a new ride offer.

```bash
curl -X POST http://carpool-rides-{build}.eastus.azurecontainer.io:8000/rides \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": 1,
    "origin": "San Francisco, CA",
    "destination": "Los Angeles, CA",
    "departure_time": "2024-01-20T08:00:00Z",
    "available_seats": 3,
    "price": 45.00
  }'
```

**Response**:
```json
{
  "id": 1,
  "driver_id": 1,
  "origin": "San Francisco, CA",
  "destination": "Los Angeles, CA",
  "departure_time": "2024-01-20T08:00:00Z",
  "available_seats": 3,
  "price": 45.00,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### **GET /rides**
Search for available rides.

```bash
curl "http://carpool-rides-{build}.eastus.azurecontainer.io:8000/rides?origin=San%20Francisco&destination=Los%20Angeles&date=2024-01-20"
```

#### **GET /rides/{ride_id}**
Get specific ride details.

```bash
curl http://carpool-rides-{build}.eastus.azurecontainer.io:8000/rides/1
```

#### **POST /rides/{ride_id}/book**
Book a seat on a ride.

```bash
curl -X POST http://carpool-rides-{build}.eastus.azurecontainer.io:8000/rides/1/book \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_id": 2
  }'
```

#### **PUT /rides/{ride_id}**
Update ride details (driver only).

```bash
curl -X PUT http://carpool-rides-{build}.eastus.azurecontainer.io:8000/rides/1 \
  -H "Content-Type: application/json" \
  -d '{
    "available_seats": 2,
    "price": 50.00
  }'
```

## 🎯 Matching Service API

### Service Communication
The Matching Service communicates with:
- **Users Service**: To get user preferences and profiles
- **Rides Service**: To find available rides and update bookings
- **RabbitMQ**: To publish matching events

### Environment Variables
```bash
USERS_SERVICE_URL=http://carpool-users-{build}.eastus.azurecontainer.io:8000
RIDES_SERVICE_URL=http://carpool-rides-{build}.eastus.azurecontainer.io:8000
RABBITMQ_HOST=rabbitmq.containerinstances.io
```

### Endpoints

#### **POST /match**
Find matching rides for a passenger.

```bash
curl -X POST http://carpool-matching-{build}.eastus.azurecontainer.io:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_id": 2,
    "origin": "San Francisco, CA",
    "destination": "Los Angeles, CA",
    "departure_time": "2024-01-20T08:00:00Z",
    "max_price": 50.00
  }'
```

**Response**:
```json
{
  "matches": [
    {
      "ride_id": 1,
      "driver_id": 1,
      "origin": "San Francisco, CA",
      "destination": "Los Angeles, CA",
      "departure_time": "2024-01-20T08:00:00Z",
      "price": 45.00,
      "available_seats": 3,
      "match_score": 0.95,
      "distance_km": 2.1
    }
  ],
  "total_matches": 1
}
```

#### **POST /match/confirm**
Confirm a match and book the ride.

```bash
curl -X POST http://carpool-matching-{build}.eastus.azurecontainer.io:8000/match/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_id": 2,
    "ride_id": 1
  }'
```

#### **GET /match/history/{user_id}**
Get matching history for a user.

```bash
curl http://carpool-matching-{build}.eastus.azurecontainer.io:8000/match/history/2
```

## 💳 Payments Service API

### Database Schema
```sql
-- payments_db.payments table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    passenger_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Endpoints

#### **POST /payments**
Process a payment for a ride.

```bash
curl -X POST http://carpool-payments-{build}.eastus.azurecontainer.io:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "ride_id": 1,
    "passenger_id": 2,
    "driver_id": 1,
    "amount": 45.00,
    "payment_method": "credit_card"
  }'
```

**Response**:
```json
{
  "id": 1,
  "ride_id": 1,
  "passenger_id": 2,
  "driver_id": 1,
  "amount": 45.00,
  "status": "completed",
  "payment_method": "credit_card",
  "transaction_id": "txn_1234567890",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:05Z"
}
```

#### **GET /payments/{payment_id}**
Get payment details.

```bash
curl http://carpool-payments-{build}.eastus.azurecontainer.io:8000/payments/1
```

#### **GET /payments/user/{user_id}**
Get payment history for a user.

```bash
curl http://carpool-payments-{build}.eastus.azurecontainer.io:8000/payments/user/2
```

#### **POST /payments/{payment_id}/refund**
Process a refund.

```bash
curl -X POST http://carpool-payments-{build}.eastus.azurecontainer.io:8000/payments/1/refund \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "ride_cancelled",
    "amount": 45.00
  }'
```

## 🐰 RabbitMQ Message Broker

### Management Interface
- **URL**: `http://carpool-rabbitmq-{build}.eastus.azurecontainer.io:15672`
- **Credentials**: admin / admin123

### Message Queues

#### **Ride Events Queue**
```json
{
  "event_type": "ride_created",
  "ride_id": 1,
  "driver_id": 1,
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "origin": "San Francisco, CA",
    "destination": "Los Angeles, CA",
    "departure_time": "2024-01-20T08:00:00Z"
  }
}
```

#### **Match Events Queue**
```json
{
  "event_type": "match_found",
  "passenger_id": 2,
  "ride_id": 1,
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "match_score": 0.95
  }
}
```

#### **Payment Events Queue**
```json
{
  "event_type": "payment_completed",
  "payment_id": 1,
  "ride_id": 1,
  "timestamp": "2024-01-15T10:40:00Z",
  "data": {
    "amount": 45.00,
    "status": "completed"
  }
}
```

## 🔄 Service Interaction Flow

### Complete Carpooling Flow

1. **User Registration**
   ```bash
   POST /users → Users Service → Database
   ```

2. **Ride Creation**
   ```bash
   POST /rides → Rides Service → Database → RabbitMQ Event
   ```

3. **Match Request**
   ```bash
   POST /match → Matching Service → Users/Rides Services → Match Results
   ```

4. **Booking Confirmation**
   ```bash
   POST /match/confirm → Matching Service → Rides Service → RabbitMQ Event
   ```

5. **Payment Processing**
   ```bash
   POST /payments → Payments Service → Database → RabbitMQ Event
   ```

## 🧪 Testing the APIs

### Health Check Script
```bash
#!/bin/bash
# health-check.sh

SERVICES=("users" "rides" "matching" "payments")
BUILD_NUMBER="your-build-number"  # Replace with actual build number

for service in "${SERVICES[@]}"; do
  echo "Checking $service service..."
  response=$(curl -s -w "%{http_code}" "http://carpool-$service-$BUILD_NUMBER.eastus.azurecontainer.io:8000/health")
  
  if [[ "${response: -3}" == "200" ]]; then
    echo "✅ $service service is healthy"
  else
    echo "❌ $service service is unhealthy (HTTP ${response: -3})"
  fi
done
```

### API Testing Script
```bash
#!/bin/bash
# api-test.sh

BUILD_NUMBER="your-build-number"  # Replace with actual build number
BASE_URL="http://carpool-users-$BUILD_NUMBER.eastus.azurecontainer.io:8000"

# Test user creation
echo "Creating test user..."
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "phone": "+1-555-0123"
  }')

echo "User created: $USER_RESPONSE"

# Extract user ID for further testing
USER_ID=$(echo "$USER_RESPONSE" | jq -r '.id')
echo "User ID: $USER_ID"
```

## 📊 Monitoring & Metrics

### Custom Metrics Available
Each service exposes Prometheus-compatible metrics at `/metrics`:

```bash
# Example metrics
carpool_users_registered_total
carpool_rides_created_total
carpool_matches_successful_total
carpool_payments_processed_total
carpool_api_request_duration_seconds
carpool_database_connections_active
```

### Monitoring Endpoints
```bash
# Service-specific monitoring
GET /health        # Overall service health
GET /metrics       # Prometheus metrics
GET /info          # Service version and build info

# Database connection status included in /health response
```

## 🚀 Local Development

For local development, all services are also available via docker-compose:

```bash
# Start all services locally
docker-compose up

# Local service URLs:
# Users: http://localhost:8001
# Rides: http://localhost:8002
# Matching: http://localhost:8003
# Payments: http://localhost:8004
# RabbitMQ: http://localhost:15672
```

The APIs maintain full compatibility between local development and Azure production environments.

## 📞 Support

For API questions or issues:
- Check service logs in Azure Container Instances
- Use the interactive `/docs` endpoints for API exploration
- Monitor RabbitMQ queues for message flow debugging
- Verify database connectivity via `/health` endpoints

All services are designed with comprehensive error handling and logging for easy debugging and maintenance. 