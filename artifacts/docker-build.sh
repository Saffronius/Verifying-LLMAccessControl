#!/bin/bash

# Build script for Quacky Pipeline Demo Docker image

set -e

echo "Building Quacky Pipeline Demo Docker image..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found!${NC}"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file. Please add your API keys before running.${NC}"
    else
        echo -e "${RED}Error: .env.example not found!${NC}"
        exit 1
    fi
fi

# Build the Docker image from current directory
echo "Building Docker image..."
docker build \
    -t quacky-pipeline-demo:latest \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    echo ""
    echo "To run the container, use:"
    echo "  ./docker-run.sh"
    echo ""
    echo "Or with docker-compose:"
    echo "  docker-compose up"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi