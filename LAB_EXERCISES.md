# Hands-On Lab Exercises

Complete these exercises to master scalable FastAPI deployment on AWS.

## Part 1: Foundation & Initial Deployment

### Exercise 1.1: Local Development Setup (30 minutes)

**Objective**: Get the application running locally with all services.

**Tasks**:
1. Start the Docker Compose stack
2. Verify all 4 services are running (FastAPI, PostgreSQL, Prometheus, Grafana)
3. Test the FastAPI endpoints
4. Create 5 items via the API
5. Query Prometheus for FastAPI metrics
6. View metrics in Grafana

**Verification**:
```bash
# Check all services are healthy
docker-compose ps

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/items

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Verify Grafana datasource
curl -u admin:admin http://localhost:3000/api/datasources
```

**Expected Output**: All services running, API responding, metrics being collected.

---

### Exercise 1.2: Infrastructure Deployment (45 minutes)

**Objective**: Deploy AWS infrastructure using Pulumi.

**Tasks**:
1. Initialize Pulumi stack
2. Configure AWS region and database password
3. Review the infrastructure code in `infra/__main__.py`
4. Run `pulumi preview` and understand what will be created
5. Deploy the infrastructure
6. Document all created resources

**Verification**:
```bash
cd infra
pulumi stack output app_url
pulumi stack output ecr_repository_url

# Verify VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=fastapi-app-vpc*"

# Verify ECS cluster
aws ecs list-clusters
```

**Questions to Answer**:
- How many subnets were created?
- What is the CIDR block of the VPC?
- How many security groups were created?
- What ports are exposed on the ALB?

---

### Exercise 1.3: Container Build & Push (30 minutes)

**Objective**: Build Docker image and push to ECR.

**Tasks**:
1. Authenticate with ECR
2. Build the Docker image locally
3. Tag the image with multiple tags (latest, v1.0.0, git commit hash)
4. Push all tags to ECR
5. Verify images in ECR console

**Verification**:
```bash
# List images in ECR
aws ecr describe-images --repository-name fastapi-repo

# Check image scan results
aws ecr describe-image-scan-findings \
  --repository-name fastapi-repo \
  --image-id imageTag=latest
```

**Challenge**: Optimize the Dockerfile to reduce image size by at least 20%.

---

### Exercise 1.4: CI/CD Pipeline Setup (45 minutes)

**Objective**: Configure GitHub Actions for automated deployment.

**Tasks**:
1. Add required secrets to GitHub repository
2. Push code to trigger CI pipeline
3. Monitor the pipeline execution
4. Fix any failing tests
5. Verify deployment completes successfully

**Verification**:
- CI pipeline passes all tests
- Docker image is built and pushed
- ECS service is updated
- Application is accessible via ALB URL

**Troubleshooting Practice**:
- Intentionally break a test and fix it
- Simulate a failed deployment and rollback

---

## Part 2: Database & Migrations

### Exercise 2.1: Database Schema Design (30 minutes)

**Objective**: Design and implement a database schema.

**Tasks**:
1. Add a new `users` table with fields: id, email, name, created_at
2. Add a foreign key relationship: items.user_id → users.id
3. Create Alembic migration
4. Apply migration locally
5. Test the new schema

**Verification**:
```bash
# Generate migration
alembic revision --autogenerate -m "Add users table"

# Apply migration
alembic upgrade head

# Verify schema
docker-compose exec postgres psql -U user -d appdb -c "\dt"
```

**Challenge**: Add a many-to-many relationship between users and items (favorites).

---

### Exercise 2.2: Migration in CI/CD (30 minutes)

**Objective**: Automate database migrations in the deployment pipeline.

**Tasks**:
1. Update `.github/workflows/deploy.yml` to run migrations
2. Test migration rollback
3. Handle migration failures gracefully
4. Add migration status check endpoint

**Verification**:
- Migrations run automatically on deployment
- Failed migrations don't break the deployment
- Can query current migration version via API

---

## Part 3: Monitoring & Observability

### Exercise 3.1: Custom Metrics (45 minutes)

**Objective**: Add custom business metrics to Prometheus.

**Tasks**:
1. Add a counter for items created
2. Add a gauge for active users
3. Add a histogram for database query duration
4. Expose metrics at `/metrics`
5. Query metrics in Prometheus

**Code Example**:
```python
from prometheus_client import Counter, Gauge, Histogram

items_created = Counter('items_created_total', 'Total items created')
active_users = Gauge('active_users', 'Number of active users')
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')

@app.post("/items")
def create_item(item: ItemCreate):
    items_created.inc()
    # ... rest of code
```

**Verification**:
```bash
# Check metrics
curl http://localhost:8000/metrics | grep items_created

# Query in Prometheus
curl 'http://localhost:9090/api/v1/query?query=items_created_total'
```

---

### Exercise 3.2: Grafana Dashboards (45 minutes)

**Objective**: Create comprehensive monitoring dashboards.

**Tasks**:
1. Create a dashboard with 6 panels:
   - Request rate (requests/sec)
   - Response time (p50, p95, p99)
   - Error rate
   - Items created over time
   - Database connection pool status
   - Container resource usage
2. Set up alerts for high error rate (>5%)
3. Configure Slack/email notifications

**Verification**:
- Dashboard shows real-time metrics
- Alerts trigger when thresholds are exceeded
- Notifications are received

---

### Exercise 3.3: Distributed Tracing (Optional, 60 minutes)

**Objective**: Add distributed tracing with Jaeger.

**Tasks**:
1. Add Jaeger to docker-compose.yml
2. Instrument FastAPI with OpenTelemetry
3. Trace database queries
4. View traces in Jaeger UI

---

## Part 4: Advanced Features

### Exercise 4.1: Feature Flags (45 minutes)

**Objective**: Implement feature flags for gradual rollouts.

**Tasks**:
1. Deploy Unleash server
2. Create a feature flag "new_item_validation"
3. Implement flag check in FastAPI
4. Test enabling/disabling the feature
5. Roll out to 50% of users

**Code Example**:
```python
from unleash import UnleashClient

unleash = UnleashClient(url="http://unleash:4242/api")

@app.post("/items")
def create_item(item: ItemCreate):
    if unleash.is_enabled("new_item_validation"):
        # New validation logic
        validate_item_advanced(item)
    else:
        # Old validation
        validate_item_basic(item)
```

---

### Exercise 4.2: Caching Layer (45 minutes)

**Objective**: Add Redis for caching frequently accessed data.

**Tasks**:
1. Add Redis to docker-compose.yml
2. Implement caching for GET /items
3. Set cache TTL to 5 minutes
4. Add cache hit/miss metrics
5. Implement cache invalidation on POST

**Verification**:
- First request is slow (cache miss)
- Subsequent requests are fast (cache hit)
- Cache is invalidated on updates

---

### Exercise 4.3: Rate Limiting (30 minutes)

**Objective**: Implement API rate limiting.

**Tasks**:
1. Add rate limiting middleware
2. Limit to 100 requests per minute per IP
3. Return 429 status when limit exceeded
4. Add rate limit headers to responses

**Code Example**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/items")
@limiter.limit("100/minute")
def list_items():
    # ...
```

---

### Exercise 4.4: API Versioning (30 minutes)

**Objective**: Implement API versioning strategy.

**Tasks**:
1. Create v1 and v2 API routes
2. Maintain backward compatibility
3. Add deprecation warnings to v1
4. Document version differences

---

## Part 5: Security & Performance

### Exercise 5.1: Authentication & Authorization (60 minutes)

**Objective**: Add JWT-based authentication.

**Tasks**:
1. Implement user registration endpoint
2. Implement login endpoint (returns JWT)
3. Add authentication middleware
4. Protect endpoints with auth
5. Implement role-based access control

**Verification**:
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret"}' \
  | jq -r '.access_token')

# Access protected endpoint
curl http://localhost:8000/items \
  -H "Authorization: Bearer $TOKEN"
```

---

### Exercise 5.2: Input Validation & Sanitization (30 minutes)

**Objective**: Implement comprehensive input validation.

**Tasks**:
1. Add Pydantic validators for all inputs
2. Sanitize user inputs to prevent XSS
3. Implement SQL injection protection
4. Add request size limits
5. Validate file uploads

---

### Exercise 5.3: Performance Optimization (45 minutes)

**Objective**: Optimize application performance.

**Tasks**:
1. Add database connection pooling
2. Implement query optimization (add indexes)
3. Enable gzip compression
4. Add response caching headers
5. Implement pagination for list endpoints

**Benchmark**:
```bash
# Before optimization
ab -n 1000 -c 10 http://localhost:8000/items

# After optimization
ab -n 1000 -c 10 http://localhost:8000/items
```

**Target**: Reduce response time by 50%.

---

### Exercise 5.4: Load Testing (45 minutes)

**Objective**: Perform load testing and identify bottlenecks.

**Tasks**:
1. Install Locust or k6
2. Create load test scenarios
3. Run tests with 100 concurrent users
4. Identify bottlenecks in Grafana
5. Optimize based on findings

**Load Test Script** (k6):
```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  let response = http.get('http://localhost:8000/items');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

---

## Part 6: Production Readiness

### Exercise 6.1: Health Checks & Readiness Probes (30 minutes)

**Objective**: Implement comprehensive health checks.

**Tasks**:
1. Add `/health/live` endpoint (liveness probe)
2. Add `/health/ready` endpoint (readiness probe)
3. Check database connectivity
4. Check external service dependencies
5. Update ECS task definition with health checks

---

### Exercise 6.2: Logging Strategy (45 minutes)

**Objective**: Implement structured logging.

**Tasks**:
1. Configure structured JSON logging
2. Add request ID to all logs
3. Log important business events
4. Set up log aggregation in CloudWatch
5. Create log-based metrics

---

### Exercise 6.3: Disaster Recovery (60 minutes)

**Objective**: Implement backup and recovery procedures.

**Tasks**:
1. Set up automated database backups
2. Test database restore procedure
3. Document recovery time objective (RTO)
4. Document recovery point objective (RPO)
5. Create runbook for common failures

---

### Exercise 6.4: Cost Optimization (30 minutes)

**Objective**: Reduce AWS costs without sacrificing performance.

**Tasks**:
1. Analyze current costs in AWS Cost Explorer
2. Implement ECR lifecycle policies
3. Use Fargate Spot for dev environment
4. Set up budget alerts
5. Right-size ECS task resources

---

## Bonus Challenges

### Challenge 1: Multi-Region Deployment
Deploy the application to multiple AWS regions with Route 53 failover.

### Challenge 2: Blue-Green Deployment
Implement blue-green deployment strategy with zero downtime.

### Challenge 3: Chaos Engineering
Use AWS Fault Injection Simulator to test resilience.

### Challenge 4: GraphQL API
Add a GraphQL endpoint alongside REST API.

### Challenge 5: WebSocket Support
Add real-time features using WebSockets.

---

## Assessment Criteria

For each exercise, you should be able to:
- ✅ Complete all tasks
- ✅ Verify the implementation works
- ✅ Explain the concepts and decisions
- ✅ Troubleshoot common issues
- ✅ Document your work

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pulumi AWS Examples](https://github.com/pulumi/examples)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)

## Getting Help

- Check the troubleshooting section in DEPLOYMENT_GUIDE.md
- Review CloudWatch logs for errors
- Use `pulumi logs` to see infrastructure events
- Join the community Discord/Slack for support
