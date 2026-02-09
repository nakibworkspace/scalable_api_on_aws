import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import json

# Configuration
config = pulumi.Config()
app_name = "fastapi-app"
db_username = config.get("db-username") or "dbadmin"
db_password = config.get_secret("db-password") or "changeme123"  # Default for dev only
db_name = config.get("db-name") or "fastapi_db"

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
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=9090,
            to_port=9090,
            security_groups=[alb_sg.id],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3000,
            to_port=3000,
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

# RDS Security Group
rds_sg = aws.ec2.SecurityGroup(
    f"{app_name}-rds-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for RDS PostgreSQL",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            security_groups=[ecs_sg.id],
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

# 3. RDS PostgreSQL Database
db_subnet_group = aws.rds.SubnetGroup(
    f"{app_name}-db-subnet-group",
    subnet_ids=vpc.private_subnet_ids,
    tags={"Name": f"{app_name}-db-subnet-group"},
)

rds_instance = aws.rds.Instance(
    f"{app_name}-postgres",
    identifier=f"{app_name}-postgres",
    engine="postgres",
    engine_version="15.4",
    instance_class="db.t3.micro",  # Free tier eligible
    allocated_storage=20,
    storage_type="gp3",
    db_name=db_name,
    username=db_username,
    password=db_password,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[rds_sg.id],
    publicly_accessible=False,
    skip_final_snapshot=True,  # For dev/testing only
    backup_retention_period=7,
    multi_az=False,  # Set to True for production
    tags={"Name": f"{app_name}-postgres"},
)

# Build DATABASE_URL from RDS instance
database_url = pulumi.Output.all(
    rds_instance.endpoint,
    db_username,
    db_password,
    db_name
).apply(lambda args: f"postgresql://{args[1]}:{args[2]}@{args[0]}/{args[3]}")

# 4. ECS Cluster
cluster = aws.ecs.Cluster(f"{app_name}-cluster")

# 5. ECR Repository
repo = aws.ecr.Repository(
    f"{app_name}-repo",
    force_delete=True,
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

# ECR Lifecycle Policy to keep only last 10 images
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

# 6. EFS for persistent storage (Prometheus and Grafana data)
efs_sg = aws.ec2.SecurityGroup(
    f"{app_name}-efs-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for EFS",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=2049,
            to_port=2049,
            security_groups=[ecs_sg.id],
        ),
    ],
)

efs_fs = aws.efs.FileSystem(
    f"{app_name}-efs",
    encrypted=True,
    tags={"Name": f"{app_name}-efs"},
)

# Mount targets in each subnet
mount_target_0 = aws.efs.MountTarget(
    f"{app_name}-mt-0",
    file_system_id=efs_fs.id,
    subnet_id=vpc.private_subnet_ids[0],
    security_groups=[efs_sg.id],
)

mount_target_1 = aws.efs.MountTarget(
    f"{app_name}-mt-1",
    file_system_id=efs_fs.id,
    subnet_id=vpc.private_subnet_ids[1],
    security_groups=[efs_sg.id],
)

mount_targets = [mount_target_0, mount_target_1]

# Access points for Prometheus and Grafana
prometheus_ap = aws.efs.AccessPoint(
    f"{app_name}-prometheus-ap",
    file_system_id=efs_fs.id,
    posix_user=aws.efs.AccessPointPosixUserArgs(gid=65534, uid=65534),
    root_directory=aws.efs.AccessPointRootDirectoryArgs(
        path="/prometheus",
        creation_info=aws.efs.AccessPointRootDirectoryCreationInfoArgs(
            permissions="755",
            owner_gid=65534,
            owner_uid=65534,
        ),
    ),
)

grafana_ap = aws.efs.AccessPoint(
    f"{app_name}-grafana-ap",
    file_system_id=efs_fs.id,
    posix_user=aws.efs.AccessPointPosixUserArgs(gid=472, uid=472),
    root_directory=aws.efs.AccessPointRootDirectoryArgs(
        path="/grafana",
        creation_info=aws.efs.AccessPointRootDirectoryCreationInfoArgs(
            permissions="755",
            owner_gid=472,
            owner_uid=472,
        ),
    ),
)

# 7. IAM Roles
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

# 8. CloudWatch Log Group
log_group = aws.cloudwatch.LogGroup(
    f"{app_name}-logs",
    retention_in_days=7,
)

# 9. Task Definition (FastAPI + Prometheus + Grafana)
task_definition = aws.ecs.TaskDefinition(
    f"{app_name}-task",
    family=f"{app_name}-stack",
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_exec_role.arn,
    task_role_arn=task_role.arn,
    volumes=[
        aws.ecs.TaskDefinitionVolumeArgs(
            name="prometheus-data",
            efs_volume_configuration=aws.ecs.TaskDefinitionVolumeEfsVolumeConfigurationArgs(
                file_system_id=efs_fs.id,
                transit_encryption="ENABLED",
                authorization_config=aws.ecs.TaskDefinitionVolumeEfsVolumeConfigurationAuthorizationConfigArgs(
                    access_point_id=prometheus_ap.id,
                ),
            ),
        ),
        aws.ecs.TaskDefinitionVolumeArgs(
            name="grafana-data",
            efs_volume_configuration=aws.ecs.TaskDefinitionVolumeEfsVolumeConfigurationArgs(
                file_system_id=efs_fs.id,
                transit_encryption="ENABLED",
                authorization_config=aws.ecs.TaskDefinitionVolumeEfsVolumeConfigurationAuthorizationConfigArgs(
                    access_point_id=grafana_ap.id,
                ),
            ),
        ),
    ],
    container_definitions=pulumi.Output.all(repo.repository_url, database_url).apply(
        lambda args: json.dumps([
            {
                "name": "fastapi",
                "image": f"{args[0]}:latest",
                "essential": True,
                "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
                "environment": [
                    {"name": "DATABASE_URL", "value": args[1]},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.name,
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": "fastapi",
                    },
                },
                "healthCheck": {
                    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 60,
                },
            },
            {
                "name": "prometheus",
                "image": "prom/prometheus:latest",
                "essential": False,
                "portMappings": [{"containerPort": 9090, "protocol": "tcp"}],
                "mountPoints": [
                    {
                        "sourceVolume": "prometheus-data",
                        "containerPath": "/prometheus",
                    },
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.name,
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": "prometheus",
                    },
                },
            },
            {
                "name": "grafana",
                "image": "grafana/grafana:latest",
                "essential": False,
                "portMappings": [{"containerPort": 3000, "protocol": "tcp"}],
                "environment": [
                    {"name": "GF_SECURITY_ADMIN_PASSWORD", "value": "admin"},
                ],
                "mountPoints": [
                    {
                        "sourceVolume": "grafana-data",
                        "containerPath": "/var/lib/grafana",
                    },
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.name,
                        "awslogs-region": "us-east-1",
                        "awslogs-stream-prefix": "grafana",
                    },
                },
            },
        ])
    ),
)

# 10. Application Load Balancer
alb = aws.lb.LoadBalancer(
    f"{app_name}-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=vpc.public_subnet_ids,
)

# Target Groups
fastapi_tg = aws.lb.TargetGroup(
    f"{app_name}-api-tg",
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

prometheus_tg = aws.lb.TargetGroup(
    f"{app_name}-prom-tg",
    port=9090,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/-/healthy",
        interval=30,
    ),
)

grafana_tg = aws.lb.TargetGroup(
    f"{app_name}-graf-tg",
    port=3000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/api/health",
        interval=30,
    ),
)

# Listeners
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

# Path-based routing
aws.lb.ListenerRule(
    f"{app_name}-prom-rule",
    listener_arn=http_listener.arn,
    priority=100,
    actions=[
        aws.lb.ListenerRuleActionArgs(
            type="forward",
            target_group_arn=prometheus_tg.arn,
        ),
    ],
    conditions=[
        aws.lb.ListenerRuleConditionArgs(
            path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                values=["/prometheus*"],
            ),
        ),
    ],
)

aws.lb.ListenerRule(
    f"{app_name}-graf-rule",
    listener_arn=http_listener.arn,
    priority=101,
    actions=[
        aws.lb.ListenerRuleActionArgs(
            type="forward",
            target_group_arn=grafana_tg.arn,
        ),
    ],
    conditions=[
        aws.lb.ListenerRuleConditionArgs(
            path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                values=["/grafana*"],
            ),
        ),
    ],
)

# 11. ECS Service
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
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=prometheus_tg.arn,
            container_name="prometheus",
            container_port=9090,
        ),
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=grafana_tg.arn,
            container_name="grafana",
            container_port=3000,
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=mount_targets + [rds_instance]),
)

# Exports
pulumi.export("app_url", pulumi.Output.concat("http://", alb.dns_name))
pulumi.export("prometheus_url", pulumi.Output.concat("http://", alb.dns_name, "/prometheus"))
pulumi.export("grafana_url", pulumi.Output.concat("http://", alb.dns_name, "/grafana"))
pulumi.export("ecr_repository_url", repo.repository_url)
pulumi.export("cluster_name", cluster.name)
pulumi.export("rds_endpoint", rds_instance.endpoint)
pulumi.export("rds_database_name", db_name)
pulumi.export("database_url", database_url)
