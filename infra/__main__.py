import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import json

# Configuration
config = pulumi.Config()
app_name = "fastapi-app"

# External database URL
external_db_url = config.get("external-db-url") or "postgresql://postgres:postgres@100.84.171.106:5432/postgres"

# 1. VPC and Networking
vpc = awsx.ec2.Vpc(
    f"{app_name}-vpc",
    number_of_availability_zones=2,
    nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(strategy="Single")
)

# 2. Security Groups
# ALB Security Group
alb_sg = aws.ec2.SecurityGroup(
    f"{app_name}-alb-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
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
)

# ECS Tasks Security Group
ecs_sg = aws.ec2.SecurityGroup(
    f"{app_name}-ecs-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for ECS tasks",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            security_groups=[alb_sg.id],
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
)

# 3. ECS Cluster
cluster = aws.ecs.get_cluster(cluster_name="default")

# 4. ECR Repository
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

# 5. IAM Roles
task_exec_role = aws.iam.Role(
    f"{app_name}-task-exec-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Effect": "Allow",
        }],
    }),
)

aws.iam.RolePolicyAttachment(
    f"{app_name}-task-exec-policy",
    role=task_exec_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

task_role = aws.iam.Role(
    f"{app_name}-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Effect": "Allow",
        }],
    }),
)

# 6. Task Definition (FastAPI only)
task_definition = aws.ecs.TaskDefinition(
    f"{app_name}-task",
    family=f"{app_name}-task",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_exec_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(repo.repository_url, external_db_url).apply(
        lambda args: json.dumps([
            {
                "name": "fastapi",
                "image": f"{args[0]}:latest",
                "essential": True,
                "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
                "environment": [
                    {"name": "DATABASE_URL", "value": args[1]},
                ],
                "healthCheck": {
                    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 60,
                },
            },
        ])
    ),
)

# 7. Application Load Balancer
alb = aws.lb.LoadBalancer(
    f"{app_name}-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=vpc.public_subnet_ids,
)

# Target Group
fastapi_tg = aws.lb.TargetGroup(
    f"{app_name}-tg",
    port=8000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
)

# HTTP Listener
http_listener = aws.lb.Listener(
    f"{app_name}-http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=fastapi_tg.arn,
        ),
    ],
)

# 8. ECS Service
service = aws.ecs.Service(
    f"{app_name}-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=vpc.private_subnet_ids,
        security_groups=[ecs_sg.id],
        assign_public_ip=False,
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=fastapi_tg.arn,
            container_name="fastapi",
            container_port=8000,
        ),
    ],
)

# Exports
pulumi.export("app_url", pulumi.Output.concat("http://", alb.dns_name))
pulumi.export("ecr_repository_url", repo.repository_url)
pulumi.export("cluster_name", cluster.name)
pulumi.export("service_name", service.name)
