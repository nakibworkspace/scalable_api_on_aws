# Setup Guide - Using External PostgreSQL Database

Since you have your own PostgreSQL database, follow these steps to deploy.

## Prerequisites ✅
- [x] AWS CLI configured (`aws configure`)
- [x] Pulumi CLI installed and logged in
- [x] Your PostgreSQL database URL ready

## Step 1: Create Environment File

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your PostgreSQL URL:

```bash
# Your PostgreSQL database URL
DATABASE_URL=postgresql://username:password@your-db-host:5432/your-db-name
```

**Example formats:**
```bash
# AWS RDS
DATABASE_URL=postgresql://admin:mypassword@mydb.abc123.us-east-1.rds.amazonaws.com:5432/myapp

# Heroku Postgres
DATABASE_URL=postgresql://user:pass@ec2-xxx.compute-1.amazonaws.com:5432/dbname

# Supabase
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# Local or self-hosted
DATABASE_URL=postgresql://user:pass@192.168.1.100:5432/mydb
```

## Step 2: Test Database Connection Locally

```bash
# Install dependencies
pip install -r app/requirements.txt

# Test connection
python -c "
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
print('✅ Database connection successful!')
conn.close()
"
```

## Step 3: Initialize Database Schema

Run this to create the `items` table in your database:

```bash
python -c "
from app.main import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database tables created!')
"
```

## Step 4: Test Locally (Optional)

Test the FastAPI app locally before deploying to AWS:

```bash
# Start just FastAPI (no PostgreSQL container needed)
uvicorn app.main:app --reload

# In another terminal, test it
curl http://localhost:8000/health
curl http://localhost:8000/

# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","description":"Testing external DB"}'

# List items
curl http://localhost:8000/items
```

## Step 5: Initialize Pulumi Stack

```bash
cd infra

# Initialize stack
pulumi stack init production

# Set AWS region
pulumi config set aws:region us-east-1

# Set your database URL (stored encrypted)
pulumi config set --secret database-url "postgresql://username:password@your-db-host:5432/your-db-name"
```

**Important:** Replace the database URL with your actual credentials!

## Step 6: Preview Infrastructure

See what Pulumi will create:

```bash
pulumi preview
```

This will show:
- VPC with subnets
- ECS Cluster
- Application Load Balancer
- ECR Repository
- EFS for Prometheus/Grafana data
- Security groups
- IAM roles

**Estimated cost:** ~$70-100/month

## Step 7: Deploy Infrastructure

```bash
pulumi up
```

Type `yes` when prompted. This takes about 10-15 minutes.

Save the outputs:
```bash
pulumi stack output app_url > ../app-url.txt
pulumi stack output ecr_repository_url > ../ecr-url.txt
cd ..
```

## Step 8: Build and Push Docker Image

```bash
# Get ECR URL
ECR_URL=$(cat ecr-url.txt)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build image
docker build -t fastapi-app .

# Tag and push
docker tag fastapi-app:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

## Step 9: Deploy to ECS

Force ECS to pull the new image:

```bash
CLUSTER_NAME=$(cd infra && pulumi stack output cluster_name)

aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service fastapi-app-service \
  --force-new-deployment \
  --region us-east-1
```

Wait for deployment to complete:

```bash
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services fastapi-app-service \
  --region us-east-1
```

## Step 10: Test Your Deployment

```bash
APP_URL=$(cat app-url.txt)

# Test health endpoint
curl $APP_URL/health

# Test API
curl $APP_URL/

# Create an item
curl -X POST $APP_URL/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Production Item","description":"From AWS!"}'

# List items
curl $APP_URL/items

# View API docs
echo "Open in browser: $APP_URL/docs"

# View Prometheus
echo "Prometheus: $APP_URL/prometheus"

# View Grafana
echo "Grafana: $APP_URL/grafana (admin/admin)"
```

## Step 11: Verify Database

Check that data is in your PostgreSQL database:

```bash
# Connect to your database and run:
SELECT * FROM items;
```

You should see the items you created!

## Troubleshooting

### Issue: Database connection fails

**Check 1:** Verify your database allows connections from AWS
```bash
# Your database must allow connections from the ECS tasks
# Check your database firewall/security group settings
```

**Check 2:** Test connection from AWS
```bash
# View ECS task logs
aws logs tail /aws/ecs/fastapi-app-logs --follow --region us-east-1
```

**Check 3:** Verify DATABASE_URL is correct
```bash
cd infra
pulumi config get database-url
```

### Issue: ECS task won't start

```bash
# Check task status
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services fastapi-app-service \
  --region us-east-1

# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow --region us-east-1
```

### Issue: Can't access the application

```bash
# Check ALB status
aws elbv2 describe-load-balancers --region us-east-1

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names fastapi-app-fastapi-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text \
    --region us-east-1) \
  --region us-east-1
```

## Database Security Best Practices

### 1. Use SSL/TLS for Database Connection

Update your DATABASE_URL to use SSL:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 2. Whitelist ECS Task IPs

If your database has IP restrictions:
- Get the NAT Gateway IP from Pulumi outputs
- Add it to your database's allowed IP list

### 3. Use AWS Secrets Manager (Optional)

Instead of storing DATABASE_URL in Pulumi config:

```python
# In infra/__main__.py
secret = aws.secretsmanager.Secret("db-secret")
secret_version = aws.secretsmanager.SecretVersion(
    "db-secret-version",
    secret_id=secret.id,
    secret_string=database_url,
)

# Reference in task definition
"secrets": [
    {
        "name": "DATABASE_URL",
        "valueFrom": secret.arn
    }
]
```

## Next Steps

1. ✅ Set up GitHub Actions for CI/CD (see `.github/workflows/`)
2. ✅ Configure custom domain and SSL
3. ✅ Set up database backups
4. ✅ Configure auto-scaling
5. ✅ Add monitoring alerts
6. ✅ Implement authentication

## Useful Commands

```bash
# View all Pulumi outputs
cd infra && pulumi stack output

# Update infrastructure
cd infra && pulumi up

# View ECS service status
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services fastapi-app-service

# Scale service
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service fastapi-app-service \
  --desired-count 2

# View logs
aws logs tail /aws/ecs/fastapi-app-logs --follow

# Rollback deployment
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service fastapi-app-service \
  --task-definition <previous-task-definition-arn>
```

## Cleanup

When you're done testing:

```bash
# Destroy all AWS resources
cd infra
pulumi destroy

# This will delete:
# - ECS Service and Cluster
# - Load Balancer
# - VPC and networking
# - EFS storage
# - ECR repository
# Note: Your external database is NOT affected
```

## Cost Optimization

- Use Fargate Spot for non-production: Save up to 70%
- Reduce task count to 0 when not in use
- Delete old ECR images
- Use smaller task sizes (0.25 vCPU, 0.5GB RAM)

## Support

- Check logs: `aws logs tail /aws/ecs/fastapi-app-logs --follow`
- Review Pulumi state: `cd infra && pulumi stack`
- Test database: Use the connection test script above
- Open an issue if you need help

---

**You're all set!** Your FastAPI app is now running on AWS ECS with your external PostgreSQL database. 🚀
