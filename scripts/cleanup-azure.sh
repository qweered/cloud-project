#!/bin/bash

# Azure Cleanup Script for Carpool Microservices
# WARNING: This will delete ALL resources in the resource group

set -e

RESOURCE_GROUP="rg-carpool-app"

echo "⚠️  WARNING: This will delete ALL resources in resource group: $RESOURCE_GROUP"
echo "This action cannot be undone!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🗑️  Deleting Azure resources..."

# Delete all container instances first
echo "🐳 Cleaning up container instances..."
az container list --resource-group $RESOURCE_GROUP --query "[].name" --output tsv | while read container; do
    if [ ! -z "$container" ]; then
        echo "Deleting container: $container"
        az container delete --resource-group $RESOURCE_GROUP --name "$container" --yes
    fi
done

# Delete the entire resource group
echo "📦 Deleting resource group and all resources..."
az group delete --name $RESOURCE_GROUP --yes --no-wait

echo ""
echo "✅ Cleanup initiated. Resources are being deleted in the background."
echo "You can check the status in the Azure portal." 