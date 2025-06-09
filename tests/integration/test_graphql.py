"""
Tests for GraphQL endpoint
"""

import httpx
import json
from datetime import datetime


# Sample GraphQL queries and mutations
GRAPHQL_QUERIES = {
    
    "health_check": """
    query {
        users {
            id
            email
            first_name
            last_name
            role
        }
    }
    """,
    
    "get_rides": """
    query {
        rides(status: "scheduled") {
            id
            status
            origin_location {
                latitude
                longitude
            }
            destination_location {
                latitude
                longitude
            }
            start_time
            max_passengers
            current_passengers
            price_per_seat
        }
    }
    """,
    
    "get_user_stats": """
    query GetUserStats($userId: Int!) {
        userStats(userId: $userId) {
            userId
            totalRidesAsDriver
            totalRidesAsPassenger
            totalEarnings
            totalSpent
            averageRating
        }
    }
    """,
    
    "find_matches": """
    mutation FindMatches($matchInput: MatchInput!) {
        findMatches(matchInput: $matchInput) {
            rideId
            passengerId
            pickupLocation {
                latitude
                longitude
            }
            dropoffLocation {
                latitude
                longitude
            }
            estimatedPickupTime
            confidenceScore
        }
    }
    """,
    
    "create_user": """
    mutation CreateUser($userInput: UserInput!) {
        createUser(userInput: $userInput) {
            id
            email
            firstName
            lastName
            role
        }
    }
    """,
    
    "create_ride": """
    mutation CreateRide($rideInput: RideInput!) {
        createRide(rideInput: $rideInput) {
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
            startTime
            maxPassengers
            pricePerSeat
        }
    }
    """
}


async def test_graphql_endpoint():
    """Test that GraphQL endpoint is accessible"""
    async with httpx.AsyncClient() as client:
        # Simple introspection query
        introspection_query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        response = await client.post(
            "http://users-service:8000/graphql",
            json={"query": introspection_query}
        )
        
        print(f"GraphQL introspection status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"GraphQL schema has {len(data.get('data', {}).get('__schema', {}).get('types', []))} types")


async def test_sample_queries():
    """Test sample GraphQL queries"""
    async with httpx.AsyncClient() as client:
        print("\n🔍 Testing GraphQL Queries:")
        
        # Test simple queries
        for query_name, query in GRAPHQL_QUERIES.items():
            if query_name in ["health_check", "get_rides"]:
                print(f"\n  Testing {query_name}...")
                
                response = await client.post(
                    "http://users-service:8000/graphql",
                    json={"query": query}
                )
                
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if "errors" in data:
                        print(f"    GraphQL Errors: {data['errors']}")
                    else:
                        print(f"    ✅ Query successful")
                        if data.get("data"):
                            for key, value in data["data"].items():
                                if isinstance(value, list):
                                    print(f"    Returned {len(value)} {key}")
                                else:
                                    print(f"    Returned {key}: {type(value)}")


async def test_mutations():
    """Test GraphQL mutations"""
    async with httpx.AsyncClient() as client:
        print("\n🛠️  Testing GraphQL Mutations:")
        
        # Test user creation
        create_user_query = GRAPHQL_QUERIES["create_user"]
        variables = {
            "userInput": {
                "email": f"graphql-test-{int(datetime.now().timestamp())}@example.com",
                "firstName": "GraphQL",
                "lastName": "Test",
                "phoneNumber": "+1234567890",
                "password": "testpass123",
                "role": "passenger"
            }
        }
        
        response = await client.post(
            "http://users-service:8000/graphql",
            json={
                "query": create_user_query,
                "variables": variables
            }
        )
        
        print(f"  Create User Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"    GraphQL Errors: {data['errors']}")
            else:
                print(f"    ✅ User creation successful")
                user_data = data.get("data", {}).get("createUser")
                if user_data:
                    print(f"    Created user ID: {user_data.get('id')}")


def run_graphql_tests():
    """Run all GraphQL tests"""
    import asyncio
    
    async def run_all():
        print("🚀 GraphQL Endpoint Tests")
        print("=" * 50)
        
        await test_graphql_endpoint()
        await test_sample_queries()
        await test_mutations()
        
        print("\n✅ GraphQL tests completed!")
    
    asyncio.run(run_all())


if __name__ == "__main__":
    run_graphql_tests() 