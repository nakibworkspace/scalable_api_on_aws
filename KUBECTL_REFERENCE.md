# kubectl Quick Reference for FastAPI Deployment

## Setup and Configuration

```bash
# Configure kubectl to use EKS cluster
cd infra
pulumi stack output kubeconfig > kubeconfig.yaml
export KUBECONFIG=$PWD/kubeconfig.yaml

# Verify connection
kubectl cluster-info
kubectl get nodes
```

## Deployment Management

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Get deployment status
kubectl get deployments
kubectl get deployment fastapi-deployment

# Describe deployment (detailed info)
kubectl describe deployment fastapi-deployment

# Check rollout status
kubectl rollout status deployment fastapi-deployment

# Restart deployment (pulls new image)
kubectl rollout restart deployment fastapi-deployment

# Rollback to previous version
kubectl rollout undo deployment fastapi-deployment

# View rollout history
kubectl rollout history deployment fastapi-deployment
```

## Pod Management

```bash
# List all pods
kubectl get pods

# List pods with more details
kubectl get pods -o wide

# Watch pods in real-time
kubectl get pods -w

# Describe a specific pod
kubectl describe pod <pod-name>

# View pod logs
kubectl logs <pod-name>

# Follow logs in real-time
kubectl logs -f <pod-name>

# View logs for all pods with label
kubectl logs -l app=fastapi

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/bash

# View previous container logs (if crashed)
kubectl logs <pod-name> --previous
```

## Service Management

```bash
# List services
kubectl get services
kubectl get svc

# Get service details
kubectl describe service fastapi-service

# Get Load Balancer URL
kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Port forward for local testing
kubectl port-forward service/fastapi-service 8080:80
```

## Scaling

```bash
# Scale deployment
kubectl scale deployment fastapi-deployment --replicas=5

# View current replicas
kubectl get deployment fastapi-deployment

# Autoscale based on CPU
kubectl autoscale deployment fastapi-deployment --min=2 --max=10 --cpu-percent=80
```

## Debugging

```bash
# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check pod events
kubectl describe pod <pod-name> | grep -A 10 Events

# Check resource usage
kubectl top nodes
kubectl top pods

# Get pod YAML
kubectl get pod <pod-name> -o yaml

# Check deployment YAML
kubectl get deployment fastapi-deployment -o yaml
```

## Configuration and Secrets

```bash
# Create secret from literal
kubectl create secret generic db-secret \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/db'

# Create secret from file
kubectl create secret generic db-secret --from-file=.env

# View secrets (values are base64 encoded)
kubectl get secrets
kubectl describe secret db-secret

# Update deployment to use secret
kubectl set env deployment/fastapi-deployment --from=secret/db-secret
```

## Updating the Application

```bash
# Update image
kubectl set image deployment/fastapi-deployment \
  fastapi=<ECR_URL>:new-tag

# Edit deployment directly
kubectl edit deployment fastapi-deployment

# Apply updated manifest
kubectl apply -f k8s/deployment.yaml

# Restart to pull latest image
kubectl rollout restart deployment fastapi-deployment
```

## Cleanup

```bash
# Delete deployment
kubectl delete deployment fastapi-deployment

# Delete service
kubectl delete service fastapi-service

# Delete all resources from manifests
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml

# Delete all resources with label
kubectl delete all -l app=fastapi
```

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kl='kubectl logs'
alias kd='kubectl describe'
alias ka='kubectl apply -f'
alias kdel='kubectl delete'
```

## Common Troubleshooting Commands

```bash
# Pod stuck in Pending
kubectl describe pod <pod-name> | grep -A 5 Events

# Pod in CrashLoopBackOff
kubectl logs <pod-name> --previous
kubectl describe pod <pod-name>

# Service has no endpoints
kubectl get endpoints fastapi-service
kubectl get pods -l app=fastapi

# Load Balancer not provisioning
kubectl describe service fastapi-service
kubectl get events | grep fastapi-service

# Image pull errors
kubectl describe pod <pod-name> | grep -A 5 "Failed to pull image"

# Check if deployment is healthy
kubectl get deployment fastapi-deployment
kubectl rollout status deployment fastapi-deployment
```

## Testing the Application

```bash
# Get Load Balancer URL
LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoint
curl http://$LB_URL/health

# Test API endpoints
curl http://$LB_URL/items

# Create an item
curl -X POST http://$LB_URL/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "Test item"}'

# Load test (requires apache2-utils)
ab -n 1000 -c 10 http://$LB_URL/health
```

## Monitoring

```bash
# Watch pod status
watch kubectl get pods

# Monitor logs from all pods
kubectl logs -f -l app=fastapi --all-containers=true

# Check resource usage
kubectl top pods
kubectl top nodes

# View metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```

## Advanced Operations

```bash
# Drain node for maintenance
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Cordon node (mark unschedulable)
kubectl cordon <node-name>

# Uncordon node
kubectl uncordon <node-name>

# Label pods
kubectl label pods <pod-name> environment=production

# Annotate deployment
kubectl annotate deployment fastapi-deployment description="FastAPI application"

# Get all resources
kubectl get all

# Get resources across all namespaces
kubectl get pods --all-namespaces
```
