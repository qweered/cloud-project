# Carpooling and Shared Rides Management System

A microservices-based system for managing carpooling and shared rides.

## Core Microservices

- **Users Service**: Manages user accounts and profiles
- **Rides Service**: Handles ride creation, updates, and status
- **Matching Service**: Matches passengers with available drivers
- **Payments Service**: Processes payments and refunds

## Key Features

- User registration and profile management
- Ride booking and management
- Intelligent matching of passengers with drivers
- Secure payment processing
- Encrypted storage of PII data
- API endpoints for data access
- Message queues for service communication
- Logging and metrics
- In-memory caching

## Architecture

This section provides visual overviews of the system architecture, requirements, and design.

### Functional Requirements

The system supports core carpooling functionalities including user management, ride operations, and payment processing:

![Functional Requirements](docs/diagrams/rendered/Functional%20Requirements.png)

### Non-Functional Requirements

The system is designed with scalability, security, and performance in mind:

![Non-Functional Requirements](docs/diagrams/rendered/Non-Functional%20Requirements.png)

### Services Communication

The microservices communicate through REST APIs and message queues:

![Services Communication](docs/diagrams/rendered/Services%20Communication.png)

### Database Schema

The system uses a relational database with the following schema design:

![Database Schema](docs/diagrams/rendered/Database%20Schema.png)

## Project Structure

- `/docs`: Project documentation and diagrams
- `/services`: Microservice implementations
- `/.github`: CI/CD pipeline configurations

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- PlantUML (optional, for rendering diagrams)

### Running with Docker Compose

The easiest way to run the entire system is with Docker Compose:

```bash
docker compose up
```

This will start all services and their dependencies.

### Running for Development

For development, you can run the services individually:

1. Start individual services:
   ```bash
   cd services/users
   python main.py
   ```

2. Or use the provided script to start all services:
   ```bash
   ./start_services.sh
   ```

### Generating Diagrams

To generate the architectural diagrams:

```bash
./render_diagrams.sh
```

This will create PNG files in the `docs/diagrams/rendered` directory.

## API Documentation

Once the services are running, you can access the Swagger UI documentation at:

- Users Service: http://localhost:8001/docs
- Rides Service: http://localhost:8002/docs
- Matching Service: http://localhost:8003/docs
- Payments Service: http://localhost:8004/docs

## Metrics and Monitoring

Each service exposes metrics endpoints:

- `/health`: Health check endpoint
- `/ping`: Simple ping endpoint
- `/metrics`: Prometheus-compatible metrics endpoint
- `/info`: Service information endpoint

## CI/CD Pipeline

The project includes a GitHub Actions workflow for continuous integration and deployment. The pipeline:

1. Builds and tests each service
2. Creates Docker images
3. Deploys the services (when merged to main)

## Contributing

1. Clone the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. 