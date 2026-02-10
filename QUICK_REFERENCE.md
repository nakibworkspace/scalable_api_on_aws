# Quick Reference Guide

## Essential Commands

### Local Development

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild after code changes
docker-compose up -d --build

# Run tests
pytest

# Run with coverage
pytest --cov=app

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

### AWS & Pulumi

```bash
# Preview infrastructure changes
cd infra && pulumi preview

# Deploy infrastructure
cd infra && pulumi up

# Destroy infrastructure
cd infra && pulumi destroy

# View stack outputs
cd infra && pulumi stack output

# View specific output
cd infra && pulumi stack output app_url

# View secrets
cd infra && pulumi stack output database_url --show-secrets

# Set configuration
pulumi config set aws:region us-east-1
pulumi config set --secret db-password YourPassword123!
```

### Docker & ECR

```bash
# Build image
docker build -t fastapi-app:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ecr-url>

# Tag image
docker tag fastapi-app:latest <ecr-url>:latest

# Push to ECR
docker push <ecr-url>:latest

# List ECR images
aws ecr list-images --repository-name fastapi-app-repo
```

### ECS Operations

```bash
# List clusters
aws ecs list-clusters

# Describe service
aws ecs describe-services \
  --cluster fastapi-app-cluster \
  --services fastapi-app-service

# List tasks
aws ecs list-tasks --cluster fastapi-app-cluster

# Describe task
aws ecs describe-tasks \
  --cluster fastapi-app-cluster \
  --tasks <task-arn>

# Force new deployment
aws ecs update-service \
  --cluster fastapi-app-cluster \
  --service fastapi-app-service \
  --force-new-deployment

# Scale service
aws ecs update-service \
  --cluster fastapi-app-cluster \
  --service fastapi-app-service \
  --desired-count 3

# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Execute command in container
aws ecs execute-command \
  --cluster fastapi-app-cluster \
  --task <task-id> \
  --container fastapi \
  --interactive \
  --command "/bin/bash"
```

### RDS Operations

```bash
# Describe RDS instances
aws rds describe-db-instances

# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier fastapi-app-postgres \
  --db-snapshot-identifier fastapi-snapshot-$(date +%Y%m%d)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier fastapi-app-postgres-restored \
  --db-snapshot-identifier fastapi-snapshot-20240101

# Modify instance
aws rds modify-db-instance \
  --db-instance-identifier fastapi-app-postgres \
  --db-instance-class db.t3.small \
  --apply-immediately
```

### Load Balancer

```bash
# Describe load balancers
aws elbv2 describe-load-balancers

# Describe target groups
aws elbv2 describe-target-groups

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Describe listeners
aws elbv2 describe-listeners \
  --load-balancer-arn <alb-arn>
```

### Monitoring & Logs

```bash
# CloudWatch log groups
aws logs describe-log-groups

# Tail logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Filter logs
aws logs filter-log-events \
  --log-group-name /aws/ecs/fastapi-app-logs \
  --filter-pattern "ERROR"

# Get metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=fastapi-app-service \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average
```

## Configuration Files

### Pulumi Config (infra/Pulumi.production.yaml)

```yaml
config:
  aws:region: us-east-1
  fastapi-app:db-username: dbadmin
  fastapi-app:db-name: fastapi_db
  fastapi-app:db-password:
    secure: <encrypted-password>
```

### Environment Variables

```bash
# Local development (.env)
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=appdb
POSTGRES_HOST=localhost
DATABASE_URL=postgresql://user:pass@localhost:5432/appdb

# Production (ECS Task Definition)
DATABASE_URL=postgresql://dbadmin:pass@rds-endpoint:5432/fastapi_db
```

### GitHub Secrets

Required secrets in GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PULUMI_ACCESS_TOKEN`

## API Endpoints

```bash
# Health check
curl http://<alb-url>/health

# API documentation
open http://<alb-url>/docs

# OpenAPI schema
curl http://<alb-url>/openapi.json

# Metrics
curl http://<alb-url>/metrics

# Prometheus
open http://<alb-url>/prometheus

# Grafana
open http://<alb-url>/grafana
```

## Troubleshooting Commands

```bash
# Check ECS task status
aws ecs describe-tasks \
  --cluster fastapi-app-cluster \
  --tasks $(aws ecs list-tasks --cluster fastapi-app-cluster --query 'taskArns[0]' --output text)

# Get task logs
TASK_ID=$(aws ecs list-tasks --cluster fastapi-app-cluster --query 'taskArns[0]' --output text | cut -d'/' -f3)
aws logs get-log-events \
  --log-group-name /aws/ecs/fastapi-app-logs \
  --log-stream-name fastapi/fastapi/$TASK_ID

# Check security group rules
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=fastapi-app-*"

# Test database connection from local
psql postgresql://dbadmin:pass@<rds-endpoint>:5432/fastapi_db

# Check ALB health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups --query 'TargetGroups[?TargetGroupName==`fastapi-app-fastapi-tg`].TargetGroupArn' --output text)

# View ECS service events
aws ecs describe-services \
  --cluster fastapi-app-cluster \
  --services fastapi-app-service \
  --query 'services[0].events[:5]'
```

## Performance Testing

```bash
# Install tools
pip install locust httpx

# Simple load test with curl
for i in {1..100}; do
  curl -s http://<alb-url>/health > /dev/null &
done
wait

# Apache Bench
ab -n 1000 -c 10 http://<alb-url>/health

# Locust (create locustfile.py first)
locust -f locustfile.py --host=http://<alb-url>
```

## Database Operations

```bash
# Connect to RDS
psql postgresql://dbadmin:pass@<rds-endpoint>:5432/fastapi_db

# Backup database
pg_dump -h <rds-endpoint> -U dbadmin -d fastapi_db > backup.sql

# Restore database
psql -h <rds-endpoint> -U dbadmin -d fastapi_db < backup.sql

# Run migration
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "add new table"

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## Cost Optimization

```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Stop ECS service (save costs)
aws ecs update-service \
  --cluster fastapi-app-cluster \
  --service fastapi-app-service \
  --desired-count 0

# Stop RDS instance
aws rds stop-db-instance \
  --db-instance-identifier fastapi-app-postgres

# Delete unused ECR images
aws ecr batch-delete-image \
  --repository-name fastapi-app-repo \
  --image-ids imageTag=old-tag
```

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Pulumi
alias pup='cd infra && pulumi up'
alias ppr='cd infra && pulumi preview'
alias pout='cd infra && pulumi stack output'

# Docker Compose
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'

# AWS ECS
alias ecs-tasks='aws ecs list-tasks --cluster fastapi-app-cluster'
alias ecs-logs='aws logs tail /aws/ecs/fastapi-app-logs --follow'
alias ecs-deploy='aws ecs update-service --cluster fastapi-app-cluster --service fastapi-app-service --force-new-deployment'

# Testing
alias test='pytest -v'
alias testcov='pytest --cov=app --cov-report=html'
```

## Resource Limits

### Free Tier Eligible Resources
- RDS: db.t3.micro (750 hours/month)
- ECS: Fargate 20GB storage, 10GB data transfer
- ECR: 500MB storage
- ALB: 750 hours/month (first year only)
- CloudWatch: 10 custom metrics, 5GB logs

### Recommended Production Sizes
- RDS: db.t3.small or larger
- ECS Task: 512 CPU, 1024 Memory (minimum)
- ECS Service: 2+ tasks for high availability
- ALB: Enable multi-AZ

## Security Checklist

- [ ] RDS in private subnet
- [ ] Security groups properly configured
- [ ] Secrets stored in AWS Secrets Manager or Pulumi config
- [ ] SSL/TLS enabled on ALB
- [ ] IAM roles follow least privilege
- [ ] Enable RDS encryption
- [ ] Enable EFS encryption
- [ ] Regular security patches
- [ ] Enable AWS CloudTrail
- [ ] Set up AWS Config rules
