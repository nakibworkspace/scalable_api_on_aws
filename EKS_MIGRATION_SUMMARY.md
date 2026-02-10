# EKS Migration Summary

This document summarizes the changes made to migrate from ECS to EKS deployment.

## Files Modified

### 1. `infra/__main__.py`
**Changes:**
- Removed ECS-specific resources (ECS Cluster, Task Definitions, ALB, Target Groups, Security Groups)
- Added EKS cluster using `pulumi-eks` package
- Created VPC with public subnets manually (instead of using awsx)
- Added Internet Gateway and Route Tables for EKS networking
- Kept ECR repository unchanged
- Updated exports to include `kubeconfig` and `cluster_name`

**Key Resources:**
- VPC with 2 public subnets in different AZs
- Internet Gateway and Route Tables
- EKS Cluster with 2 t3.medium worker nodes
- ECR Repository with lifecycle policy

### 2. `infra/requirements.txt`
**Changes:**
- Removed `pulumi-awsx` dependency
- Added `pulumi-eks>=2.0.0,<3.0.0`
- Added `pulumi-kubernetes>=4.0.0,<5.0.0`

### 3. `infra/Pulumi.yaml`
**Changes:**
- Updated project name to `fastapi-app`
- Updated description to mention EKS
- Added project tag

### 4. `.github/workflows/deploy.yml`
**Changes:**
- Renamed workflow from "Deploy to AWS ECS" to "Deploy to AWS EKS"
- Added kubectl configuration step using Pulumi kubeconfig output
- Replaced ECS service update with Kubernetes deployment update
- Added steps to:
  - Apply Kubernetes manifests (deployment.yaml and service.yaml)
  - Restart deployment to pull new image
  - Wait for rollout completion
- Updated final output to show Kubernetes service details

### 5. `k8s/deployment.yaml` (NEW)
**Purpose:** Kubernetes Deployment manifest for FastAPI application

**Features:**
- 2 replicas for high availability
- Container image from ECR (placeholder replaced by CI/CD)
- Environment variable for DATABASE_URL
- Liveness probe on /health endpoint
- Readiness probe on /health endpoint
- Resource requests and limits

### 6. `k8s/service.yaml` (NEW)
**Purpose:** Kubernetes Service manifest to expose the application

**Features:**
- Type: LoadBalancer (creates AWS ELB)
- Exposes port 80, routes to container port 8000
- Selector matches deployment labels

### 7. `documentation.md`
**Changes:**
- Updated all references from ECS to EKS
- Added new Chapter 6: Kubernetes Deployment
- Renumbered Chapter 6 (CI/CD) to Chapter 7
- Updated learning objectives to include Kubernetes
- Added kubectl installation to prerequisites
- Updated infrastructure deployment section
- Added Kubernetes concepts and manifests
- Updated troubleshooting section with EKS/Kubernetes issues
- Updated architecture diagram

## Deployment Flow

### Old (ECS):
1. Build Docker image → Push to ECR
2. Pulumi deploys ECS cluster, ALB, Task Definition
3. ECS service pulls image and runs tasks
4. ALB routes traffic to ECS tasks

### New (EKS):
1. Build Docker image → Push to ECR
2. Pulumi deploys EKS cluster, VPC, worker nodes
3. Configure kubectl with cluster credentials
4. Apply Kubernetes manifests (Deployment, Service)
5. Kubernetes creates pods and LoadBalancer service
6. AWS ELB routes traffic to pods

## Key Differences

| Aspect | ECS | EKS |
|--------|-----|-----|
| Orchestration | AWS-managed ECS | Kubernetes on AWS |
| Deployment | Task Definitions | Kubernetes Deployments |
| Networking | ALB + Target Groups | Kubernetes Service (LoadBalancer) |
| Scaling | ECS Service | Kubernetes ReplicaSets |
| Configuration | Task Definition JSON | Kubernetes YAML manifests |
| CLI Tool | AWS CLI | kubectl |

## Testing the Deployment

After deployment, verify with:

```bash
# Check cluster access
kubectl get nodes

# Check pods
kubectl get pods

# Check service
kubectl get service fastapi-service

# Get Load Balancer URL
LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test application
curl http://$LB_URL/health
curl http://$LB_URL/items
```

## Rollback Plan

If issues occur, you can:

1. **Rollback Kubernetes deployment:**
   ```bash
   kubectl rollout undo deployment fastapi-deployment
   ```

2. **Rollback infrastructure:**
   ```bash
   cd infra
   pulumi stack select dev
   pulumi refresh
   pulumi destroy  # if needed
   ```

3. **Use previous image:**
   ```bash
   kubectl set image deployment/fastapi-deployment fastapi=<ECR_URL>:<previous-tag>
   ```

## Cost Considerations

EKS costs more than ECS:
- EKS Control Plane: ~$0.10/hour (~$73/month)
- Worker Nodes: EC2 instance costs (t3.medium ~$0.0416/hour per node)
- ECS has no control plane cost, only EC2/Fargate costs

For production, consider:
- Using Spot instances for worker nodes
- Cluster autoscaling
- Right-sizing instance types
- Using Fargate for EKS (serverless)

## Next Steps

1. Configure horizontal pod autoscaling (HPA)
2. Add Ingress controller for advanced routing
3. Implement network policies for security
4. Set up cluster monitoring with Prometheus Operator
5. Configure persistent volumes for stateful workloads
6. Implement GitOps with ArgoCD or Flux
