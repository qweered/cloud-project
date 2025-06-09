#!/bin/bash

# Comprehensive Test Runner for Cloud Project
# Runs all tests for all services inside Docker containers

set -e  # Exit on any error

echo "🧪 Cloud Project - Comprehensive Test Suite"
echo "============================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
declare -a test_results=()
total_tests=0
passed_tests=0
failed_tests=0

# Function to run a test and track results
run_test() {
    local service=$1
    local test_file=$2
    local test_name=$3
    local test_type=$4
    
    echo -e "\n${BLUE}🔍 Running ${test_type}: ${test_name}${NC}"
    echo "   Service: ${service}"
    echo "   File: ${test_file}"
    echo "   " $(date)
    
    total_tests=$((total_tests + 1))
    
    if docker compose exec -T ${service} python ${test_file} > /tmp/test_output_${service}_$(basename ${test_file} .py) 2>&1; then
        echo -e "   ${GREEN}✅ PASSED${NC}"
        test_results+=("${service}:${test_name}:PASSED")
        passed_tests=$((passed_tests + 1))
        
        # Show key output for integration tests
        if [[ "$test_type" == "Integration Test" ]]; then
            echo "   Key Results:"
            grep -E "(✅|❌|Health|created|completed|available)" /tmp/test_output_${service}_$(basename ${test_file} .py) | head -10 | sed 's/^/     /'
        fi
    else
        echo -e "   ${RED}❌ FAILED${NC}"
        test_results+=("${service}:${test_name}:FAILED")
        failed_tests=$((failed_tests + 1))
        
        echo "   Error Output:"
        echo "   Last 20 lines of test output:"
        tail -20 /tmp/test_output_${service}_$(basename ${test_file} .py) | sed 's/^/     /'
        echo "   Full test output saved to: /tmp/test_output_${service}_$(basename ${test_file} .py)"
    fi
}

# Function to run unit tests with unittest
run_unit_test() {
    local service=$1
    local test_module=$2
    local test_name=$3
    
    echo -e "\n${BLUE}🔍 Running Unit Test: ${test_name}${NC}"
    echo "   Service: ${service}"
    echo "   Module: ${test_module}"
    echo "   " $(date)
    
    total_tests=$((total_tests + 1))
    
    if docker compose exec -T ${service} python -m unittest ${test_module} > /tmp/test_output_${service}_$(echo ${test_module} | tr '.' '_') 2>&1; then
        echo -e "   ${GREEN}✅ PASSED${NC}"
        test_results+=("${service}:${test_name}:PASSED")
        passed_tests=$((passed_tests + 1))
        
        # Show test count - look for "Ran X tests" line
        test_count=$(grep "Ran [0-9]* test" /tmp/test_output_${service}_$(echo ${test_module} | tr '.' '_') 2>/dev/null | grep -o '[0-9]*' | head -1 || echo "0")
        echo "   Unit Tests Run: ${test_count}"
    else
        echo -e "   ${RED}❌ FAILED${NC}"
        test_results+=("${service}:${test_name}:FAILED")
        failed_tests=$((failed_tests + 1))
        
        echo "   Error Output:"
        echo "   Last 20 lines of test output:"
        tail -20 /tmp/test_output_${service}_$(echo ${test_module} | tr '.' '_') | sed 's/^/     /'
        echo "   Full test output saved to: /tmp/test_output_${service}_$(echo ${test_module} | tr '.' '_')"
    fi
}

# Ensure Docker services are running
echo -e "\n${YELLOW}🚀 Starting Docker services...${NC}"
docker compose up -d

# Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 15

# Give additional time for database connections and message broker setup
echo -e "   Ensuring database connections are established..."
sleep 5

# Health check all services
echo -e "\n${YELLOW}🩺 Performing health checks...${NC}"
services=("users-service:8000" "rides-service:8000" "matching-service:8000" "payments-service:8000")
all_healthy=true

for service_port in "${services[@]}"; do
    service_name=$(echo $service_port | cut -d':' -f1)
    port=$(echo $service_port | cut -d':' -f2)
    
    # Try health check with retries (up to 3 attempts)
    health_check_passed=false
    for attempt in {1..3}; do
        if docker compose exec -T ${service_name} python -c "
try:
    import requests
    requests.get('http://localhost:${port}/health').raise_for_status()
except ImportError:
    import httpx
    httpx.get('http://localhost:${port}/health').raise_for_status()
" >/dev/null 2>&1; then
            health_check_passed=true
            break
        else
            if [ $attempt -lt 3 ]; then
                sleep 2  # Wait 2 seconds before retry
            fi
        fi
    done
    
    if [ "$health_check_passed" = true ]; then
        echo -e "   ${GREEN}✅ ${service_name} is healthy${NC}"
    else
        echo -e "   ${RED}❌ ${service_name} is not healthy${NC}"
        all_healthy=false
    fi
done

if [ "$all_healthy" = false ]; then
    echo -e "\n${RED}⚠️  Some services are not healthy. Continuing with tests anyway...${NC}"
fi

# Clear any previous test data for clean test runs
echo -e "\n${YELLOW}🧹 Preparing clean test environment...${NC}"
echo -e "   Restarting services to ensure clean state..."
docker compose restart users-service rides-service matching-service payments-service >/dev/null 2>&1
sleep 5

# Run all tests
echo -e "\n${YELLOW}🧪 Running Test Suite...${NC}"

# 1. Users Service Tests
echo -e "\n${BLUE}👤 USERS SERVICE TESTS${NC}"
run_test "users-service" "tests/comprehensive_test.py" "Comprehensive Service Tests" "Integration Test"
run_test "users-service" "tests/test_messaging.py" "RabbitMQ Messaging Tests" "Integration Test"

# 2. Rides Service Tests  
echo -e "\n${BLUE}🚗 RIDES SERVICE TESTS${NC}"
run_unit_test "rides-service" "tests.test_models" "Ride Models Unit Tests"

# 3. Payments Service Tests
echo -e "\n${BLUE}💳 PAYMENTS SERVICE TESTS${NC}"
run_unit_test "payments-service" "tests.test_models" "Payment Models Unit Tests"

# 4. Matching Service Tests
echo -e "\n${BLUE}🔍 MATCHING SERVICE TESTS${NC}"
run_test "matching-service" "tests/test_basic.py" "Basic API Tests" "Integration Test"

# Generate Test Report
echo -e "\n============================================================"
echo -e "${YELLOW}📊 TEST RESULTS SUMMARY${NC}"
echo -e "============================================================"

echo -e "\n${BLUE}Overall Results:${NC}"
echo "   Total Tests: ${total_tests}"
echo -e "   ${GREEN}Passed: ${passed_tests}${NC}"
echo -e "   ${RED}Failed: ${failed_tests}${NC}"

if [ $failed_tests -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED!${NC}"
    exit_code=0
else
    echo -e "\n${RED}⚠️  SOME TESTS FAILED${NC}"
    exit_code=1
fi

echo -e "\n${BLUE}Detailed Results:${NC}"
for result in "${test_results[@]}"; do
    service=$(echo $result | cut -d':' -f1)
    test_name=$(echo $result | cut -d':' -f2)
    status=$(echo $result | cut -d':' -f3)
    
    if [ "$status" = "PASSED" ]; then
        echo -e "   ${GREEN}✅${NC} ${service}: ${test_name}"
    else
        echo -e "   ${RED}❌${NC} ${service}: ${test_name}"
    fi
done

# Cleanup temp files (only if all tests passed)
if [ $failed_tests -eq 0 ]; then
    rm -f /tmp/test_output_*
    echo -e "\n${BLUE}Test logs have been cleaned up.${NC}"
else
    echo -e "\n${YELLOW}Test logs preserved for debugging:${NC}"
    ls -la /tmp/test_output_* 2>/dev/null | sed 's/^/   /' || echo "   No test output files found"
fi
echo -e "\n============================================================"
echo -e "${YELLOW}✅ Test Suite Complete - $(date)${NC}"
echo -e "============================================================"

exit $exit_code 