#!/bin/bash

# Test script to verify Docker setup for Quacky Pipeline Demo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Quacky Pipeline Demo - Docker Setup Test${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Check Docker installation
echo -e "${YELLOW}1. Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    docker --version
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
echo -e "${YELLOW}2. Checking Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    docker-compose --version
elif docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose (plugin) is installed${NC}"
    docker compose version
else
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose"
    exit 1
fi

# Check Docker daemon
echo -e "${YELLOW}3. Checking Docker daemon...${NC}"
if docker info &> /dev/null; then
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "${RED}✗ Docker daemon is not running or you don't have permissions${NC}"
    echo "Try: sudo usermod -aG docker $USER"
    echo "Then logout and login again"
    exit 1
fi

# Check .env file
echo -e "${YELLOW}4. Checking .env file...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    
    # Check for API keys (without revealing them)
    if grep -q "ANTHROPIC_API_KEY=" .env && grep -q "^[^#]*ANTHROPIC_API_KEY=..*" .env; then
        echo -e "${GREEN}  ✓ ANTHROPIC_API_KEY is set${NC}"
    else
        echo -e "${YELLOW}  ⚠ ANTHROPIC_API_KEY might not be set${NC}"
    fi
    
    if grep -q "OPENAI_API_KEY=" .env && grep -q "^[^#]*OPENAI_API_KEY=..*" .env; then
        echo -e "${GREEN}  ✓ OPENAI_API_KEY is set${NC}"
    else
        echo -e "${YELLOW}  ⚠ OPENAI_API_KEY might not be set${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
    fi
fi

# Check required files
echo -e "${YELLOW}5. Checking required files...${NC}"
required_files=("Dockerfile" "docker-compose.yml" "app.py" "requirements.txt")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓ $file exists${NC}"
    else
        echo -e "${RED}  ✗ $file is missing${NC}"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "${RED}Missing required files. Please ensure all files are present.${NC}"
    exit 1
fi

# Check port availability
echo -e "${YELLOW}6. Checking port 8501...${NC}"
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 8501 is already in use${NC}"
    echo "You may need to stop the existing service or use a different port"
else
    echo -e "${GREEN}✓ Port 8501 is available${NC}"
fi

# Summary
echo
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}All checks passed! You can now build and run the Docker container:${NC}"
echo
echo -e "${BLUE}To build:${NC}"
echo "  docker-compose build"
echo
echo -e "${BLUE}To run:${NC}"
echo "  docker-compose up -d"
echo
echo -e "${BLUE}To view logs:${NC}"
echo "  docker-compose logs -f"
echo
echo -e "${BLUE}To stop:${NC}"
echo "  docker-compose down"
echo
echo -e "${YELLOW}Note: First build will take 5-10 minutes to compile ABC and fetch dependencies${NC}"
echo -e "${BLUE}==================================================${NC}"