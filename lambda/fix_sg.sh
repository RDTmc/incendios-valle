#!/bin/bash
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance: $INSTANCE_ID"

SG_ID=$(aws ec2 describe-instances --instance-id "$INSTANCE_ID" --region us-east-1 --query "Reservations[].Instances[].SecurityGroups[].GroupId" --output text)
echo "SG: $SG_ID"

aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 --region us-east-1 2>&1
echo "Done"
