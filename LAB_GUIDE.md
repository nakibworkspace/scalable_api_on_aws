# Hands-On Lab: Scalable FastAPI on AWS with Pulumi

## Overview
Build a production-ready FastAPI application on AWS ECS with PostgreSQL, Prometheus, and Grafana running in Docker containers. Deploy using Pulumi IaC and GitHub Actions CI/CD.

## Architecture
- **FastAPI**: REST API application
- **PostgreSQL**: Database (containerized)
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **AWS ECS Fargate**: Container orchestration
- **AWS ALB**: Load balancing
- **AWS ECR**: Container registry
- **Pulumi**: Infrastructure as Code
- **GitHub Actions**: CI/CD pipeline

---

## Part 1: Setup & Initial Deployment

### Prerequisites
- AWS Account with CLI configured
- Docker installed
- Python 3.9+
- Pulumi CLI installed
- GitHub account

### Step 1: Local Development Setup

1. **Test locally with Docker Compose**:
```bash
docker-compose up --build
```

2. **Verify services**:
- FastAPI: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- PostgreSQL: localhost:5432

3. **Test API endpoints**:
```bash
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Step 2: Configure AWS Infrastructure

1. **Initialize Pulumi**:
```bash
cd infra
pulumi login
pulumi stack init dev
pulumi config set aws:region us-east-1
```

2. **Set secrets**:
```bash
pulumi config set --secret db-password YourSecurePassword123
```

3. **Deploy infrastructure**:
```bash
pulumi up
```

### Step 3: Build & Push Docker Image

1. **Authenticate with ECR**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

2. **Build and push**:
```bash
docker build -t fastapi-app .
docker tag fastapi-app:latest <ecr-repo-url>:latest
docker push <ecr-repo-url>:latest
```

### Step 4: Setup CI/CD Pipeline

The GitHub Actions workflow will:
- Run tests and linting
- Build Docker image
- Push to ECR
- Deploy to ECS using Pulumi

---

## Part 2: Database, Monitoring & Advanced Features

### Step 5: Database Migrations

1. **Add Alembic for migrations**
2. **Configure migration job in CI/CD**
3. **Run migrations on deployment**

### Step 6: End-to-End Testing

1. **Add E2E tests with pytest**
2. **Configure test database**
3. **Add E2E test job to pipeline**

### Step 7: Internal Python Packages

1. **Create shared library package**
2. **Publish to GitHub Packages**
3. **Use in FastAPI app**

### Step 8: Feature Flags with Unleash

1. **Deploy Unleash server**
2. **Integrate with FastAPI**
3. **Implement gradual rollout**

### Step 9: Monitoring Setup

1. **Configure Prometheus scraping**
2. **Import Grafana dashboards**
3. **Set up alerts**

### Step 10: Continuous Deployment

1. **Configure auto-deployment on main branch**
2. **Add deployment approval gates**
3. **Set up rollback strategy**

---

## Next Steps

Follow the detailed implementation files in this repository to complete each step.
