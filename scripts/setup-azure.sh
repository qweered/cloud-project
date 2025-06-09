#!/bin/bash

# Azure Infrastructure Setup Script for Carpool Microservices
# Run this script after installing Azure CLI and logging in

set -e

# Configuration
RESOURCE_GROUP="rg-carpool-app"
LOCATION="northeurope"
POSTGRES_SERVER="carpool-postgres-server"
POSTGRES_ADMIN_USER="carpooladmin"
POSTGRES_ADMIN_PASSWORD="YourSecurePassword123!"
SERVICE_BUS_NAMESPACE="carpool-servicebus"
VNET_NAME="carpool-vnet"

# echo "🚀 Setting up Azure infrastructure for Carpool Microservices..."

# Create Resource Group
# echo "📦 Creating resource group..."
# az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Virtual Network
# echo "🌐 Creating virtual network..."
# az network vnet create \
#   --resource-group $RESOURCE_GROUP \
#   --name $VNET_NAME \
#   --address-prefix 10.0.0.0/16 \
#   --subnet-name default \
#   --subnet-prefix 10.0.1.0/24

# Create PostgreSQL Flexible Server
# echo "🗄️ Creating PostgreSQL Flexible Server..."
# az postgres flexible-server create \
#   --resource-group $RESOURCE_GROUP \
#   --name $POSTGRES_SERVER \
#   --location $LOCATION \
#   --admin-user $POSTGRES_ADMIN_USER \
#   --admin-password $POSTGRES_ADMIN_PASSWORD \
#   --sku-name Standard_B2s \
#   --tier Burstable \
#   --version 14 \
#   --storage-size 32 \
#   --public-access 0.0.0.0-255.255.255.255

# Create databases
# echo "📊 Creating databases..."
# az postgres flexible-server db create --resource-group $RESOURCE_GROUP --server-name $POSTGRES_SERVER --database-name users_db
# az postgres flexible-server db create --resource-group $RESOURCE_GROUP --server-name $POSTGRES_SERVER --database-name rides_db
# az postgres flexible-server db create --resource-group $RESOURCE_GROUP --server-name $POSTGRES_SERVER --database-name payments_db

# Configure firewall (skip if public access not enabled - handled manually)
echo "🔒 Configuring firewall rules..."
echo "Note: If this fails due to public access being disabled, enable it manually in Azure Portal"

# # Create Service Bus
# echo "📨 Creating Service Bus..."
# az servicebus namespace create \
#   --resource-group $RESOURCE_GROUP \
#   --name $SERVICE_BUS_NAMESPACE \
#   --location $LOCATION

# # Create topics
# az servicebus topic create \
#   --resource-group $RESOURCE_GROUP \
#   --namespace-name $SERVICE_BUS_NAMESPACE \
#   --name ride-events

# az servicebus topic create \
#   --resource-group $RESOURCE_GROUP \
#   --namespace-name $SERVICE_BUS_NAMESPACE \
#   --name payment-events

# Create Application Insights
echo "📈 Creating Application Insights..."
az monitor app-insights component create \
  --app carpool-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Create Log Analytics workspace
echo "📋 Creating Log Analytics workspace..."
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name carpool-logs

# Get connection strings
echo "🔑 Retrieving credentials..."
echo ""
echo "=== POSTGRESQL CONNECTION INFO ==="
echo "Server: $POSTGRES_SERVER.postgres.database.azure.com"
echo "Admin User: $POSTGRES_ADMIN_USER"
echo "Admin Password: $POSTGRES_ADMIN_PASSWORD"

echo ""
echo "=== SERVICE BUS CONNECTION STRING ==="
az servicebus namespace authorization-rule keys list \
  --resource-group $RESOURCE_GROUP \
  --namespace-name $SERVICE_BUS_NAMESPACE \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString \
  --output tsv

echo ""
echo "✅ Azure infrastructure setup completed!"
echo ""
echo "Next steps:"
echo "1. Create a service principal for GitHub Actions"
echo "2. Configure GitHub secrets (no container registry needed - using GitHub Container Registry)"
echo "3. Push your code to trigger deployment"
echo ""
echo "To create service principal, run:"
echo "az ad sp create-for-rbac --name 'carpool-github-actions' --role contributor --scopes /subscriptions/\$(az account show --query id --output tsv)/resourceGroups/$RESOURCE_GROUP --sdk-auth" 
