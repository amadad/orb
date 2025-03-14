#!/bin/bash
# run_server.sh - Deploy the Digital Being application in Docker
# 
# This script:
# 1. Stops any existing Docker containers running on port 8000
# 2. Builds the Docker image from the Dockerfile
# 3. Runs the container with the proper environment variables
# 4. Checks if the server is responding
# 5. Provides information about Twitter and other integrations
#
# Usage: ./run_server.sh [--rebuild] [--logs] [--help]
#   --rebuild: Force rebuild the Docker image even if it exists
#   --logs: Follow the logs after starting the container
#   --help: Show this help message

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Image name
IMAGE_NAME="digital-being"

# Default values
REBUILD=false
FOLLOW_LOGS=false

# Check for command line arguments
for arg in "$@"; do
  case $arg in
    --rebuild)
      REBUILD=true
      ;;
    --logs)
      FOLLOW_LOGS=true
      ;;
    --help)
      echo -e "${GREEN}Usage: ./run_server.sh [OPTIONS]${NC}"
      echo -e "  --rebuild      Force rebuild the Docker image"
      echo -e "  --logs         Follow the logs after starting the server"
      echo -e "  --help         Show this help message"
      exit 0
      ;;
  esac
done

# Print header
echo -e "${YELLOW}===============================================${NC}"
echo -e "${YELLOW}    DEPLOYING DIGITAL BEING APPLICATION        ${NC}"
echo -e "${YELLOW}===============================================${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo -e "${RED}Error: .env file not found.${NC}"
  echo -e "Please create a .env file with the necessary environment variables."
  echo -e "Example:"
  echo -e "COMPOSIO_API_KEY=your_api_key_here"
  exit 1
fi

# Check if OAuth file exists
OAUTH_FILE_FOUND=false
if [ -f "my_digital_being/storage/oauth_tokens.json" ]; then
  OAUTH_FILE_FOUND=true
  OAUTH_FILE="my_digital_being/storage/oauth_tokens.json"
elif [ -f "storage/oauth_tokens.json" ]; then
  OAUTH_FILE_FOUND=true
  OAUTH_FILE="storage/oauth_tokens.json"
fi

if [ "$OAUTH_FILE_FOUND" = true ]; then
  echo -e "${GREEN}Found existing OAuth file with connections.${NC}"
  
  # Extract available connections
  if [ -f "$OAUTH_FILE" ]; then
    CONNECTIONS=$(grep -o '"app_name": "[^"]*"' "$OAUTH_FILE" | cut -d '"' -f 4 | sort | uniq)
    if [ ! -z "$CONNECTIONS" ]; then
      echo -e "${BLUE}Available connections: ${NC}$CONNECTIONS"
      
      # Check for specific integrations
      if echo "$CONNECTIONS" | grep -q "TWITTER"; then
        echo -e "${GREEN}✅ Twitter integration is configured.${NC}"
      else
        echo -e "${YELLOW}⚠️ Twitter integration is not configured.${NC}"
      fi
      
      if echo "$CONNECTIONS" | grep -q "LINKEDIN"; then
        echo -e "${GREEN}✅ LinkedIn integration is configured.${NC}"
      else
        echo -e "${YELLOW}⚠️ LinkedIn integration is not configured.${NC}"
      fi
    fi
  fi
else
  echo -e "${YELLOW}⚠️ No OAuth file found. You will need to set up integrations.${NC}"
fi

# Stop any existing containers running on port 8000
echo -e "\n${YELLOW}Stopping any existing containers...${NC}"
docker stop $(docker ps -q --filter "publish=8000") 2>/dev/null || true

# Check if we should rebuild or if the image doesn't exist
if [ "$REBUILD" = true ] || [ -z "$(docker images -q $IMAGE_NAME 2>/dev/null)" ]; then
  echo -e "\n${YELLOW}Building Docker image...${NC}"
  docker build --platform linux/amd64 -t $IMAGE_NAME .
else
  echo -e "\n${GREEN}Using existing Docker image. Use --rebuild to force a rebuild.${NC}"
fi

# Run the container
echo -e "\n${YELLOW}Starting the server...${NC}"
CONTAINER_ID=$(docker run -d --platform linux/amd64 -p 8000:8000 --env-file .env $IMAGE_NAME)

if [ -z "$CONTAINER_ID" ]; then
  echo -e "${RED}Failed to start the container.${NC}"
  exit 1
fi

echo -e "${GREEN}Server started in container: $CONTAINER_ID${NC}"

# Wait for server to start
echo -e "\n${YELLOW}Waiting for server to start...${NC}"
MAX_ATTEMPTS=10
ATTEMPT=1
STARTED=false

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
  echo -e "Attempt $ATTEMPT of $MAX_ATTEMPTS..."
  sleep 3
  
  # Check health endpoint
  HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "failed")
  if [ "$HEALTH_STATUS" = "200" ]; then
    STARTED=true
    break
  fi
  
  ATTEMPT=$((ATTEMPT+1))
done

if [ "$STARTED" = true ]; then
  echo -e "\n${GREEN}===============================================${NC}"
  echo -e "${GREEN}    DIGITAL BEING SERVER IS RUNNING!            ${NC}"
  echo -e "${GREEN}===============================================${NC}"
  echo -e "${GREEN}The server is accessible at: http://localhost:8000${NC}"
  echo -e "\n${YELLOW}Recent logs:${NC}"
  docker logs $CONTAINER_ID | tail -n 10
else
  echo -e "\n${YELLOW}Server may still be starting up. Recent logs:${NC}"
  docker logs $CONTAINER_ID
fi

# Print management commands
echo -e "\n${BLUE}Management commands:${NC}"
echo -e "  View logs in real-time:     ${YELLOW}docker logs -f $CONTAINER_ID${NC}"
echo -e "  Stop the server:            ${YELLOW}docker stop $CONTAINER_ID${NC}"
echo -e "  Restart the server:         ${YELLOW}docker restart $CONTAINER_ID${NC}"

# Follow logs if requested
if [ "$FOLLOW_LOGS" = true ]; then
  echo -e "\n${YELLOW}Following logs (Ctrl+C to exit)...${NC}"
  docker logs -f $CONTAINER_ID
fi 