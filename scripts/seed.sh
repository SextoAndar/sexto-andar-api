#!/bin/bash
# Seed Data Helper Script
# Usage:
#   ./scripts/seed.sh          - Run in Docker (default)
#   ./scripts/seed.sh local    - Run locally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in Docker or locally
MODE="${1:-docker}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Sexto Andar API - Seed Data${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$MODE" = "local" ]; then
    echo -e "${BLUE}Running locally...${NC}"
    echo -e "${YELLOW}Make sure both auth service and API are running!${NC}"
    echo ""
    
    # Check if services are running
    if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${RED}❌ Auth service is not running on http://localhost:8001${NC}"
        echo -e "${YELLOW}Start it with: cd ../sexto-andar-auth && docker-compose up${NC}"
        exit 1
    fi
    
    if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${RED}❌ API service is not running on http://localhost:8000${NC}"
        echo -e "${YELLOW}Start it with: docker-compose up${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Services are running${NC}"
    echo ""
    
    # Run script locally
    cd "$PROJECT_DIR"
    python3 scripts/seed_data.py
    
else
    echo -e "${BLUE}Running in Docker container...${NC}"
    echo ""
    
    # Check if container is running
    if ! docker-compose ps api | grep -q "Up"; then
        echo -e "${RED}❌ API container is not running${NC}"
        echo -e "${YELLOW}Start it with: docker-compose up -d${NC}"
        exit 1
    fi
    
    # Check if auth service is accessible from container
    if ! docker-compose exec -T api curl -s http://sexto-andar-auth:8000/health > /dev/null 2>&1; then
        echo -e "${RED}❌ Auth service is not accessible from container${NC}"
        echo -e "${YELLOW}Make sure sexto-andar-auth is running with: cd ../sexto-andar-auth && docker-compose up${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Services are running${NC}"
    echo ""
    
    # Run script in Docker
    cd "$PROJECT_DIR"
    docker-compose exec api python scripts/seed_data.py
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Seeding complete!${NC}"
echo -e "${GREEN}========================================${NC}"
