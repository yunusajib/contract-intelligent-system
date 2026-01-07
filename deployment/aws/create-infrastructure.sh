#!/bin/bash

# Contract Intelligence System - AWS Infrastructure Setup
# This script creates all required AWS resources

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
PROJECT_NAME="contract-intelligence"

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  AWS Infrastructure Setup${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "AWS Account: $AWS_ACCOUNT_ID"

echo ""
echo -e "${BLUE}1. Creating VPC and Networking${NC}"
echo "================================================================="

# Create VPC
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc}]" \
    --region $AWS_REGION \
    --query 'Vpc.VpcId' \
    --output text)

print_status "VPC Created: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames \
    --region $AWS_REGION

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-igw}]" \
    --region $AWS_REGION \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway \
    --vpc-id $VPC_ID \
    --internet-gateway-id $IGW_ID \
    --region $AWS_REGION

print_status "Internet Gateway: $IGW_ID"

# Create Public Subnets in 2 AZs
SUBNET_1_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone ${AWS_REGION}a \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-1}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text)

SUBNET_2_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone ${AWS_REGION}b \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-2}]" \
    --region $AWS_REGION \
    --query 'Subnet.SubnetId' \
    --output text)

print_status "Subnets: $SUBNET_1_ID, $SUBNET_2_ID"

# Create Route Table
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-rt}]" \
    --region $AWS_REGION \
    --query 'RouteTable.RouteTableId' \
    --output text)

aws ec2 create-route \
    --route-table-id $ROUTE_TABLE_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID \
    --region $AWS_REGION

aws ec2 associate-route-table \
    --subnet-id $SUBNET_1_ID \
    --route-table-id $ROUTE_TABLE_ID \
    --region $AWS_REGION

aws ec2 associate-route-table \
    --subnet-id $SUBNET_2_ID \
    --route-table-id $ROUTE_TABLE_ID \
    --region $AWS_REGION

print_status "Route Table configured"

echo ""
echo -e "${BLUE}2. Creating Security Groups${NC}"
echo "================================================================="

# Create Security Group for ALB
ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-alb-sg \
    --description "Security group for ALB" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' \
    --output text)

aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

print_status "ALB Security Group: $ALB_SG_ID"

# Create Security Group for ECS Tasks
ECS_SG_ID=$(aws ec2 create-security-group \
    --group-name ${PROJECT_NAME}-ecs-sg \
    --description "Security group for ECS tasks" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' \
    --output text)

aws ec2 authorize-security-group-ingress \
    --group-id $ECS_SG_ID \
    --protocol tcp \
    --port 8000 \
    --source-group $ALB_SG_ID \
    --region $AWS_REGION

print_status "ECS Security Group: $ECS_SG_ID"

echo ""
echo -e "${BLUE}3. Creating Application Load Balancer${NC}"
echo "================================================================="

ALB_ARN=$(aws elbv2 create-load-balancer \
    --name ${PROJECT_NAME}-alb \
    --subnets $SUBNET_1_ID $SUBNET_2_ID \
    --security-groups $ALB_SG_ID \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --region $AWS_REGION \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

print_status "ALB Created: $ALB_DNS"

# Create Target Group
TG_ARN=$(aws elbv2 create-target-group \
    --name ${PROJECT_NAME}-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-enabled \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --region $AWS_REGION \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

print_status "Target Group: $TG_ARN"

# Create ALB Listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $AWS_REGION

print_status "Listener configured"

echo ""
echo -e "${BLUE}4. Creating IAM Roles${NC}"
echo "================================================================="

# Create ECS Task Execution Role
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name ${PROJECT_NAME}-ecsTaskExecutionRole \
    --assume-role-policy-document file://trust-policy.json \
    --region $AWS_REGION 2>/dev/null || true

aws iam attach-role-policy \
    --role-name ${PROJECT_NAME}-ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    --region $AWS_REGION

# Add Secrets Manager policy
cat > secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name ${PROJECT_NAME}-ecsTaskExecutionRole \
    --policy-name SecretsManagerAccess \
    --policy-document file://secrets-policy.json

print_status "IAM Roles created"

# Clean up temp files
rm trust-policy.json secrets-policy.json

echo ""
echo -e "${BLUE}5. Creating Secrets Manager Secret${NC}"
echo "================================================================="

print_info "Please enter your OpenAI API key:"
read -s OPENAI_KEY

aws secretsmanager create-secret \
    --name ${PROJECT_NAME}/openai-api-key \
    --description "OpenAI API Key for Contract Intelligence System" \
    --secret-string "$OPENAI_KEY" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id ${PROJECT_NAME}/openai-api-key \
    --secret-string "$OPENAI_KEY" \
    --region $AWS_REGION

print_status "Secret stored in Secrets Manager"

echo ""
echo -e "${BLUE}6. Creating ECS Cluster${NC}"
echo "================================================================="

aws ecs create-cluster \
    --cluster-name ${PROJECT_NAME}-cluster \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --region $AWS_REGION

print_status "ECS Cluster created"

echo ""
echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Infrastructure Setup Complete!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${BLUE}Summary of Created Resources:${NC}"
echo "  VPC: $VPC_ID"
echo "  Subnets: $SUBNET_1_ID, $SUBNET_2_ID"
echo "  ALB DNS: $ALB_DNS"
echo "  Target Group: $TG_ARN"
echo "  ECS Security Group: $ECS_SG_ID"
echo ""
echo -e "${BLUE}Save these values - you'll need them for deployment:${NC}"
echo ""
echo "export VPC_ID=$VPC_ID"
echo "export SUBNET_1=$SUBNET_1_ID"
echo "export SUBNET_2=$SUBNET_2_ID"
echo "export ECS_SG=$ECS_SG_ID"
echo "export TG_ARN=$TG_ARN"
echo ""
echo -e "${YELLOW}Next Step:${NC} Run deployment/aws/deploy.sh to deploy your application"