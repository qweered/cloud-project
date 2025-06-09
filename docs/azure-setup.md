# Azure Deployment Setup Guide

This guide walks you through deploying your Carpool Microservices project to Azure using GitHub Actions CI/CD.

## Azure Infrastructure Overview

We'll deploy the application using:
- **Azure Container Registry (ACR)** - To store Docker images (reliable and integrated)
- **Azure Container Instances (ACI)** - To run the containers (alternative: Azure Container Apps)
- **Azure Database for PostgreSQL** - Managed PostgreSQL databases
- **Azure Service Bus** - For RabbitMQ messaging (alternative: self-hosted RabbitMQ)
- **Azure Virtual Network** - For secure service communication

## Prerequisites

1. **Azure Account** with an active subscription
2. **GitHub repository** with your code
3. **Azure CLI** installed locally (for initial setup)

## Step 1: Azure Resource Setup

### 1.1 Create Resource Group

```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-carpool-app --location eastus
```

### 1.2 Azure Container Registry Setup

```bash
# Create Azure Container Registry
az acr create \
  --resource-group rg-carpool-app \
  --name carpoolacr \
  --sku Basic \
  --admin-enabled true

# Import base images (RabbitMQ, etc.)
az acr import \
  --name carpoolacr \
  --source docker.io/rabbitmq:3-management \
  --image rabbitmq:3-management
```

**ACR Configuration:**
- Name: `carpoolacr` (must be globally unique)
- SKU: Basic (~$5/month)
- Admin access: Enabled for CI/CD
- Auto-imports: Base images like RabbitMQ

### 1.3 Create Azure Database for PostgreSQL Flexible Server

```bash
# Create PostgreSQL Flexible Server (replaces deprecated Single Server)
az postgres flexible-server create \
  --resource-group rg-carpool-app \
  --name carpool-postgres-server \
  --location eastus \
  --admin-user carpooladmin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B2s \
  --tier Burstable \
  --version 14 \
  --storage-size 32 \
  --public-access 0.0.0.0-255.255.255.255

# Create databases
az postgres flexible-server db create --resource-group rg-carpool-app --server-name carpool-postgres-server --database-name users_db
az postgres flexible-server db create --resource-group rg-carpool-app --server-name carpool-postgres-server --database-name rides_db
az postgres flexible-server db create --resource-group rg-carpool-app --server-name carpool-postgres-server --database-name payments_db

# Configure firewall to allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group rg-carpool-app \
  --name carpool-postgres-server \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 1.4 Create Service Bus for Messaging

```bash
# Create Service Bus namespace
az servicebus namespace create --resource-group rg-carpool-app --name carpool-servicebus --location eastus

# Create topics and subscriptions (replace RabbitMQ queues)
az servicebus topic create --resource-group rg-carpool-app --namespace-name carpool-servicebus --name ride-events
az servicebus topic create --resource-group rg-carpool-app --namespace-name carpool-servicebus --name payment-events
```

### 1.5 Create Virtual Network

```bash
# Create virtual network
az network vnet create \
  --resource-group rg-carpool-app \
  --name carpool-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name default \
  --subnet-prefix 10.0.1.0/24
```

## Step 2: GitHub Secrets Configuration

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets:

- `AZURE_CLIENT_ID` - Service Principal Client ID
- `AZURE_CLIENT_SECRET` - Service Principal Client Secret  
- `AZURE_TENANT_ID` - Azure Tenant ID
- `AZURE_SUBSCRIPTION_ID` - Azure Subscription ID
- `POSTGRES_SERVER` - PostgreSQL server name
- `POSTGRES_ADMIN_USER` - PostgreSQL admin username
- `POSTGRES_ADMIN_PASSWORD` - PostgreSQL admin password

**Note**: ACR credentials are automatically managed by the deployment pipeline.

### Creating Service Principal:

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac --name "carpool-github-actions" --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-carpool-app \
  --sdk-auth

# This will output JSON with the credentials you need for GitHub secrets
```

## Step 3: Deployment Options

### Option A: Azure Container Instances (Simpler)

- Each service runs as a separate Container Instance
- Suitable for development/testing environments
- Easy to set up and manage
- Lower cost for small applications

### Option B: Azure Container Apps (Recommended for Production)

- Managed Kubernetes-based platform
- Better for microservices architectures
- Built-in scaling, traffic splitting, and blue-green deployments
- Supports Dapr for service-to-service communication

### Option C: Azure Kubernetes Service (AKS)

- Full Kubernetes cluster
- Maximum control and flexibility
- Best for complex enterprise applications
- Higher complexity and cost

## Step 4: Environment Configuration

The deployment will use these environment variables:

### Database Configuration:
- `DB_HOST` - Azure PostgreSQL server endpoint
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password
- `DB_NAME` - Database name per service

### Service Communication:
- `USERS_SERVICE_URL` - Internal service URL
- `RIDES_SERVICE_URL` - Internal service URL

### Messaging:
- `SERVICE_BUS_CONNECTION_STRING` - Azure Service Bus connection string

## Step 5: Monitoring and Logging

### Application Insights Setup:

```bash
# Create Application Insights
az monitor app-insights component create \
  --app carpool-insights \
  --location eastus \
  --resource-group rg-carpool-app
```

### Log Analytics Workspace:

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group rg-carpool-app \
  --workspace-name carpool-logs
```

## Step 6: Security Considerations

1. **Network Security**: Use private endpoints for databases
2. **Key Management**: Store secrets in Azure Key Vault
3. **Authentication**: Configure managed identities
4. **SSL/TLS**: Enable HTTPS for all services
5. **Firewall Rules**: Restrict database access

## Step 7: Cost Optimization

1. **Use Basic tier** for ACR and databases in development
2. **Configure auto-scaling** for Container Apps
3. **Use Azure Cost Management** to monitor expenses
4. **Implement resource tagging** for cost tracking

## Step 8: Troubleshooting

### Common Issues:

1. **Container startup failures**: Check environment variables and secrets
2. **Database connection issues**: Verify firewall rules and connection strings
3. **Service discovery**: Ensure proper DNS configuration in virtual network
4. **Image pull errors**: Verify ACR credentials and permissions

### Debugging Commands:

```bash
# Check container logs
az container logs --resource-group rg-carpool-app --name users-service

# View container status
az container show --resource-group rg-carpool-app --name users-service

# Test database connectivity
az postgres flexible-server show --resource-group rg-carpool-app --name carpool-postgres-server
```

## Step 9: Maintenance

1. **Regular Updates**: Keep base images and dependencies updated
2. **Backup Strategy**: Configure automated database backups
3. **Health Monitoring**: Set up alerts for service health
4. **Performance Monitoring**: Use Application Insights for performance metrics

## Next Steps

1. Review and customize the provided GitHub Actions workflow
2. Set up Azure resources using the commands above
3. Configure GitHub secrets
4. Test the deployment pipeline
5. Set up monitoring and alerting
6. Plan for production scaling

This setup provides a robust, scalable foundation for your carpool microservices application on Azure. 