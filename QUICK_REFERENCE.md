# Quick Reference - External PostgreSQL Setup

## 🚀 Quick Deploy (Copy & Paste)

```bash
# 1. Set your database URL
export DATABASE_URL="postgresql://user:pass@your-host:5432/dbname"

# 2. Test database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.connect(); print('✅ Connected!')"

# 3. Initialize Pulumi
cd infra
pulumi stack init production
pulumi config set aws:region us-east-1
pulumi config set --secret database-url "$DATABASE_URL"

# 4. Deploy infrastructure
pulumi up --yes

# 5. Build and push Docker image
cd ..
ECR_URL=$(cd infra && pulumi stack output ecr_repository_url)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
docker build -t fastapi-app .
docker tag fastapi-app:latest $ECR_URL:latest
docker push $ECR_URL:latest

# 6. Deploy to ECS
CLUSTER=$(cd infra && pulumi stack output cluster_name)
aws ecs update-service --cluster $CLUSTER --service fastapi-app-service --force-new-deployment --region us-east-1

# 7. Get your app URL
cd infra && pulumi stack output app_url
```

## 📋 Configuration Checklist

- [ ] AWS CLI configured (`aws configure`)
- [ ] Pulumi logged in (`pulumi login`)
- [ ] PostgreSQL database URL ready
- [ ] Database allows connections from AWS
- [ ] Database has SSL enabled (recommended)

## 🔑 Database URL Formats

```bash
# Standard format
postgresql://username:password@hostname:5432/database

# With SSL (recommended)
postgresql://username:password@hostname:5432/database?sslmode=require

# AWS RDS
postgresql://admin:pass@mydb.abc123.us-east-1.rds.amazonaws.com:5432/myapp

# Supabase
postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres

# Heroku
postgresql://user:pass@ec2-xxx.compute-1.amazonaws.com:5432/dbname
```

## 🛠️ Common Commands

### Pulumi
```bash
cd infra

# View current stack
pulumi stack

# View outputs
pulumi stack output

# Update infrastructure
pulumi up

# Destroy everything
pulumi destroy
```

### AWS ECS
```bash
# View service status
aws ecs describe-services --cluster <cluster-name> --services fastapi-app-service

# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Scale service
aws ecs update-service --cluster <cluster-name> --service fastapi-app-service --desired-count 2

# Force new deployment
aws ecs update-service --cluster <cluster-name> --service fastapi-app-service --force-new-deployment
```

### Docker
```bash
# Build
docker build -t fastapi-app .

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ecr-url>

# Push
docker tag fastapi-app:latest <ecr-url>:latest
docker push <ecr-url>:latest
```

### Testing
```bash
# Test locally
uvicorn app.main:app --reload

# Test deployed app
curl $(cd infra && pulumi stack output app_url)/health
curl $(cd infra && pulumi stack output app_url)/docs
```

## 🐛 Troubleshooting

### Database connection fails
```bash
# Check DATABASE_URL
cd infra && pulumi config get database-url

# View ECS logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Test connection locally
python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); engine.connect()"
```

### ECS task won't start
```bash
# Check task status
aws ecs list-tasks --cluster <cluster-name>
aws ecs describe-tasks --cluster <cluster-name> --tasks <task-id>

# Check logs
aws logs tail /aws/ecs/fastapi-app-logs --follow
```

### Can't access application
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn <tg-arn>

# Check security groups
aws ec2 describe-security-groups --filters "Name=tag:Name,Values=*fastapi*"
```

## 📊 Monitoring

```bash
# Application
http://<alb-url>/

# API Docs
http://<alb-url>/docs

# Health Check
http://<alb-url>/health

# Metrics
http://<alb-url>/metrics

# Prometheus
http://<alb-url>/prometheus

# Grafana
http://<alb-url>/grafana
# Login: admin/admin
```

## 💰 Cost Estimate

| Resource | Monthly Cost |
|----------|--------------|
| ECS Fargate (1 task) | ~$25 |
| ALB | ~$20 |
| NAT Gateway | ~$35 |
| EFS | ~$3 |
| Data Transfer | ~$10 |
| **Total** | **~$93/month** |

## 🔒 Security Checklist

- [ ] Database uses SSL/TLS
- [ ] Database password is strong
- [ ] DATABASE_URL stored as Pulumi secret
- [ ] Database firewall allows only ECS tasks
- [ ] ECS tasks in private subnets
- [ ] Security groups follow least privilege
- [ ] CloudWatch logs enabled

## 🎯 Next Steps

1. Set up GitHub Actions CI/CD
2. Configure custom domain + SSL
3. Enable auto-scaling
4. Set up database backups
5. Add monitoring alerts
6. Implement authentication

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [README.md](README.md) - Project overview
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Advanced deployment
- [LAB_EXERCISES.md](LAB_EXERCISES.md) - Hands-on exercises

## 🆘 Getting Help

1. Check logs: `aws logs tail /aws/ecs/fastapi-app-logs --follow`
2. Review Pulumi state: `cd infra && pulumi stack`
3. Test database connection locally
4. Check AWS Console for resource status
5. Open a GitHub issue

---

**Quick Links:**
- AWS Console: https://console.aws.amazon.com/ecs
- Pulumi Console: https://app.pulumi.com
- Your App: Run `cd infra && pulumi stack output app_url`
