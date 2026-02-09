# Deployment Guide

## Part 1: Initial Setup and Deployment

### Prerequisites Setup

1. **Install Required Tools**:
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install Pulumi
curl -fsSL https://get.pulumi.com | sh

# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop
```

2. **Configure AWS Credentials**:
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

3. **Verify Setup**:
```bash
aws sts get-caller-identity
pulumi version
docker --version
```

### Local Development and Testing

1. **Clone Repository**:
```bash
git clone <your-repo-url>
cd <your-repo>
```

2. **Create Environment File**:
```bash
cp .env.example .env
# Edit .env with your values
```

3. **Start Local Stack**:
```bash
docker-compose up --build
```

4. **Run Tests**:
```bash
# In another terminal
curl http://localhost:8000/health
curl http://localhost:8000/
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Test item"}'
```

5. **Access Services**:
- FastAPI: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### AWS Infrastructure Deployment

1. **Initialize Pulumi**:
```bash
cd infra
pulumi login
pulumi stack init production
pulumi config set aws:region us-east-1
```

2. **Set Configuration**:
```bash
# Set database password (stored encrypted)
pulumi config set --secret db-password "YourSecurePassword123!"

# Optional: Set custom app name
pulumi config set app-name "my-fastapi-app"
```

3. **Preview Infrastructure**:
```bash
pulumi preview
```

4. **Deploy Infrastructure**:
```bash
pulumi up
# Review the changes
# Type "yes" to confirm
```

5. **Save Outputs**:
```bash
pulumi stack output app_url > ../deployment-url.txt
pulumi stack output ecr_repository_url > ../ecr-url.txt
```

### Build and Deploy Application

1. **Authenticate with ECR**:
```bash
cd ..
ECR_URL=$(cat ecr-url.txt)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL
```

2. **Build Docker Image**:
```bash
docker build -t fastapi-app .
```

3. **Tag and Push**:
```bash
docker tag fastapi-app:latest $ECR_URL:latest
docker tag fastapi-app:latest $ECR_URL:v1.0.0
docker push $ECR_URL:latest
docker push $ECR_URL:v1.0.0
```

4. **Force ECS Service Update**:
```bash
CLUSTER_NAME=$(cd infra && pulumi stack output cluster_name)
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service fastapi-app-service \
  --force-new-deployment
```

5. **Wait for Deployment**:
```bash
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services fastapi-app-service
```

6. **Test Deployment**:
```bash
APP_URL=$(cat deployment-url.txt)
curl $APP_URL/health
curl $APP_URL/
```

### Setup GitHub Actions CI/CD

1. **Add GitHub Secrets**:

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `PULUMI_ACCESS_TOKEN`: Get from https://app.pulumi.com/account/tokens
- `DB_PASSWORD`: Your database password
- `DB_HOST`: localhost (for ECS tasks)
- `DB_USER`: appuser
- `DB_NAME`: appdb

2. **Push Code to GitHub**:
```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

3. **Verify CI/CD**:
- Check Actions tab in GitHub
- CI pipeline should run automatically
- After CI passes, deployment pipeline runs

---

## Part 2: Advanced Features

### Database Migrations

1. **Initialize Alembic**:
```bash
alembic init migrations
```

2. **Create First Migration**:
```bash
alembic revision --autogenerate -m "Initial schema"
```

3. **Apply Migrations Locally**:
```bash
docker-compose up -d postgres
export POSTGRES_HOST=localhost
alembic upgrade head
```

4. **Apply Migrations in Production**:
```bash
# Get database endpoint from ECS task
# Migrations run automatically in CI/CD pipeline
```

### Monitoring Configuration

1. **Configure Prometheus**:
```bash
# Edit monitoring/prometheus.yml
# Add custom scrape configs
```

2. **Setup Grafana**:
```bash
# Access Grafana at http://<alb-url>/grafana
# Login: admin/admin
# Add Prometheus datasource: http://localhost:9090
# Import dashboard from monitoring/grafana-dashboard.json
```

3. **Create Custom Dashboard**:
- Add panels for request rate, latency, error rate
- Set up alerts for high error rates
- Configure notification channels

### SSL/TLS Setup

1. **Request Certificate in ACM**:
```bash
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

2. **Update Pulumi Code**:
```python
# Add HTTPS listener to ALB
https_listener = aws.lb.Listener(
    f"{app_name}-https-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn="<your-certificate-arn>",
    default_actions=[...],
)
```

3. **Deploy Changes**:
```bash
cd infra
pulumi up
```

### Custom Domain Setup

1. **Create Hosted Zone in Route 53**:
```bash
aws route53 create-hosted-zone \
  --name yourdomain.com \
  --caller-reference $(date +%s)
```

2. **Add DNS Record**:
```python
# In infra/__main__.py
zone = aws.route53.get_zone(name="yourdomain.com")
record = aws.route53.Record(
    "app-record",
    zone_id=zone.id,
    name="api.yourdomain.com",
    type="A",
    aliases=[aws.route53.RecordAliasArgs(
        name=alb.dns_name,
        zone_id=alb.zone_id,
        evaluate_target_health=True,
    )],
)
```

### Auto-Scaling Configuration

1. **Add Auto-Scaling Target**:
```python
# In infra/__main__.py
scaling_target = aws.appautoscaling.Target(
    f"{app_name}-scaling-target",
    max_capacity=10,
    min_capacity=1,
    resource_id=pulumi.Output.concat(
        "service/", cluster.name, "/", service.name
    ),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)
```

2. **Add Scaling Policy**:
```python
scaling_policy = aws.appautoscaling.Policy(
    f"{app_name}-scaling-policy",
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

### Feature Flags with Unleash

1. **Deploy Unleash**:
```bash
docker run -d -p 4242:4242 \
  --name unleash \
  unleashorg/unleash-server
```

2. **Add to FastAPI**:
```python
from unleash import UnleashClient

unleash_client = UnleashClient(
    url="http://unleash:4242/api",
    app_name="fastapi-app",
    custom_headers={'Authorization': 'your-api-key'},
)

@app.get("/feature")
def check_feature():
    if unleash_client.is_enabled("new_feature"):
        return {"feature": "enabled"}
    return {"feature": "disabled"}
```

### End-to-End Testing

1. **Create E2E Test Suite**:
```python
# tests/e2e/test_api.py
import requests
import pytest

BASE_URL = "http://localhost:8000"

def test_full_workflow():
    # Create item
    response = requests.post(
        f"{BASE_URL}/items",
        json={"name": "E2E Test", "description": "Test"}
    )
    assert response.status_code == 200
    item_id = response.json()["id"]
    
    # Get item
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "E2E Test"
```

2. **Run E2E Tests**:
```bash
pytest tests/e2e/ -v
```

### Continuous Deployment

1. **Add Approval Gate**:
```yaml
# In .github/workflows/deploy.yml
deploy:
  environment:
    name: production
    url: ${{ steps.deploy.outputs.url }}
  # Requires manual approval in GitHub
```

2. **Add Rollback Strategy**:
```bash
# Save previous task definition
aws ecs describe-task-definition \
  --task-definition fastapi-app-task \
  --query 'taskDefinition' > previous-task-def.json

# Rollback if needed
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service fastapi-app-service \
  --task-definition <previous-revision>
```

## Troubleshooting

### Common Issues

1. **ECS Task Fails to Start**:
```bash
# Check task logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Check task stopped reason
aws ecs describe-tasks \
  --cluster $CLUSTER_NAME \
  --tasks <task-id>
```

2. **Database Connection Issues**:
```bash
# Verify security groups allow traffic
# Check environment variables in task definition
# Test from within ECS task
aws ecs execute-command \
  --cluster $CLUSTER_NAME \
  --task <task-id> \
  --container fastapi \
  --interactive \
  --command "/bin/sh"
```

3. **Load Balancer Health Checks Failing**:
```bash
# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Verify health check path returns 200
curl http://<task-ip>:8000/health
```

## Cleanup

```bash
# Destroy all AWS resources
cd infra
pulumi destroy

# Remove local resources
docker-compose down -v
docker system prune -a
```

## Cost Optimization

- Use Fargate Spot for non-production environments
- Enable ECS container insights only when needed
- Use lifecycle policies for ECR to delete old images
- Set up budget alerts in AWS
- Consider reserved capacity for production

## Security Best Practices

- Rotate database passwords regularly
- Use AWS Secrets Manager for sensitive data
- Enable VPC Flow Logs
- Implement WAF rules on ALB
- Regular security scanning of Docker images
- Use least privilege IAM policies
