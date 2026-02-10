# Scalable FastAPI on AWS - Complete Lab Guide

## Overview

This hands-on lab teaches you how to build and deploy a production-ready, scalable FastAPI application on AWS using modern DevOps practices.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Application Load    │
              │     Balancer (ALB)   │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐    ┌────────────┐   ┌─────────┐
    │FastAPI │    │ Prometheus │   │ Grafana │
    │  ECS   │    │    ECS     │   │   ECS   │
    └───┬────┘    └─────┬──────┘   └────┬────┘
        │               │               │
        │               └───────┬───────┘
        │                       │
        ▼                       ▼
   ┌─────────┐            ┌─────────┐
   │   RDS   │            │   EFS   │
   │Postgres │            │ Storage │
   └─────────┘            └─────────┘
```

## Part 1: Infrastructure Setup & CI/CD Pipeline

### Learning Objectives
- Structure a FastAPI application for production
- Configure GitHub Actions CI/CD pipeline
- Manage AWS infrastructure with Pulumi (IaC)
- Build and push Docker images to AWS ECR
- Deploy containerized applications to AWS ECS
- Set up monitoring with Prometheus and Grafana

### Prerequisites
- AWS Account with appropriate permissions
- GitHub account
- Pulumi account (free tier)
- Docker installed locally
- Python 3.11+
- AWS CLI configured

---

## Lab 1: Project Setup & Local Development

### Step 1: Clone and Explore the Repository

```bash
git clone <your-repo-url>
cd <repo-name>
```

### Step 2: Understand the Project Structure

```
.
├── app/                    # FastAPI application
│   ├── main.py            # Main application entry
│   ├── config.py          # Configuration management
│   ├── database.py        # Database connection
│   └── requirements.txt   # Python dependencies
├── infra/                 # Pulumi infrastructure code
│   ├── __main__.py        # Infrastructure definition
│   └── requirements.txt   # Pulumi dependencies
├── .github/workflows/     # CI/CD pipelines
│   ├── ci.yml            # Test & quality checks
│   ├── deploy.yml        # AWS deployment
│   └── e2e-tests.yml     # End-to-end tests
├── monitoring/            # Monitoring configuration
│   ├── prometheus.yml    # Prometheus config
│   └── grafana-*.yml     # Grafana datasources
├── migrations/            # Database migrations
└── docker-compose.yml     # Local development
```

### Step 3: Set Up Local Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt

# Copy environment file
cp .env.example .env
```

### Step 4: Run Locally with Docker Compose

```bash
# Start all services (FastAPI, Postgres, Prometheus, Grafana)
docker-compose up -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f fastapi
```

### Step 5: Test Local Application

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Prometheus metrics
open http://localhost:9090

# Grafana dashboard
open http://localhost:3000  # admin/admin
```

---

## Lab 2: AWS Infrastructure with Pulumi

### Step 1: Install Pulumi

```bash
# macOS
brew install pulumi/tap/pulumi

# Linux
curl -fsSL https://get.pulumi.com | sh

# Verify installation
pulumi version
```

### Step 2: Configure Pulumi

```bash
# Login to Pulumi (creates free account)
pulumi login

# Navigate to infrastructure directory
cd infra

# Initialize stack
pulumi stack init production

# Set AWS region
pulumi config set aws:region us-east-1

# Set database password (encrypted)
pulumi config set --secret db-password YourSecurePassword123!

# Optional: customize database settings
pulumi config set db-username dbadmin
pulumi config set db-name fastapi_db
```

### Step 3: Review Infrastructure Code

Open `infra/__main__.py` and review the resources:

1. **VPC & Networking**: Private/public subnets, NAT gateway
2. **Security Groups**: ALB, ECS tasks, RDS, EFS
3. **RDS PostgreSQL**: Managed database instance
4. **ECS Cluster**: Container orchestration
5. **ECR Repository**: Docker image registry
6. **EFS**: Persistent storage for Prometheus/Grafana
7. **Application Load Balancer**: Traffic distribution
8. **IAM Roles**: Task execution permissions

### Step 4: Preview Infrastructure Changes

```bash
# Dry run - see what will be created
pulumi preview

# Review the output:
# - ~50 resources will be created
# - VPC, subnets, security groups
# - RDS instance
# - ECS cluster and services
# - ECR repository
# - Load balancer
```

### Step 5: Deploy Infrastructure

```bash
# Deploy to AWS (takes ~10-15 minutes)
pulumi up

# Type 'yes' to confirm

# Wait for completion...
# Note the outputs:
# - ecr_repository_url
# - rds_endpoint
# - app_url
```

### Step 6: Verify AWS Resources

```bash
# Check ECR repository
aws ecr describe-repositories --region us-east-1

# Check ECS cluster
aws ecs list-clusters --region us-east-1

# Check RDS instance
aws rds describe-db-instances --region us-east-1

# Get stack outputs
pulumi stack output
```

---

## Lab 3: Docker Image & ECR

### Step 1: Review Dockerfile

```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder
# ... dependencies installation

FROM python:3.11-slim
# ... runtime setup
```

### Step 2: Build Docker Image Locally

```bash
# Build image
docker build -t fastapi-app:local .

# Test image locally
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  fastapi-app:local

# Verify
curl http://localhost:8000/health
```

### Step 3: Push to ECR Manually (Optional)

```bash
# Get ECR repository URL
ECR_URL=$(cd infra && pulumi stack output ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Tag image
docker tag fastapi-app:local $ECR_URL:manual

# Push to ECR
docker push $ECR_URL:manual

# Verify in AWS Console or CLI
aws ecr list-images --repository-name fastapi-app-repo --region us-east-1
```

---

## Lab 4: GitHub Actions CI/CD Pipeline

### Step 1: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
PULUMI_ACCESS_TOKEN=<your-pulumi-token>
```

To get Pulumi token:
```bash
pulumi login
# Visit: https://app.pulumi.com/<your-org>/settings/tokens
```

### Step 2: Review CI Pipeline

Open `.github/workflows/ci.yml`:

```yaml
# Triggers on every push and PR
# Jobs:
# 1. Lint (ruff)
# 2. Type check (mypy)
# 3. Unit tests (pytest)
# 4. Security scan (bandit)
# 5. Code coverage
```

### Step 3: Review Deployment Pipeline

Open `.github/workflows/deploy.yml`:

```yaml
# Triggers after successful CI on main branch
# Steps:
# 1. Build Docker image
# 2. Push to ECR
# 3. Deploy infrastructure with Pulumi
# 4. Run database migrations
# 5. Update ECS service
# 6. Wait for stability
```

### Step 4: Trigger First Deployment

```bash
# Make a change
echo "# Update" >> README.md

# Commit and push
git add .
git commit -m "feat: trigger first deployment"
git push origin main

# Watch GitHub Actions
# Go to: https://github.com/<your-repo>/actions
```

### Step 5: Monitor Deployment

```bash
# Watch ECS service
aws ecs describe-services \
  --cluster fastapi-app-cluster \
  --services fastapi-app-service \
  --region us-east-1

# Check task status
aws ecs list-tasks \
  --cluster fastapi-app-cluster \
  --region us-east-1

# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow --region us-east-1
```

---

## Lab 5: Database Migrations with Alembic

### Step 1: Create First Migration

```bash
# Generate migration
alembic revision --autogenerate -m "create users table"

# Review generated migration in migrations/versions/
```

### Step 2: Apply Migration Locally

```bash
# Run migration
alembic upgrade head

# Check database
docker-compose exec postgres psql -U user -d appdb -c "\dt"
```

### Step 3: Migrations in CI/CD

The deployment pipeline automatically runs migrations:

```yaml
- name: Run database migrations
  run: |
    pip install alembic psycopg2-binary
    alembic upgrade head
  env:
    DATABASE_URL: ${{ env.DATABASE_URL }}
```

### Step 4: Rollback Strategy

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>

# View history
alembic history
```

---

## Lab 6: Monitoring with Prometheus & Grafana

### Step 1: Access Prometheus

```bash
# Get ALB URL
cd infra
pulumi stack output prometheus_url

# Open in browser
# http://<alb-dns>/prometheus
```

### Step 2: Explore Metrics

In Prometheus UI:
- Go to Graph
- Try queries:
  - `up` - Service health
  - `http_requests_total` - Request count
  - `http_request_duration_seconds` - Latency

### Step 3: Access Grafana

```bash
# Get Grafana URL
pulumi stack output grafana_url

# Open in browser
# http://<alb-dns>/grafana
# Login: admin/admin
```

### Step 4: Create Dashboard

1. Add Prometheus datasource (already configured)
2. Create new dashboard
3. Add panels:
   - Request rate: `rate(http_requests_total[5m])`
   - Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
   - Latency: `histogram_quantile(0.95, http_request_duration_seconds)`

---

## Part 2: Advanced Features

## Lab 7: End-to-End Testing

### Step 1: Review E2E Test Structure

```python
# tests/e2e/test_api.py
def test_full_user_flow():
    # Create user
    # Login
    # Perform operations
    # Verify database state
```

### Step 2: Run E2E Tests Locally

```bash
# Start services
docker-compose up -d

# Run E2E tests
pytest tests/e2e/ -v

# With coverage
pytest tests/e2e/ --cov=app
```

### Step 3: E2E Tests in CI/CD

The pipeline runs E2E tests against a staging environment:

```yaml
# .github/workflows/e2e-tests.yml
- name: Run E2E tests
  run: pytest tests/e2e/ -v
  env:
    API_URL: ${{ steps.deploy.outputs.url }}
```

---

## Lab 8: Auto-Scaling Configuration

### Step 1: Add Auto-Scaling to Pulumi

```python
# In infra/__main__.py, add after ECS service:

# Auto-scaling target
scaling_target = aws.appautoscaling.Target(
    f"{app_name}-scaling-target",
    max_capacity=10,
    min_capacity=1,
    resource_id=pulumi.Output.concat("service/", cluster.name, "/", service.name),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

# CPU-based scaling policy
aws.appautoscaling.Policy(
    f"{app_name}-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=scaling_target.resource_id,
    scalable_dimension=scaling_target.scalable_dimension,
    service_namespace=scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
        predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
            predefined_metric_type="ECSServiceAverageCPUUtilization",
        ),
        target_value=70.0,
    ),
)
```

### Step 2: Deploy Auto-Scaling

```bash
cd infra
pulumi up
```

### Step 3: Load Test

```bash
# Install load testing tool
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://<alb-url>
```

---

## Lab 9: SSL/TLS with AWS Certificate Manager

### Step 1: Request Certificate

```bash
# Request certificate for your domain
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

### Step 2: Add HTTPS Listener to Pulumi

```python
# Add after HTTP listener in infra/__main__.py

certificate_arn = config.get("certificate-arn")

if certificate_arn:
    https_listener = aws.lb.Listener(
        f"{app_name}-https-listener",
        load_balancer_arn=alb.arn,
        port=443,
        protocol="HTTPS",
        certificate_arn=certificate_arn,
        default_actions=[
            aws.lb.ListenerDefaultActionArgs(
                type="forward",
                target_group_arn=fastapi_tg.arn,
            ),
        ],
    )
```

### Step 3: Configure Domain

```bash
# Set certificate ARN
pulumi config set certificate-arn arn:aws:acm:...

# Deploy
pulumi up
```

---

## Lab 10: Continuous Deployment

### Step 1: Enable Blue/Green Deployment

```python
# Update ECS service in infra/__main__.py

service = aws.ecs.Service(
    f"{app_name}-service",
    # ... existing config ...
    deployment_configuration=aws.ecs.ServiceDeploymentConfigurationArgs(
        deployment_circuit_breaker=aws.ecs.ServiceDeploymentConfigurationDeploymentCircuitBreakerArgs(
            enable=True,
            rollback=True,
        ),
        maximum_percent=200,
        minimum_healthy_percent=100,
    ),
)
```

### Step 2: Add Deployment Approval

```yaml
# In .github/workflows/deploy.yml

deploy-production:
  needs: deploy-staging
  environment:
    name: production
    url: ${{ steps.deploy.outputs.url }}
  steps:
    # ... deployment steps
```

---

## Troubleshooting

### Common Issues

1. **ECS Task Fails to Start**
```bash
# Check task logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Check task definition
aws ecs describe-task-definition --task-definition fastapi-app-task
```

2. **Database Connection Issues**
```bash
# Verify security group rules
aws ec2 describe-security-groups --group-ids <ecs-sg-id>

# Test from ECS task
aws ecs execute-command --cluster fastapi-app-cluster \
  --task <task-id> --interactive --command "/bin/sh"
```

3. **Load Balancer Health Checks Failing**
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>
```

---

## Cleanup

```bash
# Destroy all AWS resources
cd infra
pulumi destroy

# Remove stack
pulumi stack rm production

# Clean local Docker
docker-compose down -v
```

---

## Next Steps

1. Implement feature flags with Unleash
2. Add API rate limiting
3. Set up CloudWatch alarms
4. Implement backup strategies
5. Add multi-region deployment
6. Implement canary deployments

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pulumi AWS Guide](https://www.pulumi.com/docs/clouds/aws/)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
