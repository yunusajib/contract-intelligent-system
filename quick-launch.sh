#!/bin/bash
set -e

REGION="us-east-1"
KEY_NAME="contract-key-$(date +%s)"

echo "🔑 Creating new key pair..."
aws ec2 create-key-pair \
  --key-name $KEY_NAME \
  --query 'KeyMaterial' \
  --output text \
  --region $REGION > ~/.ssh/$KEY_NAME.pem

chmod 400 ~/.ssh/$KEY_NAME.pem
echo "✓ Key saved to ~/.ssh/$KEY_NAME.pem"

echo "🔍 Finding latest Ubuntu AMI..."
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text \
  --region $REGION)

echo "✓ Using AMI: $AMI_ID"

echo "🚀 Launching instance..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.small \
  --key-name $KEY_NAME \
  --security-group-ids sg-039b72d2056181808 \
  --region $REGION \
  --user-data '#!/bin/bash
apt-get update
apt-get install -y python3-pip python3-venv nginx
' \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=contract-intelligence}]" \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✓ Instance launched: $INSTANCE_ID"
echo "⏳ Waiting for instance to be running..."

aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region $REGION)

echo ""
echo "=========================================="
echo "✅ Instance Ready!"
echo "=========================================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "SSH Key: ~/.ssh/$KEY_NAME.pem"
echo ""
echo "Wait 60 seconds, then connect:"
echo "ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo "Save these for later:"
echo "export INSTANCE_ID=$INSTANCE_ID"
echo "export PUBLIC_IP=$PUBLIC_IP"
echo "export KEY_NAME=$KEY_NAME"
