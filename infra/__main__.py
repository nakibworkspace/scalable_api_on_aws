import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
app_name = "fastapi-app"
database_url = config.get("database_url") or "postgresql://postgres:postgres@localhost:5432/postgres"

# 1. VPC
vpc = aws.ec2.Vpc(
    f"{app_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": f"{app_name}-vpc"},
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    f"{app_name}-igw",
    vpc_id=vpc.id,
    tags={"Name": f"{app_name}-igw"},
)

# Public Subnet
public_subnet = aws.ec2.Subnet(
    f"{app_name}-public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    tags={"Name": f"{app_name}-public-subnet"},
)

# Route Table
route_table = aws.ec2.RouteTable(
    f"{app_name}-rt",
    vpc_id=vpc.id,
    tags={"Name": f"{app_name}-rt"},
)

# Route to Internet Gateway
route = aws.ec2.Route(
    f"{app_name}-route",
    route_table_id=route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id,
)

# Associate Route Table with Subnet
rta = aws.ec2.RouteTableAssociation(
    f"{app_name}-rta",
    subnet_id=public_subnet.id,
    route_table_id=route_table.id,
)

# 2. Security Group for EC2
security_group = aws.ec2.SecurityGroup(
    f"{app_name}-sg",
    vpc_id=vpc.id,
    description="Allow HTTP traffic",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={"Name": f"{app_name}-sg"},
)

# 3. User Data Script - simplified without ECR
user_data = f"""#!/bin/bash
set -e

# Install Docker
yum update -y
yum install -y docker git
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone your repo and run with docker-compose
# Note: You'll need to manually deploy or use GitHub Actions
echo "Docker installed. Ready for deployment."
echo "DATABASE_URL={database_url}" > /home/ec2-user/.env

# Create a simple deployment script
cat > /home/ec2-user/deploy.sh << 'EOF'
#!/bin/bash
cd /home/ec2-user/app
git pull
docker-compose down
docker-compose up -d --build
EOF

chmod +x /home/ec2-user/deploy.sh
chown ec2-user:ec2-user /home/ec2-user/deploy.sh

echo "Deployment complete! SSH in and run ./deploy.sh after cloning your repo"
"""

# 4. EC2 Instance
instance = aws.ec2.Instance(
    f"{app_name}-instance",
    instance_type="t3.small",
    ami="ami-01811d4912b4ccb26",  # Amazon Linux 2023 in ap-southeast-1
    subnet_id=public_subnet.id,
    vpc_security_group_ids=[security_group.id],
    user_data=user_data,
    tags={"Name": f"{app_name}-instance"},
)

# Exports
pulumi.export("instance_id", instance.id)
pulumi.export("instance_public_ip", instance.public_ip)
pulumi.export("instance_public_dns", instance.public_dns)
pulumi.export("application_url", instance.public_dns.apply(lambda dns: f"http://{dns}"))
pulumi.export("ssh_command", instance.public_ip.apply(lambda ip: f"ssh ec2-user@{ip}"))
