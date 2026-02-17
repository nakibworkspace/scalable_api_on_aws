#!/bin/bash
# Helper script to SSH into EC2 instance

EC2_IP=$(cd infra && pulumi stack output instance_public_ip)

if [ -z "$EC2_IP" ]; then
    echo "Error: Could not get EC2 IP from Pulumi"
    exit 1
fi

echo "Connecting to EC2 instance at $EC2_IP..."
ssh -i ec2-key ec2-user@$EC2_IP
