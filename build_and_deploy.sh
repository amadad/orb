#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="givecare"
ACR_NAME="givecareregistry"
APP_NAME="digital-being"
IMAGE_NAME="digital-being"
IMAGE_TAG="latest"

# Login to Azure
echo "Logging into Azure..."
az account show > /dev/null || az login

# Login to ACR
echo "Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Build the image
echo "Building Docker image..."
docker build -t $IMAGE_NAME:$IMAGE_TAG .

# Tag the image for ACR
echo "Tagging image for ACR..."
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

# Push to ACR
echo "Pushing image to ACR..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

# Update the web app to use the container
echo "Updating App Service to use container..."
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --docker-custom-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io

# Set website to always on
echo "Configuring App Service settings..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --always-on true

echo "Deployment complete!"
echo "Your app should be available at: https://$APP_NAME.azurewebsites.net" 