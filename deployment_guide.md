# Contract Intelligence System - Deployment Guide

Complete guide for deploying your multi-agent contract analysis system to production.

---

## 📋 Table of Contents

1. [Local Docker Testing](#local-docker-testing)
2. [AWS Prerequisites](#aws-prerequisites)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Application Deployment](#application-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## 🐳 Local Docker Testing

Test your containerized application locally before deploying to AWS.

### Quick Start

```bash
# Make script executable
chmod +x test-docker.sh

# Run the test
./test-docker.sh
```

### Manual Docker Testing

```bash
# Build the image
docker build -t contract-intelligence:test .

# Run the container
docker run -d \
  --name contract-test \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-key-here" \
  contract-intelligence:test

# Check health
curl http://localhost:8000/health

# View logs
docker logs -f contract-test

# Stop and clean up
docker stop contract-test && docker rm contract-test
```

### Docker Compose Testing

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## ☁️ AWS Prerequisites

### Required AWS Services

- **ECS Fargate** - Container orchestration
- **ECR** - Container registry
- **VPC** - Networking
- **ALB** - Load balancing
- **CloudWatch** - Logging and monitoring
- **Secrets Manager** - API key storage
- **IAM** - Permissions management

### AWS CLI Setup

```bash
# Install AWS CLI
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Output format (json)

### Verify AWS Access

```bash
# Check identity
aws sts get-caller-identity

# Should return your AWS account info
```

---

## 🏗️ AWS Infrastructure Setup

### Step 1: Create Infrastructure

This script creates all required AWS resources:

```bash
# Make script executable
chmod +x deployment/aws/create-infrastructure.sh

# Run infrastructure setup
cd deployment/aws
./create-infrastructure.sh
```

**What it creates:**
- ✅ VPC with public subnets in 2 availability zones
- ✅ Internet Gateway and route tables
- ✅ Security groups for ALB and ECS
- ✅ Application Load Balancer (ALB)
- ✅ Target group with health checks
- ✅ IAM roles for ECS tasks
- ✅ Secrets Manager secret for OpenAI API key
- ✅ ECS cluster

**Save the output values** - you'll need them!

```bash
export VPC_ID=vpc-xxxxx
export SUBNET_1=subnet-xxxxx
export SUBNET_2=subnet-xxxxx
export ECS_SG=sg-xxxxx
export TG_ARN=arn:aws:elasticloadbalancing:...
```

### Step 2: Update Task Definition

Edit `deployment/aws/task-definition.json`:

```json
{
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/contract-intelligence-ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/contract-intelligence-ecsTaskExecutionRole"
}
```

Replace `YOUR_ACCOUNT_ID` with your AWS account ID.

---

## 🚀 Application Deployment

### Deploy to AWS ECS

```bash
# Make deployment script executable
chmod +x deployment/aws/deploy.sh

# Run deployment
cd deployment/aws
./deploy.sh
```

**The script will:**
1. ✅ Create ECR repository (if needed)
2. ✅ Build Docker image
3. ✅ Push to ECR
4. ✅ Register ECS task definition
5. ✅ Update/Create ECS service

### Create ECS Service (First Time Only)

```bash
aws ecs create-service \
  --cluster contract-intelligence-cluster \
  --service-name contract-intelligence-service \
  --task-definition contract-intelligence-system \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$ECS_SG],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=contract-api,containerPort=8000" \
  --region us-east-1
```

### Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster contract-intelligence-cluster \
  --services contract-intelligence-service

# Check running tasks
aws ecs list-tasks \
  --cluster contract-intelligence-cluster \
  --service-name contract-intelligence-service

# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names contract-intelligence-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text
```

### Test Your Deployed API

```bash
# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names contract-intelligence-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# Test health endpoint
curl http://$ALB_DNS/health

# Test via browser
open http://$ALB_DNS
```

---

## 📊 Monitoring & Maintenance

### View Logs

```bash
# Stream logs
aws logs tail /ecs/contract-intelligence --follow

# View specific time range
aws logs tail /ecs/contract-intelligence --since 1h

# Filter logs
aws logs tail /ecs/contract-intelligence --filter-pattern "ERROR"
```

### CloudWatch Dashboard

1. Go to AWS Console → CloudWatch
2. Create Dashboard: "contract-intelligence"
3. Add widgets for:
   - ECS CPU/Memory utilization
   - ALB request count
   - ALB target health
   - API latency

### Scaling

```bash
# Update desired task count
aws ecs update-service \
  --cluster contract-intelligence-cluster \
  --service contract-intelligence-service \
  --desired-count 5
```

### Enable Auto-Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/contract-intelligence-cluster/contract-intelligence-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/contract-intelligence-cluster/contract-intelligence-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check task status
aws ecs describe-tasks \
  --cluster contract-intelligence-cluster \
  --tasks $(aws ecs list-tasks --cluster contract-intelligence-cluster --query 'taskArns[0]' --output text)

# Common issues:
# 1. OPENAI_API_KEY not set in Secrets Manager
# 2. IAM role missing permissions
# 3. Image pull failed (check ECR permissions)
```

### Health Checks Failing

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN

# If unhealthy:
# 1. Check security group allows port 8000
# 2. Verify /health endpoint responds
# 3. Check CloudWatch logs for errors
```

### High Costs

**Cost Optimization Tips:**
- Use FARGATE_SPOT for non-critical tasks
- Reduce task count during off-hours
- Set up billing alerts
- Use smaller task sizes (0.5 vCPU, 1GB RAM)

```bash
# Switch to Spot instances
aws ecs update-service \
  --cluster contract-intelligence-cluster \
  --service contract-intelligence-service \
  --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1
```

### Updating the Application

```bash
# Simple update (uses deployment script)
cd deployment/aws
./deploy.sh

# The script automatically:
# 1. Builds new image
# 2. Pushes to ECR
# 3. Updates task definition
# 4. Forces new deployment
```

---

## 💰 Cost Estimation

**Monthly AWS Costs (approximate):**

| Service | Configuration | Cost |
|---------|--------------|------|
| ECS Fargate | 2 tasks, 1 vCPU, 2GB RAM | ~$35 |
| ALB | Standard load balancer | ~$25 |
| ECR | Image storage | ~$1 |
| CloudWatch Logs | Standard logging | ~$5 |
| Data Transfer | Moderate usage | ~$10 |
| **Total** | | **~$76/month** |

**To reduce costs:**
- Use 0.5 vCPU and 1GB RAM: **~$40/month**
- Use single task (not HA): **~$30/month**
- Use Fargate Spot: **Save 70%**

---

## 🔒 Security Best Practices

1. **API Keys**
   - ✅ Store in Secrets Manager (done)
   - ✅ Rotate regularly
   - ✅ Use IAM roles, not hard-coded keys

2. **Network Security**
   - ✅ Use security groups
   - ✅ Only expose port 80/443 on ALB
   - ✅ Keep ECS tasks in private subnets (optional upgrade)

3. **HTTPS**
   ```bash
   # Add SSL certificate to ALB
   # 1. Request certificate in ACM
   # 2. Add HTTPS listener to ALB
   # 3. Redirect HTTP to HTTPS
   ```

4. **Rate Limiting**
   - Consider adding AWS WAF
   - Or implement rate limiting in FastAPI

---

## 🎓 What You've Accomplished

✅ **Containerized Application** - Docker best practices  
✅ **AWS Infrastructure** - Production-grade setup  
✅ **High Availability** - Multi-AZ deployment  
✅ **Auto-Scaling** - Handles traffic spikes  
✅ **Monitoring** - CloudWatch integration  
✅ **Security** - Secrets management, IAM roles  
✅ **CI/CD Ready** - Automated deployment scripts  

---

## 📚 Additional Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Questions or Issues?** Check the troubleshooting section or review CloudWatch logs!