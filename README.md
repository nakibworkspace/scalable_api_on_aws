# Scalable FastAPI on AWS - Complete Hands-On Lab

A production-ready, scalable FastAPI application deployed on AWS using modern DevOps practices. This project demonstrates Infrastructure as Code (Pulumi), containerization (Docker/ECS), CI/CD (GitHub Actions), monitoring (Prometheus/Grafana), and managed databases (RDS).

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Actions CI/CD                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Lint   │→ │   Test   │→ │  Build   │→ │  Deploy  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   AWS ECR Registry   │
              │  (Docker Images)     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Application Load    │
              │     Balancer (ALB)   │
              │   - HTTP/HTTPS       │
              │   - Path routing     │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐    ┌────────────┐   ┌─────────┐
    │FastAPI │    │ Prometheus │   │ Grafana │
    │  ECS   │    │    ECS     │   │   ECS   │
    │Fargate │    │  Fargate   │   │ Fargate │
    └───┬────┘    └─────┬──────┘   └────┬────┘
        │               │               │
        │               └───────┬───────┘
        │                       │
        ▼                       ▼
   ┌─────────┐            ┌─────────┐
   │   RDS   │            │   EFS   │
   │Postgres │            │ Storage │
   │ (15.4)  │            │         │
   └─────────┘            └─────────┘
```

## ✨ Features

### Infrastructure
- ✅ **AWS ECS Fargate**: Serverless container orchestration
- ✅ **AWS ECR**: Private Docker registry
- ✅ **AWS RDS PostgreSQL**: Managed database with automated backups
- ✅ **AWS ALB**: Application load balancer with path-based routing
- ✅ **AWS EFS**: Persistent storage for monitoring data
- ✅ **VPC**: Private/public subnets with NAT gateway
- ✅ **Security Groups**: Properly configured network isolation
- ✅ **IAM Roles**: Least privilege access control

### Application
- ✅ **FastAPI**: Modern, fast Python web framework
- ✅ **SQLAlchemy**: Database ORM
- ✅ **Alembic**: Database migrations
- ✅ **Pydantic**: Data validation
- ✅ **Async/Await**: Asynchronous request handling

### Monitoring & Observability
- ✅ **Prometheus**: Metrics collection and alerting
- ✅ **Grafana**: Visualization and dashboards
- ✅ **CloudWatch Logs**: Centralized logging
- ✅ **Health Checks**: Application and infrastructure monitoring

### CI/CD
- ✅ **GitHub Actions**: Automated testing and deployment
- ✅ **Linting**: Code quality with Ruff
- ✅ **Type Checking**: Static analysis with MyPy
- ✅ **Unit Tests**: Pytest with coverage
- ✅ **E2E Tests**: End-to-end testing
- ✅ **Security Scanning**: Bandit for security issues

### DevOps
- ✅ **Pulumi**: Infrastructure as Code (Python)
- ✅ **Docker**: Containerization
- ✅ **Docker Compose**: Local development
- ✅ **Multi-stage Builds**: Optimized images
- ✅ **Blue/Green Deployments**: Zero-downtime updates

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- AWS Account
- Pulumi Account (free tier)
- GitHub Account

### Local Development

```bash
# Clone repository
git clone <your-repo-url>
cd <repo-name>

# Start all services
docker-compose up -d

# Access services
open http://localhost:8000/docs      # FastAPI
open http://localhost:9090           # Prometheus
open http://localhost:3000           # Grafana (admin/admin)

# Run tests
pytest

# Stop services
docker-compose down
```

### Deploy to AWS

```bash
# Install Pulumi
brew install pulumi/tap/pulumi  # macOS
# or visit: https://www.pulumi.com/docs/install/

# Configure Pulumi
cd infra
pulumi login
pulumi stack init production
pulumi config set aws:region us-east-1
pulumi config set --secret db-password YourSecurePassword123!

# Deploy infrastructure
pulumi up

# Note the outputs:
# - app_url: Your application URL
# - ecr_repository_url: Docker registry
# - rds_endpoint: Database endpoint
```

### Configure CI/CD

1. Go to GitHub repository → Settings → Secrets
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `PULUMI_ACCESS_TOKEN`
3. Push to main branch to trigger deployment

```bash
git add .
git commit -m "feat: initial deployment"
git push origin main
```

## 📚 Documentation

- **[LAB_GUIDE.md](LAB_GUIDE.md)**: Complete step-by-step lab exercises
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**: Command reference and troubleshooting
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**: Detailed deployment instructions
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: Initial setup and configuration
- **[LAB_EXERCISES.md](LAB_EXERCISES.md)**: Hands-on exercises

## 🎯 Learning Objectives

### Part 1: Foundation
- Structure FastAPI applications for production
- Configure CI/CD pipelines with GitHub Actions
- Manage AWS infrastructure with Pulumi (IaC)
- Build and push Docker images to ECR
- Deploy containerized apps to ECS Fargate
- Set up monitoring with Prometheus and Grafana

### Part 2: Advanced
- Manage RDS PostgreSQL databases
- Handle database migrations in CI/CD
- Implement end-to-end testing
- Configure auto-scaling
- Set up SSL/TLS with ACM
- Implement blue/green deployments
- Monitor with CloudWatch

## 🛠️ Technology Stack

| Category | Technology |
|----------|-----------|
| **Language** | Python 3.11 |
| **Framework** | FastAPI |
| **Database** | PostgreSQL 15 (RDS) |
| **ORM** | SQLAlchemy |
| **Migrations** | Alembic |
| **Container** | Docker |
| **Orchestration** | AWS ECS Fargate |
| **Registry** | AWS ECR |
| **Load Balancer** | AWS ALB |
| **Storage** | AWS EFS |
| **IaC** | Pulumi (Python) |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus + Grafana |
| **Logging** | CloudWatch Logs |
| **Testing** | Pytest |

## 📁 Project Structure

```
.
├── app/                          # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   ├── database.py               # Database connection
│   ├── models.py                 # SQLAlchemy models
│   ├── schemas.py                # Pydantic schemas
│   ├── crud.py                   # Database operations
│   └── requirements.txt          # Python dependencies
│
├── infra/                        # Pulumi infrastructure
│   ├── __main__.py               # Infrastructure definition
│   │   ├── VPC & Networking      # Private/public subnets
│   │   ├── Security Groups       # Network isolation
│   │   ├── RDS PostgreSQL        # Managed database
│   │   ├── ECS Cluster           # Container orchestration
│   │   ├── ECR Repository        # Docker registry
│   │   ├── EFS                   # Persistent storage
│   │   ├── ALB                   # Load balancer
│   │   └── IAM Roles             # Access control
│   └── requirements.txt          # Pulumi dependencies
│
├── .github/workflows/            # CI/CD pipelines
│   ├── ci.yml                    # Test & quality checks
│   ├── deploy.yml                # AWS deployment
│   └── e2e-tests.yml             # End-to-end tests
│
├── migrations/                   # Database migrations
│   ├── env.py                    # Alembic environment
│   └── versions/                 # Migration scripts
│
├── monitoring/                   # Monitoring configuration
│   ├── prometheus.yml            # Prometheus config
│   ├── grafana-dashboard.json    # Grafana dashboard
│   └── grafana-datasource.yml    # Grafana datasource
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
│
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local development
├── alembic.ini                   # Migration configuration
├── pytest.ini                    # Test configuration
└── .env.example                  # Environment template
```

## 🔧 Common Commands

```bash
# Local Development
docker-compose up -d              # Start services
docker-compose logs -f fastapi    # View logs
pytest --cov=app                  # Run tests with coverage

# Database Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Infrastructure
cd infra
pulumi preview                    # Preview changes
pulumi up                         # Deploy
pulumi destroy                    # Tear down
pulumi stack output               # View outputs

# AWS Operations
aws ecs list-tasks --cluster fastapi-app-cluster
aws logs tail /aws/ecs/fastapi-app-logs --follow
aws ecs update-service --cluster fastapi-app-cluster \
  --service fastapi-app-service --force-new-deployment
```

## 🔐 Security Best Practices

- ✅ RDS in private subnets only
- ✅ Security groups with minimal access
- ✅ Secrets encrypted with Pulumi config
- ✅ IAM roles with least privilege
- ✅ SSL/TLS for all external traffic
- ✅ RDS and EFS encryption enabled
- ✅ Regular security scanning in CI/CD
- ✅ No hardcoded credentials

## 💰 Cost Estimation

### Free Tier (First 12 months)
- RDS db.t3.micro: 750 hours/month
- ECS Fargate: 20GB storage, 10GB transfer
- ECR: 500MB storage
- ALB: 750 hours/month (first year)

### Estimated Monthly Cost (After Free Tier)
- RDS db.t3.micro: ~$15
- ECS Fargate (1 task): ~$15
- ALB: ~$20
- EFS: ~$3
- **Total: ~$53/month**

### Cost Optimization Tips
```bash
# Stop services when not in use
aws ecs update-service --desired-count 0
aws rds stop-db-instance --db-instance-identifier fastapi-app-postgres

# Use Spot instances for non-production
# Enable auto-scaling to match demand
# Clean up old ECR images
```

## 🐛 Troubleshooting

### ECS Task Won't Start
```bash
# Check logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Describe task
aws ecs describe-tasks --cluster fastapi-app-cluster --tasks <task-id>
```

### Database Connection Issues
```bash
# Verify security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connection
psql postgresql://user:pass@<rds-endpoint>:5432/dbname
```

### Load Balancer Health Checks Failing
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn <arn>

# Verify health endpoint
curl http://<alb-url>/health
```

## 📊 Monitoring

### Prometheus Metrics
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency
- `up`: Service availability

### Grafana Dashboards
- Request rate and error rate
- Latency percentiles (p50, p95, p99)
- Database connection pool
- ECS task metrics

### CloudWatch Alarms
- ECS CPU/Memory utilization
- RDS connections and storage
- ALB target health
- Application errors

## 🚢 Deployment Strategies

### Rolling Update (Default)
- Gradual replacement of tasks
- Zero downtime
- Automatic rollback on failure

### Blue/Green Deployment
- Full environment duplication
- Instant traffic switch
- Easy rollback

### Canary Deployment
- Gradual traffic shift
- Monitor metrics before full rollout
- Minimize blast radius

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- FastAPI documentation and community
- Pulumi AWS examples
- AWS ECS best practices guide
- Prometheus and Grafana communities

## 📞 Support

- 📖 [Full Lab Guide](LAB_GUIDE.md)
- 🔍 [Quick Reference](QUICK_REFERENCE.md)
- 💬 Open an issue for questions
- 📧 Contact: your-email@example.com

---

**Ready to get started?** Follow the [LAB_GUIDE.md](LAB_GUIDE.md) for step-by-step instructions!
