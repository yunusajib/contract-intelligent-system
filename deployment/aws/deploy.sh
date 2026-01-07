#!/bin/bash

# Contract Intelligence System - AWS Deployment Script
# This script automates the deployment to AWS ECS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
ECR_REPO_NAME="contract-intelligence"
ECS_CLUSTER_NAME="contract-intelligence-cluster"
ECS_SERVICE_NAME="contract-intelligence-service"
TASK_FAMILY="contract-intelligence-system"

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  Contract Intelligence System - AWS Deployment${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

# Function to print colored messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    echo "Visit: https://aws.amazon.com/cli/"
    exit 1
fi

print_status "AWS CLI found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

print_status "Docker found"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "AWS Account ID: $AWS_ACCOUNT_ID"

# ECR Repository URL
ECR_REPO_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo ""
echo -e "${BLUE}Step 1: Creating ECR Repository (if not exists)${NC}"
echo "================================================================="

# Check if ECR repository exists
if aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION &> /dev/null; then
    print_status "ECR repository already exists"
else
    print_info "Creating ECR repository..."
    aws ecr create-repository \
        --repository-name $ECR_REPO_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    print_status "ECR repository created"
fi

echo ""
echo -e "${BLUE}Step 2: Building Docker Image${NC}"
echo "================================================================="

print_info "Building Docker image..."
docker build -t $ECR_REPO_NAME:latest ../../

print_status "Docker image built successfully"

echo ""
echo -e "${BLUE}Step 3: Tagging Docker Image${NC}"
echo "================================================================="

docker tag $ECR_REPO_NAME:latest $ECR_REPO_URL:latest
docker tag $ECR_REPO_NAME:latest $ECR_REPO_URL:$(date +%Y%m%d-%H%M%S)

print_status "Image tagged"

echo ""
echo -e "${BLUE}Step 4: Logging into ECR${NC}"
echo "================================================================="

aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPO_URL

print_status "Logged into ECR"

echo ""
echo -e "${BLUE}Step 5: Pushing Image to ECR${NC}"
echo "================================================================="

print_info "Pushing image to ECR (this may take a few minutes)..."
docker push $ECR_REPO_URL:latest
docker push $ECR_REPO_URL:$(date +%Y%m%d-%H%M%S)

print_status "Image pushed to ECR"

echo ""
echo -e "${BLUE}Step 6: Creating CloudWatch Log Group${NC}"
echo "================================================================="

# Create CloudWatch log group if it doesn't exist
if aws logs describe-log-groups --log-group-name-prefix "/ecs/contract-intelligence" --region $AWS_REGION | grep -q "/ecs/contract-intelligence"; then
    print_status "CloudWatch log group already exists"
else
    aws logs create-log-group \
        --log-group-name /ecs/contract-intelligence \
        --region $AWS_REGION
    print_status "CloudWatch log group created"
fi

echo ""
echo -e "${BLUE}Step 7: Updating Task Definition${NC}"
echo "================================================================="

# Update task definition JSON with actual values
print_info "Updating task definition with account ID..."
sed "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" task-definition.json > task-definition-updated.json

# Register task definition
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://task-definition-updated.json \
    --region $AWS_REGION \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

print_status "Task definition registered: $TASK_DEFINITION_ARN"

# Clean up temporary file
rm task-definition-updated.json

echo ""
echo -e "${BLUE}Step 8: Checking ECS Cluster${NC}"
echo "================================================================="

# Check if ECS cluster exists
if aws ecs describe-clusters --clusters $ECS_CLUSTER_NAME --region $AWS_REGION | grep -q "ACTIVE"; then
    print_status "ECS cluster exists"
else
    print_info "Creating ECS cluster..."
    aws ecs create-cluster \
        --cluster-name $ECS_CLUSTER_NAME \
        --region $AWS_REGION \
        --capacity-providers FARGATE FARGATE_SPOT \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
    print_status "ECS cluster created"
fi

echo ""
echo -e "${BLUE}Step 9: Updating ECS Service${NC}"
echo "================================================================="

# Check if service exists
if aws ecs describe-services \
    --cluster $ECS_CLUSTER_NAME \
    --services $ECS_SERVICE_NAME \
    --region $AWS_REGION | grep -q "ACTIVE"; then
    
    print_info "Updating existing ECS service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER_NAME \
        --service $ECS_SERVICE_NAME \
        --task-definition $TASK_DEFINITION_ARN \
        --force-new-deployment \
        --region $AWS_REGION > /dev/null
    
    print_status "Service updated successfully"
else
    print_warning "Service doesn't exist. You need to create it first."
    print_info "Run: deployment/aws/create-service.sh"
fi

echo ""
echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Monitor deployment: aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME"
echo "2. View logs: aws logs tail /ecs/contract-intelligence --follow"
echo "3. Check service URL in AWS Console > ECS > Services"
echo ""
echo -e "${YELLOW}Note: It may take 2-3 minutes for the service to become healthy${NC}"