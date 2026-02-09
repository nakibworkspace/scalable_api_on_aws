# Scalable FastAPI on AWS - Hands-On Lab

A production-ready FastAPI application deployed on AWS ECS with PostgreSQL, Prometheus, and Grafana running in Docker containers. Infrastructure managed with Pulumi and CI/CD via GitHub Actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Cloud                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Application Load Balancer                │  │
│  │  (Routes: /, /prometheus*, /grafana*)                │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │           ECS Fargate Task                           │  │
│  │                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │ FastAPI  │  │Prometheus│  │ Grafana  │          │  │
│  │  │  :8000   │  │  :9090   │  │  :3000   │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  │       │              │              │                │  │
│  │  ┌────▼──────────────▼──────────────▼────┐         │  │
│  │  │         PostgreSQL :5432               │         │  │
│  │  └────────────────────────────────────────┘         │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │  EFS (Persistent Storage for DB, Metrics, Dashboards) │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **FastAPI**: Modern Python web framework with automatic API documentation
- **PostgreSQL**: Relational database with persistent EFS storage
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Metrics visualization and dashboards
- **AWS ECS Fargate**: Serverless container orchestration
- **Pulumi**: Infrastructure as Code for AWS resources
- **GitHub Actions**: Automated CI/CD pipeline
- **Database Migrations**: Alembic for schema management

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- AWS CLI configured
- Pulumi CLI installed
- GitHub account

### Local Development

1. **Clone and setup**:
```bash
git clone <your-repo>
cd <your-repo>
```

2. **Start all services**:
```bash
docker-compose up --build
```

3. **Access services**:
- FastAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

4. **Test the API**:
```bash
# Health check
curl http://localhost:8000/health

# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","description":"My first item"}'

# List items
curl http://localhost:8000/items

# View metrics
curl http://localhost:8000/metrics
```

## Part 1: Initial Setup & Deployment

### Step 1: Configure AWS Infrastructure

```bash
cd infra
pulumi login
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi config set --secret db-password YourSecurePassword123
```

### Step 2: Deploy to AWS

```bash
pulumi up
```

This creates:
- VPC with public/private subnets
- ECS Cluster and Fargate service
- Application Load Balancer
- ECR repository
- EFS for persistent storage
- Security groups and IAM roles

### Step 3: Build and Push Docker Image

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t fastapi-app .
docker tag fastapi-app:latest $(pulumi stack output ecr_repository_url):latest
docker push $(pulumi stack output ecr_repository_url):latest
```

### Step 4: Setup GitHub Actions

Add these secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PULUMI_ACCESS_TOKEN`
- `DB_PASSWORD`

The CI/CD pipeline will:
1. Run tests and linting
2. Build Docker image
3. Push to ECR
4. Run database migrations
5. Deploy to ECS

## Part 2: Advanced Features

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Monitoring Setup

1. **Prometheus** scrapes metrics from FastAPI at `/metrics`
2. **Grafana** visualizes metrics from Prometheus
3. Access Grafana at `http://<alb-url>/grafana`

### Feature Flags (Optional)

Add Unleash for gradual feature rollouts:
```python
from unleash import UnleashClient

client = UnleashClient(
    url="<unleash-url>",
    app_name="fastapi-app",
)

if client.is_enabled("new_feature"):
    # New feature code
    pass
```

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── test_main.py         # Unit tests
│   └── requirements.txt     # Python dependencies
├── infra/
│   ├── __main__.py          # Pulumi infrastructure code
│   ├── Pulumi.yaml          # Pulumi project config
│   └── requirements.txt     # Pulumi dependencies
├── migrations/
│   ├── env.py               # Alembic environment
│   └── script.py.mako       # Migration template
├── monitoring/
│   ├── prometheus.yml       # Prometheus config
│   ├── grafana-datasource.yml
│   └── grafana-dashboard.json
├── .github/
│   └── workflows/
│       ├── ci.yml           # CI pipeline
│       ├── deploy.yml       # Deployment pipeline
│       └── e2e-tests.yml    # E2E tests
├── docker-compose.yml       # Local development
├── Dockerfile               # Container image
└── README.md
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - API documentation (Swagger UI)
- `POST /items` - Create item
- `GET /items` - List items
- `GET /items/{id}` - Get item by ID

## Monitoring

### Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Response time
http_request_duration_seconds

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

### Grafana Dashboards

Import the provided dashboard from `monitoring/grafana-dashboard.json`

## Troubleshooting

### Check ECS task logs
```bash
aws logs tail /aws/ecs/fastapi-app --follow
```

### Check service status
```bash
aws ecs describe-services --cluster <cluster-name> --services <service-name>
```

### Test database connection
```bash
docker-compose exec postgres psql -U user -d appdb
```

## Cleanup

```bash
# Destroy AWS resources
cd infra
pulumi destroy

# Remove local containers
docker-compose down -v
```

## Next Steps

- [ ] Add SSL/TLS with AWS Certificate Manager
- [ ] Configure custom domain with Route 53
- [ ] Set up CloudWatch alarms
- [ ] Implement auto-scaling policies
- [ ] Add Redis for caching
- [ ] Create internal Python packages
- [ ] Implement feature flags with Unleash
- [ ] Add comprehensive E2E tests
- [ ] Set up continuous deployment

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pulumi AWS Guide](https://www.pulumi.com/docs/clouds/aws/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

## License

MIT
