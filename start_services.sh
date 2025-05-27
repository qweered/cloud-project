#!/bin/bash

# Script to start all services in development mode

echo "Starting Carpooling Services..."

# Start services in the background
echo "Starting Users Service..."
cd services/users && python main.py &
USERS_PID=$!

echo "Starting Rides Service..."
cd ../rides && python main.py &
RIDES_PID=$!

echo "Starting Matching Service..."
cd ../matching && python main.py &
MATCHING_PID=$!

echo "Starting Payments Service..."
cd ../payments && python main.py &
PAYMENTS_PID=$!

cd ../..

echo "All services started!"
echo "Users Service:     http://localhost:8000"
echo "Rides Service:     http://localhost:8000"
echo "Matching Service:  http://localhost:8000"
echo "Payments Service:  http://localhost:8000"
echo ""
echo "Metrics endpoints:"
echo "Users Service:     http://localhost:8000/metrics"
echo "Rides Service:     http://localhost:8000/metrics"
echo "Matching Service:  http://localhost:8000/metrics"
echo "Payments Service:  http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C and kill all background processes
trap "kill $USERS_PID $RIDES_PID $MATCHING_PID $PAYMENTS_PID; exit" INT

# Wait for all background processes
wait 