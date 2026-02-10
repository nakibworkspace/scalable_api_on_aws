# Architecture Documentation - EKS Deployment

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │   Code     │→ │    CI      │→ │   Build    │→ │   Deploy   │       │
│  │  Changes   │  │  Pipeline  │  │   Docker   │  │   to EKS   │       │
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
│  │                      Public Subnets (2 AZs)                       │ │
│  │                                                                    │ │
│  │    ┌────────────────────────────────────────────────────┐        │ │
│  │    │     AWS Load Balancer (via K8s Service)            │        │ │
│  │    │  - Type: LoadBalancer                              │        │ │
│  │    │  - HTTP (port 80)                                  │        │ │
│  │    │  - Health checks to /health                        │        │ │
│  │    │  - Routes to FastAPI pods                          │        │ │
│  │    └────────────────────┬───────────────────────────────┘        │ │
│  │                         │                                         │ │
│  │    ┌────────────────────▼──────────────────────────┐             │ │
│  │    │         EKS Cluster (Kubernetes)               │             │ │
│  │    │  - Control Plane: Managed by AWS               │             │ │
│  │    │  - Version: Latest stable                      │             │ │
│  │    │                                                 │             │ │
│  │    │  ┌──────────────────────────────────────────┐ │             │ │
│  │    │  │        Worker Nodes (EC2)                │ │             │ │
│  │    │  │  - Instance Type: t3.medium              │ │             │ │
│  │    │  │  - Desired: 2 nodes                      │ │             │ │
│  │    │  │  - Min: 1, Max: 3                        │ │             │ │
│  │    │  │  - Auto-scaling enabled                  │ │             │ │
│  │    │  │                                           │ │             │ │
│  │    │  │  ┌──────────┐  ┌──────────┐             │ │             │ │
│  │    │  │  │ FastAPI  │  │ FastAPI  │             │ │             │ │
│  │    │  │  │   Pod    │  │   Pod    │             │ │             │ │
│  │    │  │  │          │  │          │             │ │             │ │
│  │    │  │  │Port: 8000│  │Port: 8000│             │ │             │ │
│  │    │  │  │/metrics  │  │/metrics  │             │ │             │ │
│  │    │  │  │CPU: 250m │  │CPU: 250m │             │ │             │ │
│  │    │  │  │Mem: 256Mi│  │Mem: 256Mi│             │ │             │ │
│  │    │  │  └────┬─────┘  └────┬─────┘             │ │             │ │
│  │    │  │       │             │                    │ │             │ │
│  │    │  └───────┼─────────────┼────────────────────┘ │             │ │
│  │    │          │             │                      │             │ │
│  │    └──────────┼─────────────┼──────────────────────┘             │ │
│  │               │             │                                     │ │
│  └───────────────┼─────────────┼─────────────────────────────────────┘ │
│                  │             │                                       │ │
│                  │             └──────────┐                            │ │
│                  │                        │                            │ │
│        ┌─────────▼─────────┐    ┌────────▼──────────┐                │ │
│        │ External Database │    │  Monitoring Stack │                │ │
│        │   PostgreSQL      │    │  (Docker Compose) │                │ │
│        │                   │    │                    │                │ │
│        │  - Host: External │    │  ┌──────────────┐ │                │ │
│        │  - Port: 5432     │    │  │  Prometheus  │ │                │ │
│        │  - Encrypted      │    │  │  Port: 9090  │ │                │ │
│        └───────────────────┘    │  │  Scrapes     │ │                │ │
│                                  │  │  /metrics    │ │                │ │
│                                  │  └──────┬───────┘ │                │ │
│                                  │         │         │                │ │
│                                  │  ┌──────▼───────┐ │                │ │
│                                  │  │   Grafana    │ │                │ │
│                                  │  │  Port: 3001  │ │                │ │
│                                  │  │  Dashboards  │ │                │ │
│                                  │  └──────────────┘ │                │ │
│                                  └────────────────────┘                │ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Request Flow
```
User Browser
    ↓
Internet
    ↓
AWS Load Balancer (created by K8s Service)
    ↓
Kubernetes Service (fastapi-service)
    ↓
FastAPI Pods (round-robin)
    ↓
External PostgreSQL Database (query data)
    ↑
FastAPI Pods (process response)
    ↓
Kubernetes Service
    ↓
AWS Load Balancer
    ↓
Internet
    ↓
User Browser (receives response)
```

### 2. Deployment Flow
```
Developer Push
    ↓
GitHub Actions Triggered
    ↓
Run Tests (Lint, Type Check, Unit Tests)
    ↓
Build Docker Image
    ↓
Push to ECR
    ↓
Pulumi Deploy EKS Infrastructure
    ↓
Configure kubectl
    ↓
Run Database Migrations
    ↓
Apply Kubernetes Manifests
    ↓
Kubernetes Rolling Update
    ↓
Health Checks Pass
    ↓
Traffic Shifted to New Pods
    ↓
Old Pods Terminated
```

### 3. Monitoring Flow
```
FastAPI Application (in EKS)
    ↓
Expose /metrics endpoint (starlette-exporter)
    ↓
Prometheus (Docker Compose)
    ↓
Scrapes metrics from Load Balancer URL
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
- **Availability Zones**: 2 (ap-southeast-1a, ap-southeast-1b)
- **Public Subnets**: 2 (one per AZ)
  - CIDR: 10.0.1.0/24, 10.0.2.0/24
  - EKS worker nodes deployed here
  - Load Balancer deployed here
  - Internet Gateway attached
- **Route Tables**: Public route to Internet Gateway

### 2. Docker Compose Monitoring Stack

The monitoring stack runs separately via Docker Compose on your local machine or monitoring server:

```yaml
# docker-compose.yml
services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-datasource.yml:/etc/grafana/provisioning/datasources/datasource.yml
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

**Key Points:**
- Prometheus scrapes metrics from the EKS Load Balancer URL
- Grafana connects to Prometheus as data source
- Data persists in Docker volumes
- Can run on any machine with Docker installed

### 3. EKS Cluster
```yaml
Cluster Name: fastapi-app-cluster
Kubernetes Version: Latest stable
Control Plane: Fully managed by AWS
Logging: API, Audit, Authenticator logs enabled

Worker Nodes:
  Instance Type: t3.medium (2 vCPU, 4 GB RAM)
  Desired Capacity: 2
  Min Size: 1
  Max Size: 3
  AMI: Amazon EKS-optimized
  Disk: 20 GB gp3
```

### 4. Kubernetes Resources

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi
  template:
    spec:
      containers:
      - name: fastapi
        image: <ECR_URL>:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: LoadBalancer
  selector:
    app: fastapi
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### 5. Security Configuration

#### IAM Roles
```
EKS Cluster Role:
  - AmazonEKSClusterPolicy
  - AmazonEKSVPCResourceController

Worker Node Role:
  - AmazonEKSWorkerNodePolicy
  - AmazonEKS_CNI_Policy
  - AmazonEC2ContainerRegistryReadOnly
  - CloudWatchAgentServerPolicy
```

#### Security Groups
```
EKS Control Plane SG:
  - Managed by AWS
  - Communication with worker nodes

Worker Node SG:
  - Ingress from control plane
  - Ingress from other worker nodes
  - Ingress from Load Balancer (port 80, 8000)
  - Egress to internet (for pulling images)
```

## Scaling Strategy

### Horizontal Pod Autoscaling (HPA)
```bash
kubectl autoscale deployment fastapi-deployment \
  --min=2 --max=10 --cpu-percent=70
```

### Cluster Autoscaling
```yaml
# Automatically adds/removes worker nodes
Min Nodes: 1
Max Nodes: 3
Scale Up: When pods can't be scheduled
Scale Down: When nodes are underutilized
```

### Manual Scaling
```bash
# Scale pods
kubectl scale deployment fastapi-deployment --replicas=5

# Scale nodes (via Pulumi)
desired_capacity: 3
```

## High Availability

### Current Setup
- **Pods**: 2 replicas across nodes
- **Worker Nodes**: 2 nodes across 2 AZs
- **Load Balancer**: Multi-AZ by default
- **Database**: External (managed separately)
- **Availability**: ~99.9%

### Production Recommendations
- **Pods**: 3+ replicas with pod anti-affinity
- **Worker Nodes**: 3+ nodes across 3 AZs
- **Pod Disruption Budget**: Ensure minimum availability
- **Database**: Multi-AZ RDS or managed service
- **Availability**: ~99.99%

## Disaster Recovery

### Backup Strategy
```
Kubernetes Manifests:
  - Version controlled in Git
  - Can recreate cluster from code

Database:
  - External database backups
  - Point-in-time recovery

ECR Images:
  - Lifecycle policy keeps last 10 images
  - Can rollback to any previous version

EKS Cluster:
  - Pulumi state in cloud
  - Infrastructure as code
```

### Recovery Procedures
```
1. Cluster Failure:
   - Pulumi up (recreates cluster)
   - kubectl apply -f k8s/ (redeploy apps)
   - Time: 15-20 minutes

2. Pod Failure:
   - Kubernetes auto-restarts
   - Time: < 1 minute

3. Node Failure:
   - Kubernetes reschedules pods
   - Cluster autoscaler adds nodes
   - Time: 2-5 minutes

4. Database Restore:
   - Restore from backup
   - Update DATABASE_URL
   - Restart pods
```

## Cost Breakdown

### Monthly Costs (Estimated)

```
EKS Control Plane:
  - $0.10/hour × 730 hours = $73/month

Worker Nodes (2 × t3.medium):
  - $0.0416/hour × 2 × 730 hours = $61/month

Load Balancer:
  - Classic LB: ~$18/month
  - Data processing: ~$5/month

ECR Storage:
  - 500MB × $0.10/GB = $0.05/month

Data Transfer:
  - ~$5/month

CloudWatch:
  - Logs: ~$2/month
  - Metrics: ~$3/month

Monitoring (Self-hosted):
  - Prometheus/Grafana: $0 (runs on your machine via Docker Compose)
  - Storage: Minimal (local volumes)

Total: ~$167/month
```

### Cost Optimization
1. Use Spot Instances for worker nodes (~70% savings)
2. Right-size instance types
3. Enable cluster autoscaler
4. Use Fargate for EKS (pay per pod)
5. Clean up unused resources
6. Use Reserved Instances for production

## Monitoring & Observability

### Integrated Monitoring Stack (Docker Compose)

The application includes Prometheus and Grafana running via Docker Compose for monitoring:

#### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['fastapi:8000']  # Local: Docker network
        # For EKS: Update to Load Balancer URL
    metrics_path: '/metrics'
```

#### FastAPI Metrics Endpoint
The application exposes metrics at `/metrics` using `starlette-exporter`:
```python
from starlette_exporter import PrometheusMiddleware, handle_metrics

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)
```

**Available Metrics:**
- `starlette_requests_total` - Total number of requests
- `starlette_request_duration_seconds` - Request duration histogram
- `starlette_requests_in_progress` - Current requests being processed

#### Accessing Monitoring Tools
```bash
# Start monitoring stack locally
docker-compose up -d prometheus grafana

# Access Prometheus
http://localhost:9090

# Access Grafana
http://localhost:3001
# Default credentials: admin/admin
```

#### Grafana Dashboards
Create dashboards to visualize:
1. **Request Rate**: `rate(starlette_requests_total[1m])`
2. **Response Time (p95)**: `histogram_quantile(0.95, rate(starlette_request_duration_seconds_bucket[5m]))`
3. **Error Rate**: `rate(starlette_requests_total{status_code=~"5.."}[1m])`
4. **Active Requests**: `starlette_requests_in_progress`

### CloudWatch Container Insights (Optional)
```bash
# Enable Container Insights for EKS
aws eks update-cluster-config \
  --name fastapi-app-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator"],"enabled":true}]}'
```

### Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EKS Cluster                          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │ FastAPI Pod  │  │ FastAPI Pod  │                   │
│  │ /metrics     │  │ /metrics     │                   │
│  └──────┬───────┘  └──────┬───────┘                   │
│         │                  │                            │
│         └──────────┬───────┘                            │
│                    │                                    │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ (via Load Balancer)
                     │
         ┌───────────▼──────────────┐
         │   Prometheus Container   │
         │   - Scrapes /metrics     │
         │   - Stores time-series   │
         │   - Port: 9090           │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │    Grafana Container     │
         │   - Visualizes metrics   │
         │   - Dashboards & alerts  │
         │   - Port: 3001           │
         └──────────────────────────┘
```

### Useful kubectl Commands
```bash
# View logs
kubectl logs -f deployment/fastapi-deployment

# Check pod status
kubectl get pods -o wide

# Describe pod
kubectl describe pod <pod-name>

# Execute into pod
kubectl exec -it <pod-name> -- /bin/bash

# View events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top nodes
kubectl top pods
```

## Troubleshooting Guide

### Pods Not Starting
```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# Common issues:
# - Image pull errors (check ECR permissions)
# - Resource limits (increase requests/limits)
# - Health check failures (check /health endpoint)
```

### Load Balancer Not Provisioning
```bash
# Check service
kubectl describe service fastapi-service

# Check events
kubectl get events | grep fastapi-service

# Common issues:
# - Subnet tags missing
# - IAM permissions
# - Security group rules
```

### High Latency
```bash
# Check pod metrics
kubectl top pods

# Check node metrics
kubectl top nodes

# View logs
kubectl logs -f deployment/fastapi-deployment

# Common issues:
# - Database slow queries
# - Insufficient resources
# - Network latency
```

## Security Best Practices

### Network Security
- ✅ Worker nodes in public subnets with security groups
- ✅ Load Balancer as single entry point
- ✅ Security groups restrict traffic
- ✅ Network policies (can be added)

### Pod Security
- ✅ Non-root containers
- ✅ Read-only root filesystem (can be added)
- ✅ Resource limits defined
- ✅ Security context (can be enhanced)

### Access Control
- ✅ IAM roles for service accounts (IRSA)
- ✅ RBAC for kubectl access
- ✅ No hardcoded credentials
- ✅ Secrets management (can use AWS Secrets Manager)

### Image Security
- ✅ ECR image scanning enabled
- ✅ Lifecycle policy for old images
- ✅ Private registry
- ✅ Image pull secrets

## Future Enhancements

1. **Service Mesh (Istio/Linkerd)**
   - Advanced traffic management
   - mTLS between services
   - Observability

2. **GitOps (ArgoCD/Flux)**
   - Automated deployments
   - Declarative configuration
   - Drift detection

3. **Advanced Monitoring**
   - Distributed tracing (Jaeger)
   - Log aggregation (ELK/Loki)
   - Custom metrics

4. **Security Enhancements**
   - Pod Security Policies
   - Network Policies
   - OPA/Gatekeeper
   - Falco runtime security

5. **Performance**
   - Horizontal Pod Autoscaler
   - Vertical Pod Autoscaler
   - Cluster Autoscaler
   - Pod Disruption Budgets
