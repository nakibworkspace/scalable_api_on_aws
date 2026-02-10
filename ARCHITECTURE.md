# Architecture Documentation - EC2 Deployment

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │   Code     │→ │    CI      │→ │   Build    │→ │   Deploy   │       │
│  │  Changes   │  │  Pipeline  │  │   Docker   │  │   to EC2   │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │      AWS ECR Registry        │
              │   (Docker Image Storage)     │
              │  - fastapi-app:latest        │
              │  - Image scanning enabled    │
              │  - Lifecycle policy (10 img) │
              └──────────────┬───────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud (VPC)                               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                      Public Subnet                                │ │
│  │                                                                    │ │
│  │    ┌────────────────────────────────────────────────────┐        │ │
│  │    │         EC2 Instance (t3.small)                    │        │ │
│  │    │  - Public IP: Auto-assigned                        │        │ │
│  │    │  - Security Group: HTTP/HTTPS/SSH                  │        │ │
│  │    │  - IAM Role: ECR Read + SSM                        │        │ │
│  │    │  - AMI: Amazon Linux 2023                          │        │ │
│  │    │                                                     │        │ │
│  │    │  ┌──────────────────────────────────────────────┐ │        │ │
│  │    │  │         Docker Engine                        │ │        │ │
│  │    │  │                                               │ │        │ │
│  ���    │  │  ┌──────────────────────────────────────┐   │ │        │ │
│  │    │  │  │   FastAPI Container                  │   │ │        │ │
│  │    │  │  │   - Port: 8000 → 80                  │   │ │        │ │
│  │    │  │  │   - Image: ECR latest                │   │ │        │ │
│  │    │  │  │   - Restart: unless-stopped          │   │ │        │ │
│  │    │  │  │   - Health: /health endpoint         │   │ │        │ │
│  │    │  │  │   - Metrics: /metrics endpoint       │   │ │        │ │
│  │    │  │  └──────────────┬───────────────────────┘   │ │        │ │
│  │    │  │                 │                            │ │        │ │
│  │    │  └─────────────────┼────────────────────────────┘ │        │ │
│  │    │                    │                              │        │ │
│  │    └────────────────────┼──────────────────────────────┘        │ │
│  │                         │                                        │ │
│  └─────────────────────────┼────────────────────────────────────────┘ │
│                            │                                          │
│                  ┌─────────▼─────────┐                                │
│                  │ External Database │                                │
│                  │   PostgreSQL      │                                │
│                  │  - Host: External │                                │
│                  │  - Port: 5432     │                                │
│                  └───────────────────┘                                │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack (Docker Compose)                    │
│                    (Runs on local machine or separate server)           │
│                                                                         │
│  ┌──────────────────┐         ┌──────────────────┐                    │
│  │   Prometheus     │────────→│     Grafana      │                    │
│  │   Port: 9090     │         │   Port: 3001     │                    │
│  │   Scrapes EC2    │         │   Dashboards     │                    │
│  │   /metrics       │         │   admin/admin    │                    │
│  └──────────────────┘         └──────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Request Flow
```
User Browser/Client
    ↓
Internet
    ↓
EC2 Public IP (Port 80)
    ↓
Docker Container (FastAPI on Port 8000)
    ↓
FastAPI Application Routes Request
    ↓
┌─────────────────────────────────────┐
│ Request Type:                       │
│                                     │
│ /health, /, /model/info            │
│    → Return status immediately      │
│                                     │
│ /items (GET/POST)                   │
│    → Query PostgreSQL Database      │
│    → Return items data              │
│                                     │
│ /predict (POST)                     │
│    → Load ML model from memory      │
│    → Run sentiment prediction       │
│    → Return prediction result       │
└─────────────────────────────────────┘
    ↓
FastAPI Response
    ↓
Docker Container
    ↓
EC2 Instance (Port 80)
    ↓
Internet
    ↓
User Browser/Client (receives JSON response)
```

### 2. Deployment Flow
```
Developer Push to GitHub (main branch)
    ↓
GitHub Actions: CI Pipeline Triggered
    ↓
├─ Checkout Code
├─ Set up Python 3.11
├─ Install Dependencies (requirements.txt)
└─ Run Tests (pytest)
    ↓
Tests Pass ✓
    ↓
GitHub Actions: Deploy Pipeline Triggered
    ↓
├─ Checkout Code
├─ Configure AWS Credentials (from secrets)
└─ Login to Amazon ECR
    ↓
Build Docker Image
├─ Tag with commit SHA (e.g., abc123)
└─ Tag with 'latest'
    ↓
Push Both Tags to ECR
    ↓
Install Pulumi CLI & Dependencies
    ↓
Pulumi Up (Infrastructure Deployment)
├─ Create/Update VPC & Subnet
├─ Create/Update Security Group
├─ Create/Update IAM Role
├─ Create/Update EC2 Instance
└─ Output: instance_id, public_ip, ecr_url
    ↓
Run Database Migrations
└─ alembic upgrade head (on GitHub runner)
    ↓
Get EC2 Instance ID from Pulumi Output
    ↓
Wait for EC2 Instance to be Ready
└─ aws ec2 wait instance-status-ok
    ↓
Deploy to EC2 via AWS SSM
├─ Send command to EC2 instance
├─ EC2: Login to ECR
├─ EC2: Pull latest Docker image
├─ EC2: Stop old container (if exists)
├─ EC2: Remove old container
└─ EC2: Start new container
    │   ├─ Port mapping: 80:8000
    │   ├─ Restart policy: unless-stopped
    │   └─ Environment: DATABASE_URL
    ↓
Container Health Check
└─ FastAPI /health endpoint responds
    ↓
Deployment Complete ✓
└─ Application accessible at EC2 Public IP
```

### 3. Monitoring Flow
```
FastAPI Application (on EC2)
    ↓
Expose /metrics endpoint (starlette-exporter)
    ↓
Prometheus (Docker Compose)
    ↓
Scrapes metrics from EC2 Public IP
    ↓
Store in Time-Series DB (prometheus_data volume)
    ↓
Grafana (Docker Compose)
    ↓
Queries Prometheus data source
    ↓
Display Dashboards (http://localhost:3001)
```

## Component Details

### 1. VPC Configuration
- **CIDR Block**: 10.0.0.0/16
- **Availability Zone**: ap-southeast-1a
- **Public Subnet**: 1
  - CIDR: 10.0.1.0/24
  - EC2 instance deployed here
  - Internet Gateway attached
- **Route Tables**: Public route to Internet Gateway

### 2. EC2 Instance
```yaml
Instance Type: t3.small (2 vCPU, 2 GB RAM)
AMI: Amazon Linux 2023 (ami-01811d4912b4ccb26)
Storage: 8 GB gp3 (default)
Public IP: Auto-assigned
Monitoring: CloudWatch basic monitoring

User Data Script:
  - Install Docker
  - Install AWS CLI v2
  - Login to ECR
  - Pull latest image
  - Run container on port 80
  - Auto-restart on failure
```

### 3. Security Group
```yaml
Ingress Rules:
  - Port 80 (HTTP): 0.0.0.0/0
  - Port 8000 (FastAPI): 0.0.0.0/0
  - Port 22 (SSH): 0.0.0.0/0

Egress Rules:
  - All traffic: 0.0.0.0/0
```

### 4. IAM Configuration

#### EC2 Instance Role
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "ec2.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
```

#### Attached Policies
- **AmazonEC2ContainerRegistryReadOnly**: Pull images from ECR
- **AmazonSSMManagedInstanceCore**: AWS Systems Manager access

### 5. Docker Container Configuration
```bash
Container Name: fastapi-app
Image: <ECR_URL>:latest
Port Mapping: 80:8000
Restart Policy: unless-stopped
Environment Variables:
  - DATABASE_URL: PostgreSQL connection string
```

### 6. ECR Repository
```yaml
Repository Name: fastapi-app-repo
Image Scanning: Enabled (scan on push)
Lifecycle Policy: Keep last 10 images
Encryption: AES-256
```

## Scaling Strategy

### Vertical Scaling
```bash
# Upgrade instance type
# t3.small → t3.medium → t3.large

# Update Pulumi code
instance_type="t3.medium"

# Deploy
pulumi up
```

### Horizontal Scaling (Future Enhancement)
```yaml
# Use Auto Scaling Group
Min Instances: 2
Max Instances: 5
Target CPU: 70%
Load Balancer: Application Load Balancer
Health Check: /health endpoint
```

### Container Resource Limits
```bash
# Add resource limits to docker run
docker run -d \
  --memory="512m" \
  --cpus="0.5" \
  --name fastapi-app \
  <ECR_URL>:latest
```

## High Availability

### Current Setup
- **Instances**: 1 EC2 instance
- **Availability Zone**: Single AZ
- **Container**: Auto-restart on failure
- **Database**: External (managed separately)
- **Availability**: ~99.5%

### Production Recommendations
- **Instances**: 2+ EC2 instances in Auto Scaling Group
- **Availability Zones**: Multi-AZ deployment
- **Load Balancer**: Application Load Balancer
- **Database**: Multi-AZ RDS
- **Health Checks**: ALB health checks
- **Availability**: ~99.9%

## Disaster Recovery

### Backup Strategy
```
Infrastructure:
  - Pulumi code in Git
  - Can recreate from code

Docker Images:
  - Stored in ECR
  - Lifecycle policy keeps last 10
  - Can rollback to any version

Database:
  - External database backups
  - Point-in-time recovery

Application State:
  - Stateless application
  - No local state to backup
```

### Recovery Procedures
```
1. Instance Failure:
   - Pulumi up (recreates instance)
   - User data script auto-deploys
   - Time: 5-10 minutes

2. Container Failure:
   - Docker auto-restarts
   - Time: < 30 seconds

3. Application Crash:
   - Docker restart policy
   - Time: < 10 seconds

4. Database Restore:
   - Restore from backup
   - Update DATABASE_URL
   - Restart container
```

## Cost Breakdown

### Monthly Costs (Estimated)

```
EC2 Instance (t3.small):
  - $0.0208/hour × 730 hours = $15.18/month

EBS Storage (8 GB gp3):
  - $0.08/GB × 8 GB = $0.64/month

Data Transfer:
  - First 1 GB free
  - $0.09/GB after = ~$5/month

ECR Storage:
  - 500MB × $0.10/GB = $0.05/month

CloudWatch:
  - Basic monitoring: Free
  - Logs: ~$1/month

Monitoring (Self-hosted):
  - Prometheus/Grafana: $0 (Docker Compose)

Total: ~$22/month
```

### Cost Optimization
1. Use Reserved Instances (save ~40%)
2. Use Spot Instances (save ~70%)
3. Right-size instance type
4. Enable detailed monitoring only when needed
5. Clean up old ECR images
6. Use S3 for static assets

## Monitoring & Observability

### Integrated Monitoring Stack (Docker Compose)

#### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['<EC2_PUBLIC_IP>:80']
    metrics_path: '/metrics'
```

#### FastAPI Metrics Endpoint
```python
from starlette_exporter import PrometheusMiddleware, handle_metrics

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)
```

**Available Metrics:**
- `starlette_requests_total` - Total requests
- `starlette_request_duration_seconds` - Request duration
- `starlette_requests_in_progress` - Active requests

#### Accessing Monitoring Tools
```bash
# Update prometheus.yml with EC2 public IP
# Start monitoring stack
docker-compose up -d prometheus grafana

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3001 (admin/admin)
```

### CloudWatch Monitoring
```bash
# View instance metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<instance-id> \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average
```

### Useful Commands
```bash
# SSH into instance (if key pair configured)
ssh -i key.pem ec2-user@<public-ip>

# View container logs
docker logs -f fastapi-app

# Check container status
docker ps

# Restart container
docker restart fastapi-app

# View instance logs via SSM
aws ssm start-session --target <instance-id>
```

## Troubleshooting Guide

### Container Not Starting
```bash
# SSH or SSM into instance
aws ssm start-session --target <instance-id>

# Check Docker status
sudo systemctl status docker

# View container logs
docker logs fastapi-app

# Common issues:
# - Image pull errors (check IAM role)
# - Port conflicts (check port 8000)
# - Environment variables (check DATABASE_URL)
```

### Cannot Access Application
```bash
# Check security group
aws ec2 describe-security-groups --group-ids <sg-id>

# Check instance status
aws ec2 describe-instances --instance-ids <instance-id>

# Test from instance
curl http://localhost:8000/health

# Common issues:
# - Security group not allowing port 80
# - Container not running
# - Application crashed
```

### High CPU/Memory Usage
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics ...

# SSH into instance
top
docker stats

# Common issues:
# - Insufficient instance size
# - Memory leak in application
# - Database query performance
```

## Security Best Practices

### Network Security
- ✅ VPC with public subnet
- ✅ Security group restricts traffic
- ⚠️ Consider private subnet + NAT Gateway
- ⚠️ Consider Application Load Balancer

### Instance Security
- ✅ IAM role (no hardcoded credentials)
- ✅ SSM for secure access (no SSH keys needed)
- ✅ Security group limits ports
- ⚠️ Enable IMDSv2
- ⚠️ Disable SSH (use SSM only)

### Container Security
- ✅ Non-root user in container
- ✅ ECR image scanning
- ✅ Private registry
- ⚠️ Read-only root filesystem
- ⚠️ Resource limits

### Application Security
- ✅ No hardcoded credentials
- ✅ Environment variables for config
- ⚠️ Add authentication/authorization
- ⚠️ Rate limiting
- ⚠️ Input validation

## Future Enhancements

1. **Auto Scaling**
   - Auto Scaling Group
   - Application Load Balancer
   - Target tracking policies
   - Multi-AZ deployment

2. **Enhanced Monitoring**
   - CloudWatch Container Insights
   - Custom CloudWatch dashboards
   - SNS alerts
   - Log aggregation

3. **Security Improvements**
   - AWS Secrets Manager
   - Private subnets + NAT Gateway
   - WAF for DDoS protection
   - VPC Flow Logs

4. **Performance**
   - CloudFront CDN
   - ElastiCache for caching
   - RDS Read Replicas
   - Connection pooling

5. **Deployment**
   - Blue-green deployments
   - Canary deployments
   - Automated rollback
   - Health check improvements

## Comparison: EC2 vs EKS

| Feature | EC2 (Current) | EKS |
|---------|---------------|-----|
| Cost | ~$22/month | ~$167/month |
| Complexity | Low | High |
| Scaling | Manual/ASG | Automatic (HPA) |
| Management | Simple | Complex |
| High Availability | Requires ALB + ASG | Built-in |
| Learning Curve | Easy | Steep |
| Best For | Small apps, learning | Production, microservices |

**When to use EC2:**
- Small to medium applications
- Cost-sensitive projects
- Simple deployment requirements
- Learning/development environments

**When to use EKS:**
- Large-scale applications
- Microservices architecture
- Need advanced orchestration
- Enterprise production workloads
