import pulumi
import pulumi_aws as aws
import pulumi_eks as eks
import json

# Configuration
config = pulumi.Config()
app_name = "fastapi-app"

# 1. VPC for EKS
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

# Public Subnets in different AZs
public_subnet_1 = aws.ec2.Subnet(
    f"{app_name}-public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{app_name}-public-subnet-1",
        "kubernetes.io/role/elb": "1",
    },
)

public_subnet_2 = aws.ec2.Subnet(
    f"{app_name}-public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="ap-southeast-1b",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{app_name}-public-subnet-2",
        "kubernetes.io/role/elb": "1",
    },
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

# Associate Route Table with Subnets
rta1 = aws.ec2.RouteTableAssociation(
    f"{app_name}-rta-1",
    subnet_id=public_subnet_1.id,
    route_table_id=route_table.id,
)

rta2 = aws.ec2.RouteTableAssociation(
    f"{app_name}-rta-2",
    subnet_id=public_subnet_2.id,
    route_table_id=route_table.id,
)

# 2. EKS Cluster
cluster = eks.Cluster(
    f"{app_name}-cluster",
    vpc_id=vpc.id,
    subnet_ids=[public_subnet_1.id, public_subnet_2.id],
    instance_type="t3.medium",
    desired_capacity=2,
    min_size=1,
    max_size=3,
    enabled_cluster_log_types=["api", "audit", "authenticator"],
)

# 3. ECR Repository
repo = aws.ecr.Repository(
    f"{app_name}-repo",
    force_delete=True,
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

# ECR Lifecycle Policy
aws.ecr.LifecyclePolicy(
    f"{app_name}-lifecycle",
    repository=repo.name,
    policy=json.dumps({
        "rules": [{
            "rulePriority": 1,
            "description": "Keep last 10 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        }]
    }),
)

# Exports
pulumi.export("kubeconfig", cluster.kubeconfig)
pulumi.export("cluster_name", cluster.eks_cluster.name)
pulumi.export("ecr_repository_url", repo.repository_url)
