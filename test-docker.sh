#!/bin/bash

# Test Docker Build and Run Locally

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  Testing Docker Build Locally${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from example..."
    cp .env.example .env
    print_info "Please update .env with your API keys before continuing"
    exit 1
fi

print_status ".env file found"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo ""
echo -e "${BLUE}Step 1: Installing Updated Dependencies${NC}"
echo "================================================================="

# Reinstall requirements locally first
pip install -q pysqlite3-binary

print_status "Dependencies updated"

echo ""
echo -e "${BLUE}Step 2: Building Docker Image${NC}"
echo "================================================================="

docker build -t contract-intelligence:test .

print_status "Docker image built successfully"

echo ""
echo -e "${BLUE}Step 3: Running Container${NC}"
echo "================================================================="

# Stop and remove existing container if running
docker stop contract-test 2>/dev/null || true
docker rm contract-test 2>/dev/null || true

# Run container
docker run -d \
    --name contract-test \
    -p 8000:8000 \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e ENVIRONMENT=development \
    -e LOG_LEVEL=INFO \
    contract-intelligence:test

print_status "Container started"

echo ""
echo -e "${BLUE}Step 4: Waiting for Container to be Healthy${NC}"
echo "================================================================="

print_info "Waiting for application to start (max 60 seconds)..."

for i in {1..60}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    echo -n "."
    sleep 1
done

echo ""

# Check if healthy
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Container is healthy!"
    
    echo ""
    echo -e "${BLUE}Step 5: Testing API${NC}"
    echo "================================================================="
    
    # Test health endpoint
    HEALTH=$(curl -s http://localhost:8000/health)
    print_status "Health check passed"
    echo "$HEALTH" | jq '.'
    
    echo ""
    echo -e "${GREEN}=====================================================================${NC}"
    echo -e "${GREEN}  Docker Test Successful!${NC}"
    echo -e "${GREEN}=====================================================================${NC}"
    echo ""
    echo -e "${BLUE}Your application is running at:${NC}"
    echo "  Local:  http://localhost:8000"
    echo "  Docs:   http://localhost:8000/docs"
    echo "  Health: http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}Container Info:${NC}"
    echo "  Name: contract-test"
    echo "  Image: contract-intelligence:test"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs:    docker logs -f contract-test"
    echo "  Stop:         docker stop contract-test"
    echo "  Remove:       docker rm contract-test"
    echo "  Shell access: docker exec -it contract-test /bin/bash"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring logs${NC}"
    echo ""
    
    # Follow logs
    docker logs -f contract-test
    
else
    print_warning "Container failed health check"
    echo ""
    echo "Logs:"
    docker logs contract-test
    echo ""
    echo "Stopping container..."
    docker stop contract-test
    docker rm contract-test
    exit 1
fi