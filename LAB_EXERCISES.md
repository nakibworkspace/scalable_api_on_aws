# Hands-On Lab Exercises

## Part 1: Infrastructure & Deployment

### Exercise 1: Local Development Setup (30 minutes)

**Objective**: Set up and run the complete application stack locally.

**Tasks**:
1. Clone the repository and install dependencies
2. Start all services with Docker Compose
3. Verify each service is running:
   - FastAPI on port 8000
   - PostgreSQL on port 5432
   - Prometheus on port 9090
   - Grafana on port 3000
4. Create a test user via the API
5. Query Prometheus for metrics
6. Create a Grafana dashboard

**Verification**:
```bash
# All services should be healthy
docker-compose ps

# API should respond
curl http://localhost:8000/health

# Database should be accessible
docker-compose exec postgres psql -U user -d appdb -c "SELECT 1;"
```

**Deliverable**: Screenshot of all services running and Grafana dashboard

---

### Exercise 2: AWS Infrastructure Deployment (45 minutes)

**Objective**: Deploy the complete infrastructure to AWS using Pulumi.

**Tasks**:
1. Install and configure Pulumi CLI
2. Create a new Pulumi stack
3. Configure AWS credentials
4. Set required configuration values:
   - AWS region
   - Database password
   - Database name
5. Preview infrastructure changes
6. Deploy to AWS
7. Verify all resources are created

**Verification**:
```bash
# Check stack outputs
cd infra
pulumi stack output

# Verify resources in AWS
aws ecs list-clusters
aws rds describe-db-instances
aws ecr describe-repositories
```

**Deliverable**: 
- Pulumi stack output showing all resources
- AWS Console screenshots of ECS cluster, RDS instance, and ECR repository

---

### Exercise 3: Docker Image Build & Push to ECR (30 minutes)

**Objective**: Build a Docker image and push it to AWS ECR.

**Tasks**:
1. Review the Dockerfile and understand multi-stage build
2. Build the Docker image locally
3. Test the image locally
4. Authenticate with AWS ECR
5. Tag the image for ECR
6. Push the image to ECR
7. Verify the image in ECR

**Verification**:
```bash
# Image should be in ECR
aws ecr list-images --repository-name fastapi-app-repo

# Image should have correct tags
aws ecr describe-images --repository-name fastapi-app-repo
```

**Deliverable**: 
- Docker build output
- ECR repository showing the pushed image

---

### Exercise 4: CI/CD Pipeline Configuration (45 minutes)

**Objective**: Set up GitHub Actions for automated testing and deployment.

**Tasks**:
1. Configure GitHub repository secrets:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - PULUMI_ACCESS_TOKEN
2. Review the CI pipeline (.github/workflows/ci.yml)
3. Review the deployment pipeline (.github/workflows/deploy.yml)
4. Make a code change and push to trigger CI
5. Merge to main to trigger deployment
6. Monitor the deployment in GitHub Actions
7. Verify the application is deployed

**Verification**:
```bash
# Get application URL
cd infra
APP_URL=$(pulumi stack output app_url)

# Test deployed application
curl $APP_URL/health
curl $APP_URL/docs
```

**Deliverable**: 
- GitHub Actions workflow run showing successful deployment
- Application responding at the ALB URL

---

### Exercise 5: Database Migrations (30 minutes)

**Objective**: Create and apply database migrations using Alembic.

**Tasks**:
1. Create a new model in `app/models.py`:
```python
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. Generate migration:
```bash
alembic revision --autogenerate -m "add products table"
```

3. Review the generated migration
4. Apply migration locally
5. Verify table was created
6. Push changes to trigger CI/CD
7. Verify migration runs in production

**Verification**:
```bash
# Check migration history
alembic history

# Verify table exists
docker-compose exec postgres psql -U user -d appdb -c "\dt"
```

**Deliverable**: 
- Migration file
- Database schema showing new table

---

## Part 2: Monitoring & Observability

### Exercise 6: Prometheus Metrics (30 minutes)

**Objective**: Implement custom metrics and query them in Prometheus.

**Tasks**:
1. Add custom metrics to FastAPI:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
```

2. Instrument endpoints
3. Deploy changes
4. Access Prometheus UI
5. Query metrics:
   - `rate(api_requests_total[5m])`
   - `histogram_quantile(0.95, api_request_duration_seconds)`
6. Create alerts

**Verification**:
- Metrics visible in Prometheus
- Queries return data
- Alerts configured

**Deliverable**: 
- Screenshot of Prometheus queries
- Alert rules configuration

---

### Exercise 7: Grafana Dashboard (45 minutes)

**Objective**: Create a comprehensive monitoring dashboard in Grafana.

**Tasks**:
1. Access Grafana UI
2. Add Prometheus datasource
3. Create a new dashboard with panels:
   - Request rate (requests/second)
   - Error rate (4xx, 5xx)
   - Latency (p50, p95, p99)
   - Active connections
   - Database query time
   - ECS task count
4. Add variables for filtering
5. Set up dashboard refresh
6. Export dashboard JSON

**Verification**:
- Dashboard shows real-time data
- All panels display correctly
- Variables work

**Deliverable**: 
- Dashboard JSON file
- Screenshot of complete dashboard

---

### Exercise 8: CloudWatch Logs & Alarms (30 minutes)

**Objective**: Set up CloudWatch monitoring and alerting.

**Tasks**:
1. View ECS task logs in CloudWatch
2. Create log insights queries:
   - Error count by hour
   - Slowest endpoints
   - Failed requests
3. Create CloudWatch alarms:
   - High CPU utilization (>80%)
   - High memory utilization (>80%)
   - Error rate threshold
   - RDS connection count
4. Test alarms by generating load

**Verification**:
```bash
# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# List alarms
aws cloudwatch describe-alarms
```

**Deliverable**: 
- CloudWatch Insights queries
- Alarm configurations
- Screenshot of triggered alarm

---

## Part 3: Advanced Features

### Exercise 9: Auto-Scaling Configuration (45 minutes)

**Objective**: Implement auto-scaling for ECS service.

**Tasks**:
1. Add auto-scaling configuration to Pulumi:
```python
scaling_target = aws.appautoscaling.Target(
    f"{app_name}-scaling-target",
    max_capacity=10,
    min_capacity=1,
    resource_id=pulumi.Output.concat("service/", cluster.name, "/", service.name),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

cpu_scaling = aws.appautoscaling.Policy(
    f"{app_name}-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=scaling_target.resource_id,
    scalable_dimension=scaling_target.scalable_dimension,
    service_namespace=scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration={
        "predefined_metric_specification": {
            "predefined_metric_type": "ECSServiceAverageCPUUtilization",
        },
        "target_value": 70.0,
    },
)
```

2. Deploy auto-scaling configuration
3. Generate load to trigger scaling
4. Monitor scaling events
5. Verify tasks scale up and down

**Verification**:
```bash
# Check scaling policies
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs

# Monitor task count
watch -n 5 'aws ecs describe-services \
  --cluster fastapi-app-cluster \
  --services fastapi-app-service \
  --query "services[0].desiredCount"'
```

**Deliverable**: 
- Auto-scaling configuration
- Screenshots showing scaling events

---

### Exercise 10: Load Testing (30 minutes)

**Objective**: Perform load testing and analyze results.

**Tasks**:
1. Install load testing tool:
```bash
pip install locust
```

2. Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)
    def list_items(self):
        self.client.get("/items")
```

3. Run load test:
```bash
locust -f locustfile.py --host=http://<alb-url>
```

4. Monitor in Grafana
5. Observe auto-scaling
6. Analyze results

**Verification**:
- Load test completes successfully
- Auto-scaling triggers
- No errors during load

**Deliverable**: 
- Locust test results
- Grafana dashboard during load test

---

### Exercise 11: SSL/TLS Configuration (45 minutes)

**Objective**: Secure the application with SSL/TLS.

**Tasks**:
1. Register a domain (or use existing)
2. Request ACM certificate:
```bash
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS
```

3. Validate certificate via DNS
4. Add HTTPS listener to Pulumi:
```python
certificate_arn = config.get("certificate-arn")

https_listener = aws.lb.Listener(
    f"{app_name}-https-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=certificate_arn,
    default_actions=[{
        "type": "forward",
        "target_group_arn": fastapi_tg.arn,
    }],
)

# Redirect HTTP to HTTPS
http_redirect = aws.lb.Listener(
    f"{app_name}-http-redirect",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[{
        "type": "redirect",
        "redirect": {
            "protocol": "HTTPS",
            "port": "443",
            "status_code": "HTTP_301",
        },
    }],
)
```

5. Configure Route 53 DNS
6. Deploy changes
7. Test HTTPS access

**Verification**:
```bash
# Test HTTPS
curl -I https://yourdomain.com/health

# Verify redirect
curl -I http://yourdomain.com/health
```

**Deliverable**: 
- Working HTTPS endpoint
- HTTP to HTTPS redirect

---

### Exercise 12: Blue/Green Deployment (60 minutes)

**Objective**: Implement blue/green deployment strategy.

**Tasks**:
1. Update ECS service configuration:
```python
service = aws.ecs.Service(
    f"{app_name}-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=2,
    deployment_configuration={
        "deployment_circuit_breaker": {
            "enable": True,
            "rollback": True,
        },
        "maximum_percent": 200,
        "minimum_healthy_percent": 100,
    },
)
```

2. Make a visible change to the application
3. Deploy new version
4. Monitor deployment:
   - Old tasks running
   - New tasks starting
   - Health checks passing
   - Traffic shifting
   - Old tasks draining
5. Verify zero downtime
6. Test rollback scenario

**Verification**:
```bash
# Monitor deployment
aws ecs describe-services \
  --cluster fastapi-app-cluster \
  --services fastapi-app-service \
  --query 'services[0].deployments'

# Continuous health check during deployment
while true; do
  curl -s http://<alb-url>/health || echo "FAILED"
  sleep 1
done
```

**Deliverable**: 
- Deployment logs showing blue/green process
- Proof of zero downtime

---

### Exercise 13: End-to-End Testing (45 minutes)

**Objective**: Implement comprehensive E2E tests.

**Tasks**:
1. Create E2E test suite:
```python
# tests/e2e/test_user_flow.py
import pytest
import httpx

@pytest.mark.asyncio
async def test_complete_user_flow():
    async with httpx.AsyncClient(base_url=API_URL) as client:
        # Create user
        response = await client.post("/users", json={
            "email": "test@example.com",
            "name": "Test User"
        })
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Get user
        response = await client.get(f"/users/{user_id}")
        assert response.status_code == 200
        
        # Update user
        response = await client.put(f"/users/{user_id}", json={
            "name": "Updated Name"
        })
        assert response.status_code == 200
        
        # Delete user
        response = await client.delete(f"/users/{user_id}")
        assert response.status_code == 204
```

2. Add E2E tests to CI/CD pipeline
3. Run tests against staging environment
4. Implement test data cleanup
5. Add test reporting

**Verification**:
```bash
# Run E2E tests
pytest tests/e2e/ -v --html=report.html
```

**Deliverable**: 
- E2E test suite
- Test report
- CI/CD integration

---

### Exercise 14: Database Backup & Restore (30 minutes)

**Objective**: Implement database backup and restore procedures.

**Tasks**:
1. Create manual RDS snapshot:
```bash
aws rds create-db-snapshot \
  --db-instance-identifier fastapi-app-postgres \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)
```

2. Configure automated backups in Pulumi:
```python
rds_instance = aws.rds.Instance(
    f"{app_name}-postgres",
    # ... existing config ...
    backup_retention_period=7,
    backup_window="03:00-04:00",
    maintenance_window="Mon:04:00-Mon:05:00",
    copy_tags_to_snapshot=True,
)
```

3. Test restore from snapshot:
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier fastapi-app-postgres-restored \
  --db-snapshot-identifier manual-backup-20240101
```

4. Verify restored database
5. Document backup procedures

**Verification**:
```bash
# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier fastapi-app-postgres

# Check backup status
aws rds describe-db-instances \
  --db-instance-identifier fastapi-app-postgres \
  --query 'DBInstances[0].LatestRestorableTime'
```

**Deliverable**: 
- Backup procedure documentation
- Successful restore test

---

### Exercise 15: Cost Optimization (30 minutes)

**Objective**: Analyze and optimize AWS costs.

**Tasks**:
1. Review current costs:
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

2. Implement cost optimizations:
   - ECR lifecycle policy (keep last 10 images)
   - RDS instance right-sizing
   - ECS task right-sizing
   - CloudWatch log retention
   - Unused resource cleanup

3. Set up cost alerts:
```bash
aws budgets create-budget \
  --account-id <account-id> \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

4. Document cost-saving measures

**Verification**:
- Cost report showing optimizations
- Budget alerts configured

**Deliverable**: 
- Cost analysis report
- Optimization recommendations

---

## Bonus Challenges

### Challenge 1: Multi-Region Deployment
Deploy the application to multiple AWS regions with Route 53 failover.

### Challenge 2: Feature Flags
Implement feature flags using Unleash or similar service.

### Challenge 3: API Rate Limiting
Add rate limiting to protect against abuse.

### Challenge 4: Secrets Management
Migrate secrets to AWS Secrets Manager.

### Challenge 5: Canary Deployments
Implement canary deployment with gradual traffic shifting.

---

## Assessment Criteria

Each exercise will be evaluated on:
- **Completeness** (40%): All tasks completed
- **Correctness** (30%): Solution works as expected
- **Documentation** (20%): Clear documentation and screenshots
- **Best Practices** (10%): Follows security and operational best practices

## Submission

Submit your work including:
1. All code changes (GitHub repository)
2. Screenshots of working deployments
3. Configuration files
4. Documentation of any issues encountered
5. Lessons learned summary

Good luck! 🚀
