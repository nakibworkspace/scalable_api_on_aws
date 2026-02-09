# Quick Start Guide

Get up and running in 10 minutes!

## Local Development (5 minutes)

```bash
# 1. Clone and navigate
git clone <your-repo>
cd <your-repo>

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be ready
sleep 15

# 4. Test the API
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Open in browser

# 5. Create your first item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"My First Item","description":"Hello FastAPI!"}'

# 6. View items
curl http://localhost:8000/items | jq

# 7. Access monitoring
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)
```

## AWS Deployment (15 minutes)

### Prerequisites
```bash
# Install tools (macOS)
brew install awscli pulumi

# Configure AWS
aws configure
```

### Deploy Infrastructure
```bash
# 1. Initialize Pulumi
cd infra
pulumi login
pulumi stack init production
pulumi config set aws:region us-east-1
pulumi config set --secret db-password "YourSecurePassword123!"

# 2. Deploy (takes ~10 minutes)
pulumi up --yes

# 3. Save outputs
pulumi stack output app_url > ../app-url.txt
pulumi stack output ecr_repository_url > ../ecr-url.txt
```

### Deploy Application
```bash
cd ..

# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(cat ecr-url.txt)

# 2. Build and push
docker build -t fastapi-app .
docker tag fastapi-app:latest $(cat ecr-url.txt):latest
docker push $(cat ecr-url.txt):latest

# 3. Update ECS service
aws ecs update-service \
  --cluster $(cd infra && pulumi stack output cluster_name) \
  --service fastapi-app-service \
  --force-new-deployment

# 4. Wait for deployment
aws ecs wait services-stable \
  --cluster $(cd infra && pulumi stack output cluster_name) \
  --services fastapi-app-service

# 5. Test deployment
curl $(cat app-url.txt)/health
```

## GitHub Actions Setup (5 minutes)

```bash
# 1. Add secrets to GitHub repo
# Go to: Settings → Secrets and variables → Actions
# Add:
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - PULUMI_ACCESS_TOKEN
#   - DB_PASSWORD

# 2. Push to GitHub
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo>
git push -u origin main

# 3. Watch the pipeline
# Go to: Actions tab in GitHub
```

## Common Commands

### Local Development
```bash
# Start services
make docker-up

# Stop services
make docker-down

# Run tests
make test

# Format code
make format

# View logs
docker-compose logs -f fastapi
```

### AWS Operations
```bash
# View infrastructure
cd infra && pulumi stack

# Update infrastructure
cd infra && pulumi up

# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Check service status
aws ecs describe-services \
  --cluster $(cd infra && pulumi stack output cluster_name) \
  --services fastapi-app-service

# Scale service
aws ecs update-service \
  --cluster $(cd infra && pulumi stack output cluster_name) \
  --service fastapi-app-service \
  --desired-count 3
```

## Troubleshooting

### Service won't start locally
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down -v
docker-compose up -d
```

### Can't connect to database
```bash
# Check if postgres is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U user -d appdb -c "SELECT 1"
```

### ECS task fails to start
```bash
# Check task logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Describe task
aws ecs list-tasks --cluster <cluster-name>
aws ecs describe-tasks --cluster <cluster-name> --tasks <task-id>
```

### Image push fails
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(cat ecr-url.txt)

# Check repository exists
aws ecr describe-repositories --repository-names fastapi-repo
```

## Next Steps

1. ✅ Complete [LAB_EXERCISES.md](LAB_EXERCISES.md) for hands-on practice
2. ✅ Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
3. ✅ Review [README.md](README.md) for architecture overview
4. ✅ Set up monitoring dashboards in Grafana
5. ✅ Configure SSL/TLS and custom domain
6. ✅ Implement authentication and authorization
7. ✅ Add more features to your API

## Useful Links

- **API Documentation**: http://localhost:8000/docs (local) or http://<alb-url>/docs (AWS)
- **Prometheus**: http://localhost:9090 (local)
- **Grafana**: http://localhost:3000 (local)
- **AWS Console**: https://console.aws.amazon.com/ecs
- **Pulumi Console**: https://app.pulumi.com

## Clean Up

### Local
```bash
docker-compose down -v
docker system prune -a
```

### AWS
```bash
cd infra
pulumi destroy --yes
```

**Warning**: This will delete all AWS resources and data!

## Getting Help

- 📖 Check the [README.md](README.md)
- 🔧 Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 💪 Try [LAB_EXERCISES.md](LAB_EXERCISES.md)
- 🐛 Check logs: `docker-compose logs` or `aws logs tail`
- 💬 Open an issue on GitHub

Happy coding! 🚀
