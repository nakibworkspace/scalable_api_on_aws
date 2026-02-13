# Building a Production-Ready FastAPI Application with ML Model Deployment

## Introduction

This lab teaches you to build a production-grade FastAPI application that serves machine learning models with proper database integration, containerization, and automated deployment to AWS EC2. You will create a complete system that handles CRUD operations, sentiment analysis predictions, and health monitoring.

Approach: Rather than building isolated components, you will create one cohesive application that progressively adds production features. By the end, you will have a fully functional FastAPI service with ML capabilities, deployed on AWS infrastructure with automated CI/CD pipelines.

## Learning Objectives

By the end of this lab, you will be able to:

1. Create a FastAPI application with database integration using SQLAlchemy
2. Implement CRUD operations with proper validation using Pydantic
3. Integrate a machine learning model for sentiment analysis
4. Load ML models efficiently using startup hooks
5. Containerize the application using Docker
6. Deploy infrastructure to AWS using Pulumi (EC2, ECR, VPC)
7. Set up automated CI/CD pipelines with GitHub Actions
8. Test API endpoints and verify database operations

**Prerequisites:** Basic Python knowledge, familiarity with REST APIs, and basic understanding of Docker concepts.

## Prologue: The Challenge

You join a development team at a growing startup. The team has built a FastAPI application that manages items in a database and provides sentiment analysis for customer feedback. Currently, the application runs only on developers' local machines. The product team cannot access it for testing. The operations team has no visibility into system health. Deployment requires manual steps that often fail.

Your task: Transform this local application into a production-ready service deployed on AWS with automated deployments, monitoring, and database management.

This system will provide:

- Reliable database connectivity with connection pooling
- CRUD operations for item management
- ML-powered sentiment analysis
- Automated schema migrations
- Container-based deployment for consistency
- Infrastructure as code for reproducibility
- Automated testing and deployment pipelines

## Environment Setup

This lab assumes you have access to:

- AWS account with appropriate permissions
- GitHub repository for code hosting
- Pulumi account for infrastructure state management
- PostgreSQL database (external or RDS)

Required tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip unzip

# Install Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
```

Create project structure:

```bash
mkdir -p app infra migrations monitoring .github/workflows
```

## Chapter 1: Building the FastAPI Foundation

Every production application begins with a solid foundation. Before adding business logic, you establish health checks and basic routing. These operational endpoints allow monitoring systems to verify the service is running.

### 1.1 What You Will Build

A FastAPI application with health checks and database connectivity. This forms the foundation for all subsequent features.

Key Concept: FastAPI uses Python type hints for automatic validation, documentation generation, and IDE support. SQLAlchemy provides database abstraction.

### 1.2 Think First: Database Connection Management

Before implementing, consider these questions:

**Question 1:** Why should database credentials be stored in environment variables rather than hardcoded in the application?

**Question 2:** What happens if the database connection fails during application startup?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Environment variables allow different configurations for development, staging, and production without code changes. They prevent credentials from being committed to version control, reducing security risks.

**Answer 2:** Without proper error handling, the application would crash. Production systems need graceful degradation—the process should start but health checks should report unhealthy status until the database connection is established.

</details>

### 1.3 Implementation: Create the FastAPI Application

Create `app/main.py`. Complete the missing parts:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pydantic import BaseModel
import os

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL') or "___"  # Q1: Default PostgreSQL URL format?

engine = create_engine(___)  # Q2: What variable contains the database URL?
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class Item(Base):
    __tablename__ = "items"
    id = Column(___, primary_key=True, index=True)  # Q3: What type for ID?
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas
class ItemCreate(BaseModel):
    name: str
    description: str

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

# FastAPI Application
app = FastAPI(title="Scalable FastAPI on AWS", version="1.0.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.___("/")  # Q4: What HTTP method for retrieving data?
def read_root():
    return {"status": "online", "service": "FastAPI on AWS EC2", "version": "1.0.0"}

@app.get("/health")
def health_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.___()  # Q5: What method releases the database connection?
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
```

**Hints:**
- PostgreSQL URL format: `postgresql://user:password@host:port/database`
- Use `DATABASE_URL` variable for the engine
- ID columns are typically `Integer` type
- GET method retrieves data without modification
- Always close database connections with `close()`

<details>
<summary>Click to see the complete solution</summary>

```python
DATABASE_URL = os.getenv('DATABASE_URL') or "postgresql://user:pass@localhost:5432/appdb"
engine = create_engine(DATABASE_URL)
id = Column(Integer, primary_key=True, index=True)
@app.get("/")
db.close()
```

</details>

### 1.4 Understanding the Code

Match each component to its purpose:

| Component | Purpose (A-E) |
|-----------|---------------|
| `Base.metadata.create_all()` | ___ |
| `SessionLocal()` | ___ |
| `db.close()` | ___ |
| `HTTPException` | ___ |
| `@app.on_event("startup")` | ___ |

**Options:**
- A: Creates database tables from model definitions
- B: Creates a new database session
- C: Releases database connection
- D: Returns HTTP error response
- E: Runs code when application starts

<details>
<summary>Click to check your answers</summary>

- `Base.metadata.create_all()` → A: Creates database tables from model definitions
- `SessionLocal()` → B: Creates a new database session
- `db.close()` → C: Releases database connection
- `HTTPException` → D: Returns HTTP error response
- `@app.on_event("startup")` → E: Runs code when application starts

</details>

### 1.5 Create Environment Configuration

Create `.env` file:

```bash
DATABASE_URL=postgresql://postgres:postgres@your-db-host:5432/postgres
```

Create `app/requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic-settings==2.1.0
```

### 1.6 Test Locally

Install dependencies and run:

```bash
pip install -r app/requirements.txt
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 1.7 Checkpoint

**Predict:** What will the health check return if the database is unreachable?

<details>
<summary>Click to verify</summary>

```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "connection error message"
}
```

The health check catches the exception and returns an unhealthy status instead of crashing.

</details>

Test the endpoints:

```bash
# Test root endpoint
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/health
```

**Self-Assessment:**
- [ ] Application starts without errors
- [ ] Health endpoint returns database connection status
- [ ] You understand why database sessions must be closed
- [ ] You can explain the difference between healthy and unhealthy responses

## Chapter 2: Implementing CRUD Operations

The catalog needs functionality to create, read, update, and delete items. These CRUD operations form the core of most web applications. Proper error handling becomes essential—when a requested item does not exist, the API responds with a clear 404 status rather than failing silently.

### 2.1 What You Will Build

Add endpoints to create items, list all items, and retrieve specific items. This teaches you to:

- Use POST for creating resources
- Handle path parameters (`{item_id}`)
- Return appropriate HTTP status codes
- Manage database sessions properly

### 2.2 Think First: HTTP Methods and Status Codes

**Question 1:** What is the difference between GET and POST methods?

**Question 2:** What HTTP status code should be returned when successfully creating a new resource?

<details>
<summary>Click to review answers</summary>

**Answer 1:** GET retrieves data without modifying server state (idempotent). POST creates new resources and modifies server state (not idempotent).

**Answer 2:** 201 (Created) indicates successful resource creation. 200 (OK) is for successful retrieval.

</details>

### 2.3 Implementation: Add CRUD Endpoints

Add these endpoints to your `app/main.py` (after the health check):

```python
@app.post("/items", response_model=ItemResponse, status_code=___)  # Q1: Status code for creation?
def create_item(item: ItemCreate):
    db = SessionLocal()
    try:
        db_item = Item(name=item.name, description=item.description)
        db.___(___)  # Q2: What method adds item to session?
        db.___()  # Q3: What method persists changes?
        db.refresh(db_item)
        return db_item
    finally:
        db.close()

@app.get("/items", response_model=list[ItemResponse])
def list_items():
    db = SessionLocal()
    try:
        items = db.query(Item).___()  # Q4: What method retrieves all records?
        return items
    finally:
        db.close()

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id).___()  # Q5: Get first result?
        if not item:
            raise HTTPException(status_code=___, detail="Item not found")  # Q6: Status for not found?
        return item
    finally:
        db.close()
```

**Hints:**
- 201 status code means "Created"
- `add()` adds objects to the session
- `commit()` persists changes to database
- `all()` retrieves all matching records
- `first()` retrieves the first matching record
- 404 status code means "Not Found"

<details>
<summary>Click to see the complete solution</summary>

```python
status_code=201
db.add(db_item)
db.commit()
items = db.query(Item).all()
item = db.query(Item).filter(Item.id == item_id).first()
raise HTTPException(status_code=404, detail="Item not found")
```

</details>

### 2.4 Predict the Output

Before running the tests, predict what each command will return:

**Test A:** `curl -X POST http://localhost:8000/items -H "Content-Type: application/json" -d '{"name": "Test Item", "description": "This is a test"}'`

Your prediction: _______________

**Test B:** `curl http://localhost:8000/items`

Your prediction: _______________

**Test C:** `curl http://localhost:8000/items/999`

Your prediction: _______________

### 2.5 Restart and Test

Stop your server (Ctrl+C) and restart:

```bash
python3 main.py
```

Run the tests:

```bash
# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "This is a test"}'
```

<details>
<summary>Click to see expected output</summary>

```json
{
  "id": 1,
  "name": "Test Item",
  "description": "This is a test",
  "created_at": "2024-01-15T10:30:00"
}
```

</details>

```bash
# List all items
curl http://localhost:8000/items
```

<details>
<summary>Click to see expected output</summary>

```json
[
  {
    "id": 1,
    "name": "Test Item",
    "description": "This is a test",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

</details>

```bash
# Get non-existent item
curl http://localhost:8000/items/999
```

<details>
<summary>Click to see expected output</summary>

```json
{
  "detail": "Item not found"
}
```

Status code: 404

</details>

### 2.6 Checkpoint

**Self-Assessment:**
- [ ] POST endpoint creates items and returns 201 status
- [ ] GET /items returns all items in the database
- [ ] GET /items/{id} returns specific item or 404
- [ ] You understand why we use `finally` blocks for database cleanup
- [ ] You can explain the difference between 200, 201, and 404 status codes

## Chapter 3: Integrating Machine Learning Models

Production ML systems require more than just training models—they need reliable serving infrastructure. A model that works perfectly in a Jupyter notebook becomes valuable only when it can receive requests, make predictions, and return results at scale.

### 3.1 What You Will Build

A sentiment analysis model integrated into the FastAPI application with endpoints for predictions and model information.

Key Concept: ML models in production are loaded once at startup and kept in memory. This avoids the overhead of loading the model on every request, which would create unacceptable latency.

### 3.2 Think First: Model Loading Strategy

**Question 1:** Why load the ML model at application startup instead of on each prediction request?

**Question 2:** What should the API return if the model fails to load?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Loading at startup provides:
- Faster predictions (no load time per request)
- Consistent memory usage
- Fail-fast behavior (know immediately if model is broken)
- Better resource utilization

Loading a 100MB model on every request would add seconds of latency and exhaust memory.

**Answer 2:** The API should:
- Start successfully (don't crash)
- Return 503 (Service Unavailable) for prediction requests
- Include model status in health checks
- Log clear error messages for debugging

</details>

### 3.3 Prepare the Model

Create `app/train_model.py`:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

# Training data
texts = [
    "This product is amazing and works great",
    "Excellent quality and fast shipping",
    "Best purchase I've made this year",
    "Terrible product, waste of money",
    "Poor quality and broke after one use",
    "Very disappointed with this purchase",
]
labels = [1, 1, 1, 0, 0, 0]  # 1=positive, 0=negative

# Train pipeline
model = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=100)),
    ('clf', LogisticRegression(random_state=42))
])
model.fit(texts, labels)

# Save model
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/sentiment_model.joblib')
print("Model saved to models/sentiment_model.joblib")
```

Train the model:

```bash
cd app
python3 train_model.py
```

### 3.4 Implementation: Add Model Loading

Add imports to `app/main.py`:

```python
from contextlib import asynccontextmanager
import joblib
from pathlib import Path
```

Add global model variable and lifespan management (before `app = FastAPI(...)`):

```python
# Global model variable
ml_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup, cleanup at shutdown"""
    global ml_model
    model_path = Path("models/sentiment_model.joblib")

    if model_path.exists():
        ml_model = joblib.load(___)  # Q1: What variable contains the path?
        print(f"Model loaded from {model_path}")
    else:
        print(f"Warning: Model not found at {model_path}")

    yield  # Application runs here

    # Cleanup
    ml_model = ___  # Q2: What value indicates no model?
    print("Model unloaded")
```

Update FastAPI initialization:

```python
app = FastAPI(
    title="Scalable FastAPI on AWS",
    version="1.0.0",
    lifespan=___  # Q3: What function manages lifecycle?
)
```

**Hints:**
- Use `model_path` variable for loading
- Set to `None` to indicate no model
- Pass the `lifespan` function to FastAPI

<details>
<summary>Click to see the complete solution</summary>

```python
ml_model = joblib.load(model_path)
ml_model = None
lifespan=lifespan
```

</details>

### 3.5 Implementation: Add Prediction Endpoints

Add prediction schemas and endpoints:

```python
class PredictionRequest(BaseModel):
    text: str

class PredictionResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float

@app.post("/predict", response_model=PredictionResponse)
def predict_sentiment(request: PredictionRequest):
    """Predict sentiment of input text"""
    if ml_model is ___:  # Q1: What value means model not loaded?
        raise HTTPException(status_code=___, detail="Model not loaded")  # Q2: Status for unavailable?

    # Get prediction
    prediction = ml_model.predict([request.text])[0]
    probabilities = ml_model.predict_proba([request.text])[0]
    confidence = float(max(probabilities))

    sentiment = "positive" if prediction == ___ else "negative"  # Q3: What value is positive?

    return PredictionResponse(
        text=request.text,
        sentiment=sentiment,
        confidence=confidence
    )

@app.get("/model/info")
def model_info():
    """Get model information"""
    if ml_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_type": "Sentiment Classifier",
        "algorithm": "Logistic Regression with TF-IDF",
        "status": "loaded"
    }
```

**Hints:**
- `None` indicates no model loaded
- 503 means "Service Unavailable"
- Positive sentiment is labeled as `1`

<details>
<summary>Click to see the complete solution</summary>

```python
if ml_model is None:
raise HTTPException(status_code=503, detail="Model not loaded")
sentiment = "positive" if prediction == 1 else "negative"
```

</details>

### 3.6 Update Health Check

Modify the root endpoint to include ML model status:

```python
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "FastAPI on AWS EC2",
        "version": "1.0.0",
        "ml_model_loaded": ml_model is not None
    }
```

### 3.7 Restart and Test

Update requirements:

```bash
echo "scikit-learn==1.3.2" >> requirements.txt
echo "joblib==1.3.2" >> requirements.txt
pip install scikit-learn joblib
```

Restart the server:

```bash
python3 main.py
```

You should see: `Model loaded from models/sentiment_model.joblib`

### 3.8 Checkpoint

**Predict:** What will this return?

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is absolutely amazing!"}'
```

<details>
<summary>Click to verify</summary>

```json
{
  "text": "This product is absolutely amazing!",
  "sentiment": "positive",
  "confidence": 0.85
}
```

Confidence may vary slightly.

</details>

Test the endpoints:

```bash
# Check model status
curl http://localhost:8000/

# Get model info
curl http://localhost:8000/model/info

# Test positive sentiment
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Excellent product, highly recommend!"}'

# Test negative sentiment
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Terrible quality, complete waste of money"}'
```

**Self-Assessment:**
- [ ] Model loads successfully at startup
- [ ] `/predict` endpoint returns sentiment and confidence
- [ ] `/model/info` endpoint shows model details
- [ ] Root endpoint shows ML model status
- [ ] You understand why models are loaded at startup

## Chapter 4: Containerization with Docker

Containers solve the "works on my machine" problem. By packaging the application with its dependencies, containers ensure consistent behavior across development, testing, and production environments.

### 4.1 What You Will Build

Docker containers for the FastAPI application that include the trained ML model.

Key Concept: Docker images are immutable snapshots of your application and its dependencies. Containers are running instances of images.

### 4.2 Think First: Container Benefits

**Question:** Why containerize an application instead of deploying directly to a server?

<details>
<summary>Click to review answer</summary>

Containers provide:
- Consistency across environments (eliminates configuration drift)
- Isolation from host system dependencies
- Easy scaling (spin up multiple containers)
- Simplified deployment (single artifact to deploy)
- Version control for the entire runtime environment

</details>

### 4.3 Implementation: Create Dockerfile

Create `Dockerfile` in the project root. Complete the missing parts:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and model
COPY app/ .

# Expose port
EXPOSE ___  # Q1: What port does FastAPI use?

# Run the application
CMD ["uvicorn", "main:app", "--host", "___", "--port", "8000"]  # Q2: Host for external access?
```

**Hints:**
- FastAPI runs on port 8000 by default
- Use `0.0.0.0` to bind to all network interfaces in containers

<details>
<summary>Click to see the complete solution</summary>

```dockerfile
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

</details>

### 4.4 Build and Test

Build the image:

```bash
docker build -t fastapi-app .
```

Run the container:

```bash
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@your-db-host:5432/postgres \
  --name fastapi-container \
  fastapi-app
```

Test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/model/info
```

### 4.5 Checkpoint

**Self-Assessment:**
- [ ] Docker image builds successfully
- [ ] Container runs and responds to health checks
- [ ] ML model is included in the container
- [ ] You understand the difference between images and containers

## Epilogue: The Complete System

You have built a production-ready FastAPI application with complete ML integration. The system now provides:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Service status and version |
| GET | `/health` | Database health check |
| GET | `/items` | List all items |
| POST | `/items` | Create new item |
| GET | `/items/{id}` | Get specific item |
| POST | `/predict` | Sentiment prediction |
| GET | `/model/info` | Model information |

### End-to-End Verification

Verify the complete system:

```bash
# Check service status
curl http://localhost:8000/

# Check health
curl http://localhost:8000/health

# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Customer Review", "description": "Product feedback"}'

# List items
curl http://localhost:8000/items

# Get sentiment prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product exceeded my expectations!"}'
```

All commands should succeed without errors.


## Chapter 5: Monitoring with Prometheus and Grafana

Production systems require observability. Prometheus collects metrics and Grafana visualizes them.

### 5.1 Add Metrics to FastAPI

Update `app/requirements.txt`:

```txt
starlette-exporter==0.17.1
```

Update `app/main.py`:

```python
from starlette_exporter import PrometheusMiddleware, handle_metrics

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)
```

### 5.2 Configure Prometheus

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['fastapi:8000']
    metrics_path: '/metrics'
```

### 5.3 Configure Grafana

Create `monitoring/grafana-datasource.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### 5.4 Start Monitoring

```bash
docker-compose up -d

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3001 (admin/admin)
```

**Self-Assessment:**
- [ ] FastAPI exposes /metrics endpoint
- [ ] Prometheus scrapes metrics
- [ ] Grafana connects to Prometheus

## Chapter 6: Infrastructure as Code with Pulumi

Manual infrastructure provisioning is error-prone. Pulumi treats infrastructure as code.

### 6.1 Configure Pulumi

Create `infra/Pulumi.yaml`:

```yaml
name: fastapi-app
runtime: python
description: FastAPI application infrastructure on AWS EC2
```

Create `infra/requirements.txt`:

```
pulumi>=3.0.0,<4.0.0
pulumi-aws>=6.0.0,<7.0.0
```

### 6.2 Define Infrastructure

The `infra/__main__.py` file creates:

- VPC with public subnet
- Internet Gateway and routing
- Security Group (ports 80, 8000, 22)
- ECR repository for Docker images
- IAM role for EC2 with ECR access
- EC2 instance with Docker
- User data script to pull and run containers

### 6.3 Deploy Infrastructure

```bash
pulumi login
cd infra
pulumi stack init dev
pulumi config set aws:region ap-southeast-1
pulumi config set database_url "postgresql://..." --secret
pulumi up --yes
```

Get outputs:

```bash
pulumi stack output instance_public_ip
pulumi stack output ecr_repository_url
```

**Self-Assessment:**
- [ ] Pulumi deploys EC2 infrastructure
- [ ] You can access EC2 instance
- [ ] ECR repository is created

## Chapter 7: EC2 Deployment

Deploy the Docker container to EC2 using the infrastructure created by Pulumi.

### 7.1 Push Image to ECR

```bash
# Get ECR URL
ECR_URL=$(cd infra && pulumi stack output ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region ap-southeast-1 | \\
  docker login --username AWS --password-stdin $(echo $ECR_URL | cut -d'/' -f1)

# Tag and push
docker tag fastapi-app:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

### 7.2 Deploy to EC2

The EC2 instance automatically:
1. Installs Docker
2. Installs AWS CLI
3. Logs into ECR
4. Pulls the latest image
5. Runs the container on port 80

### 7.3 Test Deployment

```bash
# Get EC2 public IP
EC2_IP=$(cd infra && pulumi stack output instance_public_ip)

# Test endpoints
curl http://$EC2_IP/health
curl http://$EC2_IP/model/info
curl -X POST http://$EC2_IP/predict \\
  -H "Content-Type: application/json" \\
  -d '{"text": "This is amazing!"}'
```

**Self-Assessment:**
- [ ] Image pushed to ECR
- [ ] Container running on EC2
- [ ] Application accessible via public IP

## Chapter 8: CI/CD with GitHub Actions

Automated pipelines test code and deploy to AWS automatically.

### 8.1 CI Pipeline

Create `.github/workflows/ci.yml`:

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r app/requirements.txt
        pip install pytest
    
    - name: Run tests
      run: |
        cd app
        pytest test_main.py -v
```

### 8.2 Deployment Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS EC2

on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types:
      - completed
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: ap-southeast-1
  ECR_REPOSITORY: fastapi-app-repo

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name == 'workflow_dispatch' }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Pulumi CLI
      uses: pulumi/actions@v4
    
    - name: Install Pulumi dependencies
      run: |
        cd infra
        pip install -r requirements.txt
    
    - name: Deploy infrastructure with Pulumi
      uses: pulumi/actions@v4
      with:
        command: up
        stack-name: dev
        work-dir: infra
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
    
    - name: Run database migrations
      run: |
        pip install alembic psycopg2-binary sqlalchemy
        alembic upgrade head
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
    
    - name: Get EC2 instance ID
      id: get-instance
      run: |
        cd infra
        INSTANCE_ID=$(pulumi stack output instance_id)
        echo "instance_id=$INSTANCE_ID" >> $GITHUB_OUTPUT
    
    - name: Restart application on EC2
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
      run: |
        INSTANCE_ID=${{ steps.get-instance.outputs.instance_id }}
        
        # Wait for instance to be ready
        aws ec2 wait instance-status-ok --instance-ids $INSTANCE_ID --region ${{ env.AWS_REGION }}
        
        # Send command to pull latest image and restart container
        aws ssm send-command \
          --instance-ids $INSTANCE_ID \
          --document-name "AWS-RunShellScript" \
          --parameters 'commands=[
            "aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin $ECR_REGISTRY",
            "docker pull $ECR_REGISTRY/$ECR_REPOSITORY:latest",
            "docker stop fastapi-app || true",
            "docker rm fastapi-app || true",
            "docker run -d --name fastapi-app --restart unless-stopped -p 80:8000 -e DATABASE_URL=\"${{ secrets.DATABASE_URL }}\" $ECR_REGISTRY/$ECR_REPOSITORY:latest"
          ]' \
          --region ${{ env.AWS_REGION }}
    
    - name: Get deployment URL
      run: |
        cd infra
        echo "Deployment Complete!"
        echo "Application URL: $(pulumi stack output application_url)"
```

**Understanding the Deployment Pipeline:**

This workflow automates the entire deployment process:

1. **Trigger Conditions:**
   - `workflow_run`: Runs after CI Pipeline succeeds on main branch
   - `workflow_dispatch`: Allows manual triggering from GitHub UI

2. **AWS Authentication:**
   - Configures AWS credentials from GitHub secrets
   - Logs into ECR to push Docker images

3. **Docker Image Build:**
   - Builds image with current code
   - Tags with commit SHA (for traceability) and `latest`
   - Pushes both tags to ECR

4. **Infrastructure Deployment:**
   - Installs Pulumi and dependencies
   - Runs `pulumi up` to create/update EC2, VPC, Security Groups, etc.
   - Infrastructure is idempotent (safe to run multiple times)

5. **Database Migrations:**
   - Runs Alembic migrations against production database
   - Ensures schema is up-to-date before deploying new code

6. **Application Deployment:**
   - Gets EC2 instance ID from Pulumi outputs
   - Uses AWS Systems Manager (SSM) to execute commands on EC2
   - Pulls latest Docker image from ECR
   - Stops old container and starts new one
   - Container automatically restarts if it crashes

**Why SSM instead of SSH?**
- No SSH keys to manage
- Works through AWS IAM permissions
- Audit trail of all commands
- No need to open SSH port (22) to the internet

### 8.3 Configure Secrets

Add to GitHub repository (Settings → Secrets):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PULUMI_ACCESS_TOKEN`
- `DATABASE_URL`

### 8.4 Test Pipeline

```bash
git add .
git commit -m "Add CI/CD pipelines"
git push origin main
```

Monitor in GitHub Actions tab.

**Self-Assessment:**
- [ ] CI pipeline runs on push
- [ ] Tests execute automatically
- [ ] Deployment triggers after CI success
- [ ] Application updates on EC2

## Epilogue: The Complete System

You have built a production-ready FastAPI application with complete infrastructure and automation.

| Component | Purpose |
|-----------|---------|
| FastAPI Application | REST API with database integration |
| ML Model | Sentiment analysis predictions |
| PostgreSQL Database | Persistent data storage |
| Alembic | Database migrations |
| Docker | Containerization |
| AWS EC2 | Compute instances |
| AWS ECR | Container registry |
| Pulumi | Infrastructure as code |
| GitHub Actions | Automated CI/CD |
| Prometheus/Grafana | Monitoring |

### End-to-End Verification

```bash
# Get EC2 IP
EC2_IP=$(cd infra && pulumi stack output instance_public_ip)

# Test all endpoints
curl http://$EC2_IP/
curl http://$EC2_IP/health
curl http://$EC2_IP/metrics

# Create item
curl -X POST http://$EC2_IP/items \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Production Item", "description": "Created in production"}'

# Get prediction
curl -X POST http://$EC2_IP/predict \\
  -H "Content-Type: application/json" \\
  -d '{"text": "This product is excellent!"}'
```

## The Principles

1. **Configuration as environment variables** — Never hardcode credentials
2. **Database migrations as code** — Track schema changes with version control
3. **Containers for consistency** — Package applications with dependencies
4. **Infrastructure as code** — Define infrastructure in version-controlled files
5. **Automated testing** — Run tests on every commit
6. **Automated deployment** — Deploy automatically after tests pass
7. **Health checks at every layer** — Application and container health checks
8. **Observability from the start** — Collect metrics and logs from day one
9. **Immutable deployments** — Deploy new containers rather than modifying running ones
10. **Rollback capability** — Tag images and maintain deployment history

## Troubleshooting

### Database Connection Errors

```bash
# Verify database URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Docker Build Failures

```bash
# Verify Dockerfile syntax
docker build -t test .

# Check requirements.txt exists
ls -la app/requirements.txt
```

### EC2 Connection Issues

```bash
# Check instance status
aws ec2 describe-instances --instance-ids <instance-id>

# View instance logs
aws ssm start-session --target <instance-id>
docker logs fastapi-app
```

## Next Steps

1. **Add authentication** — Implement JWT tokens or OAuth2
2. **Implement caching** — Add Redis for frequently accessed data
3. **Set up alerting** — Configure Prometheus Alertmanager
4. **Add more tests** — Increase test coverage
5. **Implement auto-scaling** — Use Auto Scaling Groups
6. **Add load balancing** — Use Application Load Balancer
7. **Implement rate limiting** — Protect against abuse
8. **Set up log aggregation** — Centralize logs with CloudWatch
9. **Add database backups** — Automated backups
10. **Implement secrets management** — Use AWS Secrets Manager

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
