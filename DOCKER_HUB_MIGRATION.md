# Docker Hub Migration Guide

This project has been updated to use Docker Hub instead of AWS ECR for container image storage.

## Key Changes

### 1. Infrastructure (infra/__main__.py)
- Removed ECR repository creation
- Removed IAM roles and policies for ECR access
- Updated user data script to pull from Docker Hub
- Added `docker_image` configuration parameter

### 2. CI/CD Workflows

#### .github/workflows/ci.yml
- Replaced ECR login with Docker Hub login
- Uses `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
- Pushes images to Docker Hub
- Deploys to EC2 via SSH

#### .github/workflows/deploy.yml
- Updated to use Docker Hub for image storage
- Configures Pulumi with Docker Hub image URL
- Deploys via SSH instead of AWS SSM

### 3. Required GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `DOCKERHUB_USERNAME` - Your Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token (create at hub.docker.com → Account Settings → Security)
- `EC2_HOST` - Your EC2 public IP address
- `EC2_SSH_KEY` - Your EC2 private key (.pem file content)
- `DATABASE_URL` - PostgreSQL connection string
- `PULUMI_ACCESS_TOKEN` - Pulumi access token

## Deployment Workflow

### Manual Deployment

1. **Build and push to Docker Hub:**
```bash
# Login to Docker Hub
docker login

# Build image
docker build -t your-dockerhub-username/fastapi-app:latest .

# Push to Docker Hub
docker push your-dockerhub-username/fastapi-app:latest
```

2. **Configure Pulumi:**
```bash
cd infra
pulumi config set docker_image your-dockerhub-username/fastapi-app:latest
pulumi config set database_url "postgresql://user:pass@host:5432/db" --secret
```

3. **Deploy infrastructure:**
```bash
pulumi up --yes
```

4. **Get EC2 IP and test:**
```bash
EC2_IP=$(pulumi stack output instance_public_ip)
curl http://$EC2_IP/health
```

### Automated Deployment (CI/CD)

1. **Set up GitHub secrets** (see list above)

2. **Generate SSH key for EC2:**
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/fastapi-ec2-key -N ""
```

3. **Configure Pulumi with public key:**
```bash
cd infra
pulumi config set ssh_public_key "$(cat ~/.ssh/fastapi-ec2-key.pub)"
```

4. **Add private key to GitHub secrets:**
```bash
# Copy the entire output including BEGIN and END lines
cat ~/.ssh/fastapi-ec2-key
```
Add this as `EC2_SSH_KEY` secret in GitHub.

5. **Push to main branch:**
```bash
git add .
git commit -m "Deploy with Docker Hub"
git push origin main
```

The CI/CD pipeline will:
- Run tests
- Build Docker image
- Push to Docker Hub
- Deploy to EC2 automatically

## Benefits of Docker Hub

1. **No AWS permissions needed** - No ECR or IAM role management
2. **Simpler setup** - Just Docker Hub credentials
3. **Public or private repos** - Free private repos on Docker Hub
4. **Familiar workflow** - Standard Docker commands
5. **Cross-cloud compatible** - Works with any cloud provider

## Troubleshooting

### Image pull fails on EC2
- Verify Docker Hub image exists: `docker pull your-username/fastapi-app:latest`
- Check Pulumi config: `pulumi config get docker_image -C infra`
- Check EC2 user data logs: `ssh ec2-user@<ip> 'sudo cat /var/log/cloud-init-output.log'`

### CI/CD fails to push
- Verify Docker Hub credentials in GitHub secrets
- Check Docker Hub token has write permissions
- Ensure image name matches your Docker Hub username

### SSH deployment fails
- Verify EC2_SSH_KEY secret contains the full private key
- Check EC2 security group allows SSH (port 22)
- Verify EC2_HOST matches the actual public IP

## Migration from ECR

If you have existing ECR infrastructure:

1. **Pull image from ECR:**
```bash
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <ecr-url>
docker pull <ecr-url>/fastapi-app:latest
```

2. **Tag for Docker Hub:**
```bash
docker tag <ecr-url>/fastapi-app:latest your-dockerhub-username/fastapi-app:latest
```

3. **Push to Docker Hub:**
```bash
docker login
docker push your-dockerhub-username/fastapi-app:latest
```

4. **Update Pulumi and redeploy:**
```bash
cd infra
pulumi config set docker_image your-dockerhub-username/fastapi-app:latest
pulumi up --yes
```

5. **Clean up ECR (optional):**
```bash
aws ecr delete-repository --repository-name fastapi-app-repo --force
```
