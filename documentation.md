# Building a Production-Ready FastAPI Application on AWS

## Introduction

This lab teaches you to build and deploy a production-grade FastAPI application on AWS infrastructure. You will create a complete system that includes database integration, ML model serving, containerization, infrastructure as code, monitoring, and automated CI/CD pipelines.

Approach: Rather than building isolated components, you will create one cohesive application that progressively adds production features. By the end, you will have a fully deployed FastAPI service running on AWS EC2 with Docker containers from ECR, automated deployments, database migrations, and monitoring dashboards.

## Learning Objectives

By the end of this lab, you will be able to:

1. Create a FastAPI application with database integration using SQLAlchemy
2. Integrate a machine learning model for sentiment analysis
3. Configure PostgreSQL database connections and implement migrations with Alembic
4. Containerize the application using Docker and Docker Compose
5. Deploy infrastructure to AWS using Pulumi (EC2, ECR, VPC)
6. Implement monitoring with Prometheus and Grafana
7. Set up automated CI/CD pipelines with GitHub Actions
8. Test API endpoints and verify database operations
9. Deploy Docker containers to EC2 instances

**Prerequisites:** Basic Python knowledge, familiarity with REST APIs, basic understanding of Docker concepts, and basic AWS knowledge.

## Prologue: The Challenge

You join a development team at a growing startup. The team has built a FastAPI application that manages items in a database and provides sentiment analysis for customer feedback. Currently, the application runs only on developers' local machines. The product team cannot access it for testing. The operations team has no visibility into system health. Deployment requires manual steps that often fail.

Your task: Transform this local application into a production-ready service deployed on AWS with automated deployments, monitoring, and database management.

This system will provide:

- Reliable database connectivity with connection pooling
- Automated schema migrations
- Container-based deployment for consistency
- Infrastructure as code for reproducibility
- Health monitoring and metrics collection
- Automated testing and deployment pipelines

## Environment Setup

This lab assumes you have access to:

- AWS account with appropriate permissions
- GitHub repository for code hosting
- Pulumi account for infrastructure state management
- PostgreSQL database (external or RDS)

Required tools:

\`\`\`bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip unzip

# Install Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic-settings

# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
\`\`\`

Create project structure:

\`\`\`bash
mkdir -p app infra migrations monitoring .github/workflows
\`\`\`

