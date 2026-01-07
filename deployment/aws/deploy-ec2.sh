#!/bin/bash

# Deploy to AWS EC2 (No Docker Required!)
# This is perfect for showcasing to recruiters without Docker issues

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  Contract Intelligence System - EC2 Deployment${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# Configuration
INSTANCE_TYPE="t3.small"  # $0.0208/hour (~$15/month)
AMI_ID="ami-0fcb14c72c80bdef2" # Ubuntu 20.04 LTS (update for your region)
KEY_NAME="contract-intelligence-key"
SECURITY_GROUP="contract-intelligence-sg"
REGION="${AWS_REGION:-us-east-1}"

echo -e "${BLUE}Step 1: Creating EC2 Key Pair${NC}"
echo "================================================================="

if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION &>/dev/null; then
    print_info "Creating SSH key pair..."
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text \
        --region $REGION > ~/.ssh/$KEY_NAME.pem
    
    chmod 400 ~/.ssh/$KEY_NAME.pem
    print_status "Key pair created: ~/.ssh/$KEY_NAME.pem"
else
    print_status "Key pair already exists"
fi

echo ""
echo -e "${BLUE}Step 2: Creating Security Group${NC}"
echo "================================================================="

# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text \
    --region $REGION)

# Create security group if it doesn't exist
if ! aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION &>/dev/null; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP \
        --description "Security group for Contract Intelligence System" \
        --vpc-id $VPC_ID \
        --region $REGION \
        --query 'GroupId' \
        --output text)
    
    # Allow SSH
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    # Allow HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    # Allow app port
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    print_status "Security group created: $SG_ID"
else
    SG_ID=$(aws ec2 describe-security-groups \
        --group-names $SECURITY_GROUP \
        --query 'SecurityGroups[0].GroupId' \
        --output text \
        --region $REGION)
    print_status "Security group exists: $SG_ID"
fi

echo ""
echo -e "${BLUE}Step 3: Launching EC2 Instance${NC}"
echo "================================================================="

# Create user data script
cat > user-data.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Python 3.11
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip git nginx

# Create app directory
mkdir -p /opt/contract-intelligence
cd /opt/contract-intelligence

# Clone or copy application (you'll need to modify this)
# For now, we'll assume you SCP the files after instance creation

# Create systemd service
cat > /etc/systemd/system/contract-intelligence.service << 'SYSTEMD'
[Unit]
Description=Contract Intelligence System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/contract-intelligence
Environment="OPENAI_API_KEY=YOUR_KEY_HERE"
ExecStart=/opt/contract-intelligence/venv/bin/python /opt/contract-intelligence/start.py
Restart=always

[Install]
WantedBy=multi-user.target
SYSTEMD

# Configure nginx as reverse proxy
cat > /etc/nginx/sites-available/contract-intelligence << 'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/contract-intelligence /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

echo "EC2 setup complete!"
EOF

# Launch instance
print_info "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --user-data file://user-data.sh \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=contract-intelligence}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

print_status "Instance launched: $INSTANCE_ID"

# Wait for instance to be running
print_info "Waiting for instance to start (this takes ~2 minutes)..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region $REGION)

print_status "Instance is running!"

echo ""
echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  EC2 Instance Ready!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${BLUE}Instance Details:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  SSH Key: ~/.ssh/$KEY_NAME.pem"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Wait 2-3 minutes for instance setup to complete"
echo ""
echo "2. Copy your code to the instance:"
echo "   cd ../.."
echo "   tar czf app.tar.gz agents api core tests *.py requirements.txt"
echo "   scp -i ~/.ssh/$KEY_NAME.pem app.tar.gz ubuntu@$PUBLIC_IP:~/"
echo ""
echo "3. SSH into instance:"
echo "   ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo "4. On the instance, run:"
echo "   cd /opt/contract-intelligence"
echo "   sudo tar xzf ~/app.tar.gz -C ."
echo "   python3.11 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   sudo nano /etc/systemd/system/contract-intelligence.service"
echo "   # Update OPENAI_API_KEY in the service file"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl start contract-intelligence"
echo "   sudo systemctl enable contract-intelligence"
echo ""
echo "5. Access your app:"
echo "   http://$PUBLIC_IP"
echo ""
echo -e "${BLUE}Monitoring:${NC}"
echo "   sudo systemctl status contract-intelligence"
echo "   sudo journalctl -u contract-intelligence -f"
echo ""

# Clean up temp file
rm user-data.sh

echo -e "${GREEN}Setup complete!${NC}"