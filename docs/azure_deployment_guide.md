# Azure Deployment Guide - Carpooling Microservices Platform

## 🎯 Overview

This guide covers the complete Azure deployment of our carpooling microservices platform, including Azure Container Registry (ACR), Azure Container Instances (ACI), PostgreSQL Flexible Server, and automated CI/CD with GitHub Actions.

## 📋 Prerequisites

### Required Tools
- Azure CLI (`az`) installed and configured
- GitHub account with repository access
- Azure subscription with sufficient permissions

### Required Permissions
- Contributor role on Azure subscription
- Ability to create service principals
- Access to GitHub repository settings

## 🏗️ Infrastructure Components

### **Azure Resources Created**
```
Resource Group: rg-carpool-app
├── Azure Container Registry (carpoolacr)
├── PostgreSQL Flexible Server (carpool-postgres-server)
├── Container Instances (5x)
│   ├── users-service
│   ├── rides-service  
│   ├── matching-service
│   ├── payments-service
│   └── rabbitmq
└── Service Principal (carpool-github-actions)
```

## 🔧 Step 1: Initial Azure Setup

### 1.1 Create Resource Group
```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name rg-carpool-app \
  --location eastus
```

### 1.2 Register Required Providers
```bash
# Register Azure providers (one-time setup)
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.ContainerInstance
az provider register --namespace Microsoft.Network
az provider register --namespace Microsoft.Storage

# Verify registration
az provider show --namespace Microsoft.ContainerRegistry --query "registrationState"
```

### 1.3 Create Azure Container Registry
```bash
# Create ACR
az acr create \
  --resource-group rg-carpool-app \
  --name carpoolacr \
  --sku Basic \
  --admin-enabled true

# Import base images
az acr import \
  --name carpoolacr \
  --source mcr.microsoft.com/mirror/docker/library/rabbitmq:3-management \
  --image rabbitmq:3-management
```

## 💾 Step 2: Database Setup

### 2.1 Create PostgreSQL Flexible Server
```bash
# Create PostgreSQL server
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
```

### 2.2 Create Databases
```bash
# Create application databases
az postgres flexible-server db create \
  --resource-group rg-carpool-app \
  --server-name carpool-postgres-server \
  --database-name users_db

az postgres flexible-server db create \
  --resource-group rg-carpool-app \
  --server-name carpool-postgres-server \
  --database-name rides_db

az postgres flexible-server db create \
  --resource-group rg-carpool-app \
  --server-name carpool-postgres-server \
  --database-name payments_db
```

### 2.3 Configure Firewall
```bash
# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group rg-carpool-app \
  --name carpool-postgres-server \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## 🔑 Step 3: Service Principal Setup

### 3.1 Create Service Principal for GitHub Actions
```bash
# Create service principal
az ad sp create-for-rbac \
  --name "carpool-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-carpool-app \
  --sdk-auth

# Output will be JSON - save for GitHub secrets
```

### 3.2 Get Required Values
```bash
# Get subscription ID
az account show --query id --output tsv

# Get tenant ID  
az account show --query tenantId --output tsv

# Get ACR credentials
az acr credential show --name carpoolacr
```

## 🔐 Step 4: GitHub Secrets Configuration

Configure these secrets in your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):

### Required Secrets
```
AZURE_CLIENT_ID: <service-principal-client-id>
AZURE_CLIENT_SECRET: <service-principal-client-secret>
AZURE_TENANT_ID: <azure-tenant-id>
AZURE_SUBSCRIPTION_ID: <azure-subscription-id>
POSTGRES_SERVER: carpool-postgres-server
POSTGRES_ADMIN_USER: carpooladmin
POSTGRES_ADMIN_PASSWORD: YourSecurePassword123!
```

## 🚀 Step 5: Deployment Pipeline

### 5.1 GitHub Actions Workflow
The workflow automatically:

1. **Sets up ACR** - Creates registry and imports base images
2. **Builds services** - Compiles and pushes 4 microservices to ACR
3. **Runs tests** - Executes unit tests and code quality checks
4. **Deploys to Azure** - Creates container instances with proper networking

### 5.2 Trigger Deployment
```bash
# Push to main or test branch triggers deployment
git push origin main

# Or trigger manually in GitHub Actions UI
```

## 📊 Step 6: Verification

### 6.1 Check Container Status
```bash
# List all containers
az container list \
  --resource-group rg-carpool-app \
  --output table

# Check specific container
az container show \
  --resource-group rg-carpool-app \
  --name users-service \
  --query instanceView.state
```

### 6.2 Test Services
```bash
# Health checks (replace {build} with actual build number)
curl http://carpool-users-{build}.eastus.azurecontainer.io:8000/health
curl http://carpool-rides-{build}.eastus.azurecontainer.io:8000/health
curl http://carpool-matching-{build}.eastus.azurecontainer.io:8000/health
curl http://carpool-payments-{build}.eastus.azurecontainer.io:8000/health

# API documentation
open http://carpool-users-{build}.eastus.azurecontainer.io:8000/docs
```

### 6.3 RabbitMQ Management
```bash
# Access RabbitMQ UI
open http://carpool-rabbitmq-{build}.eastus.azurecontainer.io:15672

# Credentials: admin / admin123
```

## 🔧 Step 7: Troubleshooting

### Common Issues & Solutions

**Container startup failures:**
```bash
# Check container logs
az container logs \
  --resource-group rg-carpool-app \
  --name users-service

# Check container events
az container show \
  --resource-group rg-carpool-app \
  --name users-service \
  --query instanceView.events
```

**Database connection issues:**
```bash
# Test database connectivity
az postgres flexible-server connect \
  --name carpool-postgres-server \
  --admin-user carpooladmin \
  --admin-password "YourSecurePassword123!"
```

**ACR authentication problems:**
```bash
# Test ACR login
az acr login --name carpoolacr

# List ACR repositories
az acr repository list --name carpoolacr --output table

# Check ACR credentials
az acr credential show --name carpoolacr
```

**GitHub Actions failures:**
```bash
# Check workflow logs in GitHub Actions UI
# Common fixes:
# 1. Verify all secrets are set correctly
# 2. Ensure service principal has proper permissions
# 3. Check Azure provider registration status
```

## 📈 Step 8: Monitoring & Maintenance

### 8.1 Container Monitoring
```bash
# Monitor container resource usage
az container show \
  --resource-group rg-carpool-app \
  --name users-service \
  --query containers[0].instanceView.currentState

# Check restart count
az container show \
  --resource-group rg-carpool-app \
  --name users-service \
  --query containers[0].instanceView.restartCount
```

### 8.2 Database Monitoring
```bash
# Check database metrics
az postgres flexible-server show \
  --resource-group rg-carpool-app \
  --name carpool-postgres-server \
  --query state

# Monitor connections
az postgres flexible-server parameter show \
  --resource-group rg-carpool-app \
  --server-name carpool-postgres-server \
  --name max_connections
```

### 8.3 Cost Monitoring
```bash
# Check resource costs
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --billing-period-name current
```

## 🛠️ Step 9: Scaling & Updates

### 9.1 Manual Scaling
```bash
# Scale container resources
az container update \
  --resource-group rg-carpool-app \
  --name users-service \
  --cpu 1 \
  --memory 2
```

### 9.2 Service Updates
```bash
# Update service image (triggered by new push)
# Or manually update container
az container create \
  --resource-group rg-carpool-app \
  --name users-service-v2 \
  --image carpoolacr.azurecr.io/carpool-users:latest \
  # ... other parameters
```

## 🔮 Step 10: Next Steps

### Recommended Improvements
1. **Azure Container Apps** - Better scaling and traffic management
2. **Azure Service Bus** - Replace RabbitMQ with managed service
3. **Azure API Management** - Centralized API gateway
4. **Azure Key Vault** - Enhanced secret management
5. **Azure Front Door** - Global load balancing and CDN

### Production Hardening
1. **Private endpoints** - Secure database access
2. **Virtual networks** - Network isolation
3. **SSL certificates** - HTTPS for all endpoints
4. **Backup strategy** - Automated database backups
5. **Disaster recovery** - Multi-region deployment

## 📞 Support & Resources

### Useful Commands
```bash
# Quick status check
az container list --resource-group rg-carpool-app --query "[].{Name:name,State:instanceView.state}" --output table

# Restart all containers
az container restart --resource-group rg-carpool-app --name users-service
az container restart --resource-group rg-carpool-app --name rides-service
az container restart --resource-group rg-carpool-app --name matching-service
az container restart --resource-group rg-carpool-app --name payments-service
az container restart --resource-group rg-carpool-app --name rabbitmq

# Clean up resources (WARNING: Deletes everything)
az group delete --name rg-carpool-app --yes --no-wait
```

### Documentation Links
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances/)
- [PostgreSQL Flexible Server](https://docs.microsoft.com/azure/postgresql/flexible-server/)
- [GitHub Actions for Azure](https://docs.microsoft.com/azure/developer/github/github-actions)

The deployment is designed to be fully automated and reproducible. Any push to the main or test branch will trigger a complete rebuild and redeployment of the entire system. 