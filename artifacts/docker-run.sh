#!/bin/bash

# Run script for Quacky Pipeline Demo Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Container name
CONTAINER_NAME="quacky-pipeline-demo"
IMAGE_NAME="quacky-pipeline-demo:latest"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with your API keys:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your keys"
    exit 1
fi

# Check if image exists
if ! docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
    echo -e "${YELLOW}Docker image not found. Building...${NC}"
    ./docker-build.sh
fi

# Stop and remove existing container if it exists
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
fi

# Create directories for volumes if they don't exist
mkdir -p results temp

# Run the container
echo -e "${BLUE}Starting Quacky Pipeline Demo...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    -p 8501:8501 \
    --env-file .env \
    -v "$(pwd)/.env:/app/.env:ro" \
    -v "$(pwd)/results:/app/results" \
    -v "$(pwd)/temp:/app/temp" \
    --restart unless-stopped \
    $IMAGE_NAME

# Wait for the container to be ready
echo "Waiting for application to start..."
sleep 5

# Check if container is running
if docker ps | grep -q $CONTAINER_NAME; then
    echo -e "${GREEN}✅ Quacky Pipeline Demo is running!${NC}"
    echo ""
    echo -e "${BLUE}Access the application at:${NC}"
    echo "  http://localhost:8501"
    echo ""
    echo -e "${YELLOW}To view logs:${NC}"
    echo "  docker logs -f $CONTAINER_NAME"
    echo ""
    echo -e "${YELLOW}To stop the container:${NC}"
    echo "  docker stop $CONTAINER_NAME"
else
    echo -e "${RED}❌ Failed to start container!${NC}"
    echo "Check logs with: docker logs $CONTAINER_NAME"
    exit 1
fi