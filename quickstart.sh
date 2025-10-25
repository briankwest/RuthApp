#!/bin/bash

# Ruth Platform - Quick Start Script
# This script sets up and starts the Ruth platform quickly

set -e

echo "================================================"
echo "        Ruth Platform - Quick Start"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit backend/.env and add your API keys:${NC}"
    echo "   - OPENAI_API_KEY"
    echo "   - GEOCODIO_API_KEY"
    echo "   - SECRET_KEY (32 random characters)"
    echo "   - JWT_SECRET_KEY (32 random characters)"
    echo ""
    echo "Press Enter after you've added your API keys..."
    read
fi

# Start services
echo -e "${GREEN}Starting Docker containers...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check if services are running
if docker-compose ps | grep -q "ruth_backend.*Up"; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    docker-compose logs backend
    exit 1
fi

if docker-compose ps | grep -q "ruth_postgres.*Up"; then
    echo -e "${GREEN}✓ Database is running${NC}"
else
    echo -e "${RED}✗ Database failed to start${NC}"
    docker-compose logs postgres
    exit 1
fi

# Run migrations
echo -e "${GREEN}Running database migrations...${NC}"
docker-compose exec backend alembic upgrade head

# Test the API
echo -e "${GREEN}Testing API endpoints...${NC}"
curl -s http://localhost:8000/health | grep -q "healthy" && echo -e "${GREEN}✓ API is healthy${NC}" || echo -e "${RED}✗ API health check failed${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}       Ruth Platform is ready!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Access points:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/api/docs"
echo "  • Frontend: http://localhost:3000 (when implemented)"
echo ""
echo "Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Run tests: docker-compose exec backend python test_api.py"
echo ""
echo -e "${YELLOW}Next step: Test the authentication system${NC}"
echo "Run: docker-compose exec backend python test_api.py"
echo ""