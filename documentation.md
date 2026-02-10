# Building a Production-Ready FastAPI Application on AWS

## Introduction

This lab teaches you to build and deploy a production-grade FastAPI application on AWS infrastructure. You will create a complete system that includes database integration, containerization, infrastructure as code, monitoring, and automated CI/CD pipelines.

Approach: Rather than building isolated components, you will create one cohesive application that progressively adds production features. By the end, you will have a fully deployed FastAPI service running on AWS EKS (Kubernetes) with automated deployments, database migrations, and monitoring dashboards.

## Learning Objectives

By the end of this lab, you will be able to:

1. Create a FastAPI application with database integration using SQLAlchemy
2. Integrate a machine learning model for sentiment analysis
3. Configure PostgreSQL database connections and implement migrations with Alembic
4. Containerize the application using Docker and Docker Compose
5. Deploy infrastructure to AWS using Pulumi (EKS, ECR, VPC)
6. Implement monitoring with Prometheus and Grafana
7. Set up automated CI/CD pipelines with GitHub Actions
8. Test API endpoints and verify database operations
9. Deploy applications to Kubernetes using kubectl and manifests

**Prerequisites:** Basic Python knowledge, familiarity with REST APIs, basic understanding of Docker concepts, and basic Kubernetes knowledge.

## Prologue: The Challenge

You join a development team at a growing startup. The team has built a FastAPI application that manages items in a database. Currently, the application runs only on developers' local machines. The product team cannot access it for testing. The operations team has no visibility into system health. Deployment requires manual steps that often fail.

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

```bash
# Install Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic-settings

# Install Docker and Docker Compose
# Follow official Docker installation guide for your OS

# Install Pulumi CLI
curl -fsSL https://get.pulumi.com | sh

# Install AWS CLI
pip install awscli

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

Create project structure:

```bash
mkdir -p app infra migrations monitoring k8s .github/workflows
```

## Chapter 1: Building the FastAPI Application

Every production application begins with a solid foundation. Before deploying to the cloud, you establish the core API with proper database integration, health checks, and data validation.

### 1.1 What You Will Build

A FastAPI application that connects to PostgreSQL, manages items with CRUD operations, and provides health endpoints for monitoring systems.

Key Concept: FastAPI uses Pydantic for automatic data validation and SQLAlchemy for database operations. This combination provides type safety and prevents invalid data from reaching your database.

### 1.2 Think First: Configuration Management

Before implementing, consider these questions:

**Question 1:** Why should database credentials be stored in environment variables rather than hardcoded in the application?

**Question 2:** What happens if the database connection fails during application startup?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Environment variables allow different configurations for development, staging, and production without code changes. They prevent credentials from being committed to version control, reducing security risks.

**Answer 2:** Without proper error handling, the application would crash. Production systems need graceful degradation—the process should start but health checks should report unhealthy status until the database connection is established.

</details>

### 1.3 Implementation: Configuration Setup

Create `app/config.py` to manage environment variables:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "___"  # Q1: What should the default PostgreSQL URL format be?
    
    postgres_user: str = "user"
    postgres_password: str = "pass"
    postgres_db: str = "appdb"
    postgres_host: str = "___"  # Q2: What host for local development?
    postgres_port: int = ___  # Q3: What is PostgreSQL's default port?
    
    class Config:
        env_file = ".env"
    
    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
```

**Hints:**
- PostgreSQL URL format: `postgresql://user:password@host:port/database`
- Local development typically uses `localhost`
- PostgreSQL default port is 5432

<details>
<summary>Click to see the complete solution</summary>

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:pass@localhost:5432/appdb"
    
    postgres_user: str = "user"
    postgres_password: str = "pass"
    postgres_db: str = "appdb"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    class Config:
        env_file = ".env"
    
    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

settings = Settings()
```

</details>

### 1.4 Implementation: Database Connection

Create `app/database.py` for database session management:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = settings.get_database_url()

engine = create_engine(___)  # Q1: What variable contains the database URL?
SessionLocal = sessionmaker(autocommit=___, autoflush=___, bind=engine)  # Q2: Should autocommit be True or False?
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.___()  # Q3: What method releases the database connection?
```

<details>
<summary>Click to see the complete solution</summary>

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

DATABASE_URL = settings.get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

</details>

### 1.5 Implementation: FastAPI Application

Create `app/main.py` with the complete API:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from pydantic import BaseModel
import os

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL') or "postgresql://user:pass@localhost:5432/appdb"

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
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

@app.get("/")
def read_root():
    return {"status": "online", "service": "FastAPI on AWS ECS", "version": "1.0.0"}

@app.get("/health")
def health_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate):
    db = SessionLocal()
    try:
        db_item = Item(name=item.name, description=item.description)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    finally:
        db.close()

@app.get("/items", response_model=list[ItemResponse])
def list_items():
    db = SessionLocal()
    try:
        items = db.query(Item).all()
        return items
    finally:
        db.close()

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    finally:
        db.close()
```

### 1.6 Understanding the Code

Match each component to its purpose:

| Component | Purpose (A-E) |
|-----------|---------------|
| `Base.metadata.create_all()` | ___ |
| `SessionLocal()` | ___ |
| `db.commit()` | ___ |
| `db.refresh()` | ___ |
| `HTTPException(status_code=404)` | ___ |

**Options:**
- A: Creates database tables from model definitions
- B: Creates a new database session
- C: Persists changes to the database
- D: Reloads the object with database-generated values
- E: Returns a 404 error response

<details>
<summary>Click to check your answers</summary>

- `Base.metadata.create_all()` → A: Creates database tables from model definitions
- `SessionLocal()` → B: Creates a new database session
- `db.commit()` → C: Persists changes to the database
- `db.refresh()` → D: Reloads the object with database-generated values
- `HTTPException(status_code=404)` → E: Returns a 404 error response

</details>

### 1.7 Create Environment Configuration

Create `.env` file:

```bash
DATABASE_URL=postgresql://postgres:postgres@100.84.171.106:5432/postgres
```

Create `app/requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic-settings==2.1.0
starlette-exporter==0.17.1
```

### 1.8 Test Locally

Install dependencies and run:

```bash
pip install -r app/requirements.txt
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 1.9 Checkpoint

Test the endpoints:

```bash
# Test root endpoint
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/health

# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "This is a test"}'

# List all items
curl http://localhost:8000/items

# Get specific item
curl http://localhost:8000/items/1
```

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

**Self-Assessment:**
- [ ] Application starts without errors
- [ ] Health endpoint returns database connection status
- [ ] Items can be created and retrieved
- [ ] Invalid item IDs return 404 errors
- [ ] You understand why database sessions must be closed in `finally` blocks

## Chapter 2: Machine Learning Model Integration

Production ML systems require more than just training models—they need reliable serving infrastructure. A model that works perfectly in a Jupyter notebook becomes valuable only when it can receive requests, make predictions, and return results at scale.

### 2.1 What You Will Build

A sentiment analysis model integrated into the FastAPI application with endpoints for predictions and model information.

Key Concept: ML models in production are loaded once at startup and kept in memory. This avoids the overhead of loading the model on every request, which would create unacceptable latency.

### 2.2 Think First: Model Serving Architecture

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

This allows the infrastructure to remain operational while the model issue is resolved.

</details>

### 2.3 Implementation: Create Training Script

Create `app/train_model.py` - see the complete code in the ML_MODEL_GUIDE.md file or the training script includes TF-IDF vectorization and Logistic Regression for sentiment classification.

### 2.4 Update Dependencies

Add ML libraries to `app/requirements.txt`:

```
scikit-learn==1.3.2
joblib==1.3.2
```

### 2.5 Train the Model

```bash
cd app
python train_model.py
```

### 2.6 Add ML Endpoints to FastAPI

The application now includes:
- `POST /predict` - Sentiment prediction
- `GET /model/info` - Model information
- Updated `/health` - Includes ML model status

### 2.7 Test ML Endpoints

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is absolutely amazing!"}'
```

### 2.8 Checkpoint

**Self-Assessment:**
- [ ] Model trains successfully
- [ ] `/predict` endpoint returns sentiment and confidence
- [ ] `/model/info` endpoint shows model details
- [ ] Docker image includes trained model
- [ ] You understand why models are loaded at startup

## Chapter 3: Database Migrations with Alembic

As applications evolve, database schemas change. Adding columns, creating indexes, or modifying constraints requires a systematic approach. Manual SQL scripts are error-prone and difficult to track across environments.

Alembic provides version-controlled database migrations. Each schema change becomes a tracked migration file that can be applied, rolled back, and audited.

### 2.1 What You Will Build

Database migration infrastructure using Alembic that tracks schema changes and applies them consistently across environments.

Key Concept: Migrations are version-controlled Python scripts that describe schema changes. Alembic maintains a version table in your database to track which migrations have been applied.

### 2.2 Think First: Why Migrations Matter

**Question 1:** Your application adds a new `price` column to the `items` table. Without migrations, how would you update production databases?

**Question 2:** What happens if two developers create conflicting schema changes?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Without migrations, you would need to manually run SQL commands on each environment. This is error-prone, difficult to track, and can cause inconsistencies between environments.

**Answer 2:** Migration tools detect conflicts through version tracking. Developers must resolve conflicts by creating a merge migration or reordering changes, ensuring schema consistency.

</details>

### 2.3 Implementation: Initialize Alembic

Install Alembic:

```bash
pip install alembic
```

Initialize Alembic in your project:

```bash
alembic init migrations
```

This creates:
- `alembic.ini` - Configuration file
- `migrations/` - Directory for migration scripts
- `migrations/env.py` - Migration environment configuration

### 2.4 Implementation: Configure Alembic

Edit `alembic.ini` to use environment variables for the database URL:

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

# Remove or comment out the sqlalchemy.url line
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

Edit `migrations/env.py` to import your models and use the database URL from environment:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add your app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models
from app.main import Base

# this is the Alembic Config object
config = context.config

# Set the database URL from environment
config.set_main_option(
    'sqlalchemy.url',
    os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/appdb')
)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 2.5 Create Initial Migration

Generate the initial migration based on your models:

```bash
alembic revision --autogenerate -m "Initial migration with items table"
```

This creates a migration file in `migrations/versions/` with the schema definition.

### 2.6 Understanding Migration Files

Open the generated migration file. It contains two functions:

```python
def upgrade() -> None:
    # Commands to apply the migration
    op.create_table('items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_index(op.f('ix_items_name'), 'items', ['name'], unique=False)

def downgrade() -> None:
    # Commands to revert the migration
    op.drop_index(op.f('ix_items_name'), table_name='items')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_table('items')
```

**Question:** Why does each migration have both `upgrade()` and `downgrade()` functions?

<details>
<summary>Click for the answer</summary>

The `upgrade()` function applies the migration, while `downgrade()` reverts it. This allows rolling back problematic migrations in production without data loss. It provides a safety mechanism for schema changes.

</details>

### 2.7 Apply Migrations

Apply all pending migrations:

```bash
alembic upgrade head
```

Check migration status:

```bash
alembic current
```

View migration history:

```bash
alembic history
```

### 2.8 Experiment: Add a New Column

Modify `app/main.py` to add a `price` column to the Item model:

```python
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer, default=0)  # New column
    created_at = Column(DateTime, default=datetime.utcnow)
```

Generate a new migration:

```bash
alembic revision --autogenerate -m "Add price column to items"
```

Review the generated migration file, then apply it:

```bash
alembic upgrade head
```

Verify the column was added by querying the database or checking the table schema.

### 2.9 Checkpoint

**Self-Assessment:**
- [ ] Alembic is initialized and configured
- [ ] Initial migration creates the items table
- [ ] You can generate new migrations with `--autogenerate`
- [ ] You can apply migrations with `upgrade head`
- [ ] You understand the difference between `upgrade()` and `downgrade()`
- [ ] You can explain why migrations are better than manual SQL scripts

## Chapter 4: Containerization with Docker

Containers solve the "works on my machine" problem. By packaging the application with its dependencies, containers ensure consistent behavior across development, testing, and production environments.

### 3.1 What You Will Build

Docker containers for the FastAPI application and a Docker Compose configuration that orchestrates the application with monitoring services.

Key Concept: Docker images are immutable snapshots of your application and its dependencies. Containers are running instances of images. Docker Compose manages multi-container applications.

### 3.2 Think First: Container Benefits

**Question 1:** Why containerize an application instead of deploying directly to a server?

**Question 2:** What is the difference between a Docker image and a Docker container?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Containers provide:
- Consistency across environments (eliminates configuration drift)
- Isolation from host system dependencies
- Easy scaling (spin up multiple containers)
- Simplified deployment (single artifact to deploy)
- Version control for the entire runtime environment

**Answer 2:** An image is a read-only template containing the application and dependencies. A container is a running instance of an image with its own filesystem, network, and process space.

</details>

### 3.3 Implementation: Create Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Expose port
EXPOSE ___  # Q1: What port does the FastAPI app use?

# Run the application
CMD ["uvicorn", "main:app", "--host", "___", "--port", "8000"]  # Q2: What host allows external connections?
```

**Hints:**
- FastAPI runs on port 8000 by default
- Use `0.0.0.0` to bind to all network interfaces in containers

<details>
<summary>Click to see the complete solution</summary>

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

</details>

### 3.4 Understanding Dockerfile Instructions

Match each instruction to its purpose:

| Instruction | Purpose (A-E) |
|-------------|---------------|
| `FROM` | ___ |
| `WORKDIR` | ___ |
| `COPY` | ___ |
| `RUN` | ___ |
| `CMD` | ___ |

**Options:**
- A: Sets the working directory inside the container
- B: Specifies the base image
- C: Executes commands during image build
- D: Copies files from host to container
- E: Defines the default command when container starts

<details>
<summary>Click to check your answers</summary>

- `FROM` → B: Specifies the base image
- `WORKDIR` → A: Sets the working directory inside the container
- `COPY` → D: Copies files from host to container
- `RUN` → C: Executes commands during image build
- `CMD` → E: Defines the default command when container starts

</details>

### 3.5 Build and Test the Docker Image

Build the image:

```bash
docker build -t fastapi-app .
```

Run the container:

```bash
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@100.84.171.106:5432/postgres \
  --name fastapi-container \
  fastapi-app
```

Test the containerized application:

```bash
curl http://localhost:8000/health
```

View container logs:

```bash
docker logs fastapi-container
```

Stop and remove the container:

```bash
docker stop fastapi-container
docker rm fastapi-container
```

### 3.6 Implementation: Docker Compose Configuration

Create `docker-compose.yml` for multi-service orchestration:

```yaml
services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@100.84.171.106:5432/postgres
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-datasource.yml:/etc/grafana/provisioning/datasources/datasource.yml
    networks:
      - app-network
    depends_on:
      - prometheus

networks:
  app-network:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

### 3.7 Understanding Docker Compose

**Question:** What is the purpose of the `depends_on` directive in the Grafana service?

<details>
<summary>Click for the answer</summary>

The `depends_on` directive ensures Prometheus starts before Grafana. This is important because Grafana needs Prometheus as a data source. However, `depends_on` only waits for the container to start, not for the service to be ready. For production, use health checks.

</details>

### 3.8 Start the Complete Stack

Start all services:

```bash
docker-compose up -d
```

Verify all containers are running:

```bash
docker-compose ps
```

Test the services:

```bash
# FastAPI
curl http://localhost:8000/health

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana (in browser)
# http://localhost:3001 (admin/admin)
```

View logs:

```bash
docker-compose logs -f fastapi
```

Stop all services:

```bash
docker-compose down
```

### 3.9 Checkpoint

**Self-Assessment:**
- [ ] Dockerfile builds successfully
- [ ] Container runs and responds to health checks
- [ ] Docker Compose starts all services
- [ ] You can access FastAPI, Prometheus, and Grafana
- [ ] You understand the difference between `docker run` and `docker-compose up`
- [ ] You can explain why health checks are important in containers

## Chapter 5: Monitoring with Prometheus and Grafana

Production systems require observability. When issues occur, you need metrics to diagnose problems. Prometheus collects time-series metrics, and Grafana visualizes them in dashboards.

### 4.1 What You Will Build

Monitoring infrastructure that collects application metrics and displays them in visual dashboards.

Key Concept: Prometheus scrapes metrics from endpoints at regular intervals. Grafana queries Prometheus and renders the data in customizable dashboards.

### 4.2 Think First: Monitoring Strategy

**Question 1:** What metrics would help diagnose a slow API response?

**Question 2:** Why collect metrics instead of just checking logs?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Useful metrics include:
- Request duration (latency)
- Request rate (throughput)
- Error rate
- Database query time
- Active connections

**Answer 2:** Metrics provide:
- Aggregated data over time (trends)
- Real-time alerting capabilities
- Lower storage requirements than logs
- Faster queries for time-series data
- Visual representation of system behavior

Logs provide detailed event information, while metrics provide quantitative measurements. Both are necessary for complete observability.

</details>

### 4.3 Implementation: Add Prometheus Metrics to FastAPI

Update `app/requirements.txt` to include the Prometheus exporter:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic-settings==2.1.0
starlette-exporter==0.17.1
```

The application in `app/main.py` already includes Prometheus middleware:

```python
from starlette_exporter import PrometheusMiddleware, handle_metrics

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)
```

This automatically exposes metrics at `/metrics` endpoint.

### 4.4 Understanding Prometheus Metrics

Test the metrics endpoint:

```bash
curl http://localhost:8000/metrics
```

You will see metrics like:

```
# HELP starlette_requests_total Total requests
# TYPE starlette_requests_total counter
starlette_requests_total{method="GET",path="/health"} 42.0

# HELP starlette_request_duration_seconds Request duration
# TYPE starlette_request_duration_seconds histogram
starlette_request_duration_seconds_bucket{le="0.005",method="GET",path="/items"} 15.0
```

**Question:** What is the difference between a counter and a histogram metric?

<details>
<summary>Click for the answer</summary>

- **Counter:** A value that only increases (e.g., total requests, total errors). Used for rates and totals.
- **Histogram:** Samples observations and counts them in configurable buckets (e.g., request duration). Used for percentiles and distributions.

</details>

### 4.5 Implementation: Configure Prometheus

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['fastapi:8000']
    metrics_path: '/metrics'
```

This configuration tells Prometheus to:
- Scrape metrics every 15 seconds
- Target the FastAPI service at `fastapi:8000`
- Collect metrics from the `/metrics` endpoint

### 4.6 Implementation: Configure Grafana Data Source

Create `monitoring/grafana-datasource.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

### 4.7 Start Monitoring Stack

Start all services with Docker Compose:

```bash
docker-compose up -d
```

Generate some traffic to create metrics:

```bash
# Create multiple requests
for i in {1..20}; do
  curl http://localhost:8000/health
  curl http://localhost:8000/items
done
```

### 4.8 Explore Prometheus

Access Prometheus at `http://localhost:9090`

Try these queries in the Prometheus UI:

```promql
# Request rate per second
rate(starlette_requests_total[1m])

# 95th percentile response time
histogram_quantile(0.95, rate(starlette_request_duration_seconds_bucket[5m]))

# Error rate
rate(starlette_requests_total{status_code=~"5.."}[1m])
```

### 4.9 Create Grafana Dashboard

Access Grafana at `http://localhost:3001` (username: `admin`, password: `admin`)

Create a new dashboard:

1. Click "+" → "Dashboard"
2. Click "Add visualization"
3. Select "Prometheus" data source
4. Add a query: `rate(starlette_requests_total[1m])`
5. Set title: "Request Rate"
6. Click "Apply"

Add more panels for:
- Response time (95th percentile)
- Error rate
- Active requests

### 4.10 Understanding Grafana Queries

**Question:** What does `rate(starlette_requests_total[1m])` calculate?

<details>
<summary>Click for the answer</summary>

The `rate()` function calculates the per-second average rate of increase over the specified time window. `rate(starlette_requests_total[1m])` shows how many requests per second occurred over the last minute.

This is useful for counters because it converts cumulative totals into rates, making trends visible.

</details>

### 4.11 Checkpoint

**Self-Assessment:**
- [ ] FastAPI exposes metrics at `/metrics`
- [ ] Prometheus scrapes metrics from FastAPI
- [ ] Grafana connects to Prometheus as a data source
- [ ] You can query metrics in Prometheus UI
- [ ] You can create visualizations in Grafana
- [ ] You understand the difference between counters and histograms
- [ ] You can explain why monitoring is essential for production systems

## Chapter 6: Infrastructure as Code with Pulumi

Manual infrastructure provisioning is error-prone and difficult to reproduce. Infrastructure as Code (IaC) treats infrastructure configuration as software, enabling version control, testing, and automation.

### 6.1 What You Will Build

AWS infrastructure using Pulumi that provisions EKS clusters, VPCs, and container registries.

Key Concept: Pulumi uses familiar programming languages (Python, TypeScript, Go) to define infrastructure. It manages state and handles dependencies automatically.

### 6.2 Think First: Infrastructure Components

**Question 1:** Why use Kubernetes instead of running containers directly on EC2 instances?

**Question 2:** What is the purpose of a VPC in AWS?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Kubernetes provides:
- Automatic container orchestration and scheduling
- Self-healing (restarts failed containers)
- Horizontal scaling based on load
- Service discovery and load balancing
- Rolling updates and rollbacks
- Declarative configuration

**Answer 2:** A VPC (Virtual Private Cloud) provides:
- Network isolation for your resources
- Control over IP address ranges
- Public and private subnets
- Security group rules for traffic control
- Network-level security boundaries

</details>

### 6.3 Implementation: Pulumi Configuration

Create `infra/Pulumi.yaml`:

```yaml
name: fastapi-app
runtime: python
description: FastAPI application infrastructure on AWS EKS
```

Create `infra/requirements.txt`:

```
pulumi>=3.0.0
pulumi-aws>=6.0.0
pulumi-eks>=2.0.0
pulumi-kubernetes>=4.0.0
```

Install Pulumi dependencies:

```bash
cd infra
pip install -r requirements.txt
```

### 6.4 Implementation: Define Infrastructure

Create `infra/__main__.py`:

```python
import pulumi
import pulumi_aws as aws
import pulumi_eks as eks

config = pulumi.Config()
app_name = "fastapi-app"

# 1. VPC for EKS
vpc = aws.ec2.Vpc(
    f"{app_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    f"{app_name}-igw",
    vpc_id=vpc.id,
)

# Public Subnets
public_subnet_1 = aws.ec2.Subnet(
    f"{app_name}-public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
)

public_subnet_2 = aws.ec2.Subnet(
    f"{app_name}-public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="ap-southeast-1b",
    map_public_ip_on_launch=True,
)

# Route Table
route_table = aws.ec2.RouteTable(
    f"{app_name}-rt",
    vpc_id=vpc.id,
)

# Route to Internet Gateway
route = aws.ec2.Route(
    f"{app_name}-route",
    route_table_id=route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id,
)

# Associate Route Table with Subnets
rta1 = aws.ec2.RouteTableAssociation(
    f"{app_name}-rta-1",
    subnet_id=public_subnet_1.id,
    route_table_id=route_table.id,
)

rta2 = aws.ec2.RouteTableAssociation(
    f"{app_name}-rta-2",
    subnet_id=public_subnet_2.id,
    route_table_id=route_table.id,
)

# 2. EKS Cluster
cluster = eks.Cluster(
    f"{app_name}-cluster",
    vpc_id=vpc.id,
    subnet_ids=[public_subnet_1.id, public_subnet_2.id],
    instance_type="t3.medium",
    desired_capacity=___,  # Q1: How many nodes for high availability?
    min_size=1,
    max_size=3,
    enabled_cluster_log_types=["api", "audit", "authenticator"],
)

# 3. ECR Repository
repo = aws.ecr.Repository(
    f"{app_name}-repo",
    force_delete=True,
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

# ECR Lifecycle Policy
aws.ecr.LifecyclePolicy(
    f"{app_name}-lifecycle",
    repository=repo.name,
    policy="""{
        "rules": [{
            "rulePriority": 1,
            "description": "Keep last 10 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 10
            },
            "action": {
                "type": "expire"
            }
        }]
    }""",
)

# Exports
pulumi.export("kubeconfig", cluster.kubeconfig)
pulumi.export("cluster_name", cluster.eks_cluster.name)
pulumi.export("ecr_repository_url", repo.repository_url)
```

**Hints:**
- Use 2 nodes for high availability
- EKS manages the Kubernetes control plane
- Worker nodes run in your VPC

<details>
<summary>Click to see key values</summary>

- `desired_capacity=2`

</details>

### 6.5 Understanding Pulumi and EKS Concepts

Match each concept to its description:

| Concept | Description (A-E) |
|---------|-------------------|
| `pulumi.Config()` | ___ |
| `pulumi.export()` | ___ |
| `pulumi.Output` | ___ |
| EKS Cluster | ___ |
| Worker Nodes | ___ |

**Options:**
- A: Retrieves configuration values for the current stack
- B: Makes values available after deployment
- C: Represents a value that will be known after resources are created
- D: Managed Kubernetes control plane
- E: EC2 instances that run containerized applications

<details>
<summary>Click to check your answers</summary>

- `pulumi.Config()` → A: Retrieves configuration values for the current stack
- `pulumi.export()` → B: Makes values available after deployment
- `pulumi.Output` → C: Represents a value that will be known after resources are created
- EKS Cluster → D: Managed Kubernetes control plane
- Worker Nodes → E: EC2 instances that run containerized applications

</details>

### 6.6 Initialize Pulumi Stack

Login to Pulumi (create account at pulumi.com if needed):

```bash
pulumi login
```

Initialize a new stack:

```bash
cd infra
pulumi stack init dev
```

Set AWS region:

```bash
pulumi config set aws:region ap-southeast-1
```

### 6.7 Preview Infrastructure Changes

Preview what Pulumi will create:

```bash
pulumi preview
```

This shows all resources that will be created without actually creating them.

### 6.8 Deploy Infrastructure

Deploy the infrastructure:

```bash
pulumi up
```

Review the changes and confirm. Pulumi will create:
- VPC with public subnets
- Internet Gateway and Route Tables
- EKS cluster (control plane)
- EKS worker nodes (EC2 instances)
- ECR repository
- IAM roles and policies

This process takes 10-15 minutes as EKS cluster creation is time-intensive.

### 6.9 Configure kubectl

After deployment, configure kubectl to access your EKS cluster:

```bash
pulumi stack output kubeconfig > kubeconfig.yaml
export KUBECONFIG=$PWD/kubeconfig.yaml
```

Verify cluster access:

```bash
kubectl get nodes
```

Get the ECR repository URL:

```bash
pulumi stack output ecr_repository_url
```

### 5.10 Checkpoint

**Self-Assessment:**
- [ ] Pulumi is installed and configured
- [ ] Infrastructure code defines all required AWS resources
- [ ] `pulumi preview` shows planned changes
- [ ] `pulumi up` successfully deploys EKS cluster
- [ ] kubectl can connect to the cluster
- [ ] You can see worker nodes with `kubectl get nodes`
- [ ] You understand why IaC is better than manual provisioning
- [ ] You can explain the purpose of each infrastructure component

## Chapter 7: Kubernetes Deployment

With the EKS cluster running, you need to deploy the FastAPI application to Kubernetes. Kubernetes uses declarative YAML manifests to define desired state.

### 6.1 What You Will Build

Kubernetes manifests that define deployments, services, and ingress for the FastAPI application.

Key Concept: Kubernetes operates on desired state. You declare what you want (3 replicas of the app), and Kubernetes ensures that state is maintained.

### 7.2 Think First: Kubernetes Resources

**Question 1:** What is the difference between a Deployment and a Pod in Kubernetes?

**Question 2:** Why use a Service instead of accessing Pods directly?

<details>
<summary>Click to review answers</summary>

**Answer 1:** 
- **Pod:** The smallest deployable unit, contains one or more containers
- **Deployment:** Manages a set of identical Pods, handles scaling, updates, and self-healing

Deployments provide the management layer that Pods lack.

**Answer 2:** Services provide:
- Stable IP address and DNS name
- Load balancing across Pods
- Service discovery
- Abstraction from Pod lifecycle (Pods are ephemeral)

Pods can be created and destroyed, but Services remain stable.

</details>

### 7.3 Implementation: Kubernetes Deployment Manifest

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-deployment
  labels:
    app: fastapi
spec:
  replicas: ___  # Q1: How many replicas for high availability?
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: <ECR_REPOSITORY_URL>:latest  # Replace with your ECR URL
        ports:
        - containerPort: ___  # Q2: What port does FastAPI use?
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:postgres@100.84.171.106:5432/postgres"
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
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Hints:**
- Use 2-3 replicas for high availability
- FastAPI runs on port 8000

<details>
<summary>Click to see key values</summary>

- `replicas: 2`
- `containerPort: 8000`

</details>

### 7.4 Implementation: Kubernetes Service Manifest

Create `k8s/service.yaml`:

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

This creates an AWS Load Balancer that routes traffic to your FastAPI Pods.

### 7.5 Understanding Kubernetes Probes

**Question:** What is the difference between `livenessProbe` and `readinessProbe`?

<details>
<summary>Click for the answer</summary>

- **livenessProbe:** Checks if the container is running. If it fails, Kubernetes restarts the container.
- **readinessProbe:** Checks if the container is ready to serve traffic. If it fails, Kubernetes removes the Pod from the Service endpoints.

Use liveness for detecting crashed applications and readiness for detecting temporarily unavailable applications (e.g., during startup).

</details>

### 7.6 Deploy to Kubernetes

First, update the deployment manifest with your ECR repository URL:

```bash
ECR_URL=$(pulumi stack output ecr_repository_url)
sed -i "s|<ECR_REPOSITORY_URL>|$ECR_URL|g" k8s/deployment.yaml
```

Apply the manifests:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 7.7 Verify Deployment

Check deployment status:

```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

View Pod logs:

```bash
kubectl logs -l app=fastapi
```

Describe a Pod for detailed information:

```bash
kubectl describe pod <pod-name>
```

### 7.8 Access the Application

Get the Load Balancer URL:

```bash
kubectl get service fastapi-service
```

The `EXTERNAL-IP` column shows the Load Balancer DNS name. It may take a few minutes to provision.

Test the application:

```bash
LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/health
curl http://$LB_URL/items
```

### 7.9 Scaling the Application

Scale to 5 replicas:

```bash
kubectl scale deployment fastapi-deployment --replicas=5
```

Verify scaling:

```bash
kubectl get pods -w
```

Scale back to 2:

```bash
kubectl scale deployment fastapi-deployment --replicas=2
```

### 7.10 Update the Application

When you push a new image to ECR, update the deployment:

```bash
kubectl rollout restart deployment fastapi-deployment
```

Or update the image explicitly:

```bash
kubectl set image deployment/fastapi-deployment fastapi=<ECR_URL>:new-tag
```

Check rollout status:

```bash
kubectl rollout status deployment fastapi-deployment
```

### 6.11 Checkpoint

**Self-Assessment:**
- [ ] Deployment manifest defines the application
- [ ] Service manifest exposes the application
- [ ] Pods are running successfully
- [ ] Load Balancer is provisioned
- [ ] Application is accessible via Load Balancer URL
- [ ] You can scale the deployment
- [ ] You understand the difference between Deployments, Pods, and Services
- [ ] You can explain how probes enable self-healing

## Chapter 8: CI/CD with GitHub Actions

Manual deployments are slow and error-prone. Continuous Integration and Continuous Deployment (CI/CD) automate testing and deployment, ensuring code quality and rapid delivery.

### 6.1 What You Will Build

Automated pipelines that test code on every commit and deploy to AWS on successful merges to the main branch.

Key Concept: CI/CD pipelines run automatically in response to repository events. They execute tests, build containers, and deploy infrastructure without manual intervention.

### 8.2 Think First: Pipeline Design

**Question 1:** Why run tests before deployment?

**Question 2:** What should happen if tests fail on the main branch?

<details>
<summary>Click to review answers</summary>

**Answer 1:** Running tests before deployment:
- Catches bugs before they reach production
- Validates that new code does not break existing functionality
- Ensures code meets quality standards
- Provides confidence in automated deployments

**Answer 2:** If tests fail on main:
- Deployment should be blocked
- Team should be notified immediately
- The failing commit should be reverted or fixed quickly
- No further deployments should occur until tests pass

</details>

### 8.3 Implementation: CI Pipeline

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
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r app/requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd app
        pytest test_main.py -v --cov=main
    
    - name: Lint code
      run: |
        pip install flake8
        flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
```

### 8.4 Understanding GitHub Actions Syntax

Match each component to its purpose:

| Component | Purpose (A-E) |
|-----------|---------------|
| `on:` | ___ |
| `jobs:` | ___ |
| `steps:` | ___ |
| `uses:` | ___ |
| `run:` | ___ |

**Options:**
- A: Defines when the workflow triggers
- B: Groups related tasks
- C: Individual commands or actions
- D: References a reusable action
- E: Executes shell commands

<details>
<summary>Click to check your answers</summary>

- `on:` → A: Defines when the workflow triggers
- `jobs:` → B: Groups related tasks
- `steps:` → C: Individual commands or actions
- `uses:` → D: References a reusable action
- `run:` → E: Executes shell commands

</details>

### 8.5 Implementation: Deployment Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS EKS

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
    
    - name: Configure kubectl
      run: |
        cd infra
        pulumi stack output kubeconfig > kubeconfig.yaml
        echo "KUBECONFIG=$PWD/kubeconfig.yaml" >> $GITHUB_ENV
    
    - name: Run database migrations
      run: |
        pip install alembic psycopg2-binary
        alembic upgrade head
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
    
    - name: Update Kubernetes deployment
      run: |
        ECR_URL=$(cd infra && pulumi stack output ecr_repository_url)
        sed -i "s|<ECR_REPOSITORY_URL>|$ECR_URL|g" k8s/deployment.yaml
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        kubectl rollout restart deployment fastapi-deployment
    
    - name: Get application URL
      run: |
        echo "🚀 Deployment Complete!"
        kubectl get service fastapi-service
    
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
        pip install alembic psycopg2-binary
        alembic upgrade head
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
    
    - name: Force ECS service update
      run: |
        aws ecs update-service \
          --cluster fastapi-app-cluster \
          --service fastapi-app-service \
          --force-new-deployment \
          --region ${{ env.AWS_REGION }}
```

### 8.6 Understanding Pipeline Flow

The deployment pipeline follows this sequence:

1. **Trigger:** Runs after CI pipeline succeeds on main branch
2. **Authenticate:** Configure AWS credentials from secrets
3. **Build:** Create Docker image with application code
4. **Push:** Upload image to ECR with commit SHA tag
5. **Deploy Infrastructure:** Run Pulumi to update EKS cluster
6. **Configure kubectl:** Set up Kubernetes access
7. **Migrate Database:** Apply pending Alembic migrations
8. **Update Kubernetes:** Apply manifests and restart deployment

**Question:** Why tag images with the commit SHA in addition to `latest`?

<details>
<summary>Click for the answer</summary>

Tagging with commit SHA provides:
- Traceability (know exactly which code is deployed)
- Rollback capability (deploy previous SHA if needed)
- Immutable references (SHA tags never change)

The `latest` tag provides convenience for development but should not be relied upon in production.

</details>

### 8.7 Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `PULUMI_ACCESS_TOKEN`: Your Pulumi access token
- `DATABASE_URL`: Your PostgreSQL connection string

### 8.8 Create Basic Tests

Create `app/test_main.py`:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_create_item():
    response = client.post(
        "/items",
        json={"name": "Test Item", "description": "Test Description"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"

def test_list_items():
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_nonexistent_item():
    response = client.get("/items/99999")
    assert response.status_code == 404
```

### 8.9 Test the Pipeline

Commit and push your changes:

```bash
git add .
git commit -m "Add CI/CD pipelines"
git push origin main
```

Monitor the workflow:

1. Go to your GitHub repository
2. Click "Actions" tab
3. Watch the CI pipeline run
4. After CI succeeds, watch the deployment pipeline

### 8.10 Verify Deployment

After the pipeline completes, test the deployed application:

```bash
# Get the Load Balancer URL
kubectl get service fastapi-service

# Test the deployed API
LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/health
curl http://$LB_URL/items
```

### 8.11 Checkpoint

**Self-Assessment:**
- [ ] CI pipeline runs on every push
- [ ] Tests execute automatically
- [ ] Deployment pipeline triggers after successful CI
- [ ] Docker image builds and pushes to ECR
- [ ] Pulumi deploys EKS infrastructure
- [ ] kubectl is configured automatically
- [ ] Database migrations run automatically
- [ ] Kubernetes deployment updates with new image
- [ ] You understand the complete deployment flow
- [ ] You can explain why CI/CD improves reliability

## Epilogue: The Complete System

You have built a production-ready FastAPI application with complete infrastructure and automation. The system now provides:

| Component | Purpose |
|-----------|---------|
| FastAPI Application | REST API with database integration |
| PostgreSQL Database | Persistent data storage |
| Alembic Migrations | Version-controlled schema changes |
| Docker Containers | Consistent runtime environment |
| Prometheus | Metrics collection |
| Grafana | Metrics visualization |
| AWS EKS | Kubernetes cluster management |
| AWS ECR | Container registry |
| Kubernetes Service | Load balancing and service discovery |
| Pulumi | Infrastructure as code |
| GitHub Actions | Automated CI/CD |

### End-to-End Verification

Verify the complete system:

```bash
# Get the Load Balancer URL
kubectl get service fastapi-service
export LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test all endpoints
curl http://$LB_URL/
curl http://$LB_URL/health
curl http://$LB_URL/metrics

# Create an item
curl -X POST http://$LB_URL/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Item", "description": "Created in production"}'

# List items
curl http://$LB_URL/items

# Get specific item
curl http://$LB_URL/items/1

# Check Prometheus metrics
curl http://$LB_URL/metrics | grep starlette_requests_total
```

All commands should succeed without errors.

### Architecture Overview

The deployed system follows this architecture:

```
GitHub Repository
    ↓ (push to main)
GitHub Actions CI
    ↓ (tests pass)
GitHub Actions Deploy
    ↓
Docker Image → ECR
    ↓
Pulumi → AWS Infrastructure (EKS)
    ↓
EKS Cluster
    ↓
Kubernetes Service (LoadBalancer) → Pods (FastAPI)
    ↓
External PostgreSQL Database
    ↓
Prometheus ← Metrics
    ↓
Grafana ← Visualization
```

## The Principles

Building production-ready applications follows these principles:

1. **Configuration as environment variables** — Never hardcode credentials or environment-specific values
2. **Database migrations as code** — Track schema changes with version control
3. **Containers for consistency** — Package applications with their dependencies
4. **Infrastructure as code** — Define infrastructure in version-controlled files
5. **Automated testing** — Run tests on every commit to catch issues early
6. **Automated deployment** — Deploy automatically after tests pass
7. **Health checks at every layer** — Application, container, and load balancer health checks
8. **Observability from the start** — Collect metrics and logs from day one
9. **Immutable deployments** — Deploy new containers rather than modifying running ones
10. **Rollback capability** — Tag images and maintain deployment history

## Troubleshooting

### Database Connection Errors

**Error:** `could not connect to server: Connection refused`

**Cause:** Database is unreachable or credentials are incorrect.

**Solution:**
```bash
# Verify database URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check security groups allow traffic from ECS tasks
```

### Docker Build Failures

**Error:** `failed to solve with frontend dockerfile.v0`

**Cause:** Dockerfile syntax error or missing files.

**Solution:**
```bash
# Verify Dockerfile syntax
docker build -t test .

# Check that app/requirements.txt exists
ls -la app/requirements.txt
```

### EKS Task Failures

**Error:** Pods are in CrashLoopBackOff state

**Cause:** Application crashes or health check fails.

**Solution:**
```bash
# View pod logs
kubectl logs -l app=fastapi

# Describe pod for events
kubectl describe pod <pod-name>

# Check pod status
kubectl get pods -o wide
```

### Kubernetes Service Issues

**Error:** Service has no EXTERNAL-IP

**Cause:** Load Balancer is still provisioning or there's an AWS issue.

**Solution:**
```bash
# Check service events
kubectl describe service fastapi-service

# Verify service type is LoadBalancer
kubectl get service fastapi-service -o yaml

# Wait a few minutes for AWS to provision the Load Balancer
```

### Pulumi Deployment Errors

**Error:** `error: resource already exists`

**Cause:** Resource exists outside Pulumi management.

**Solution:**
```bash
# Import existing resource
pulumi import aws:ec2/vpc:Vpc my-vpc vpc-12345

# Or delete and recreate
pulumi destroy
pulumi up
```

### Migration Failures

**Error:** `alembic.util.exc.CommandError: Can't locate revision identified by`

**Cause:** Migration history mismatch between code and database.

**Solution:**
```bash
# Check current database version
alembic current

# View migration history
alembic history

# Stamp database to specific version
alembic stamp head
```

### GitHub Actions Failures

**Error:** `Error: Process completed with exit code 1`

**Cause:** Tests failed or deployment step encountered an error.

**Solution:**
1. Check the Actions tab for detailed logs
2. Run the failing command locally
3. Verify all secrets are configured
4. Check AWS permissions

## Next Steps

To extend this system, consider:

1. **Add authentication** — Implement JWT tokens or OAuth2 for API security
2. **Implement caching** — Add Redis for frequently accessed data
3. **Set up alerting** — Configure Prometheus Alertmanager for critical issues
4. **Add more tests** — Increase test coverage with integration and load tests
5. **Implement blue-green deployment** — Zero-downtime deployments with traffic shifting
6. **Add API versioning** — Support multiple API versions simultaneously
7. **Implement rate limiting** — Protect against abuse with request throttling
8. **Set up log aggregation** — Centralize logs with CloudWatch or ELK stack
9. **Add database backups** — Automated backups with point-in-time recovery
10. **Implement secrets management** — Use AWS Secrets Manager or Parameter Store

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Lab Questions

Test your understanding of the lab concepts:

### FastAPI and Application Development

**Question 1:** Why does the FastAPI application use Pydantic models for request validation?

<details>
<summary>Click to review</summary>

Pydantic models provide:
- Automatic type validation
- Clear error messages for invalid data
- API documentation generation
- IDE autocomplete support
- Prevention of invalid data reaching business logic

</details>

**Question 2:** What is the purpose of the `SessionLocal()` context manager pattern in database operations?

<details>
<summary>Click to review</summary>

The pattern ensures:
- Database connections are properly closed after use
- Resources are released even if exceptions occur
- Connection pool is not exhausted
- Transactions are properly managed

The `finally` block guarantees cleanup regardless of success or failure.

</details>

**Question 3:** Why does the health check endpoint test the database connection?

<details>
<summary>Click to review</summary>

Testing the database connection in health checks:
- Verifies the application can fulfill its purpose
- Allows load balancers to route traffic only to functional instances
- Detects database connectivity issues before they affect users
- Provides early warning of infrastructure problems

A running process without database access cannot serve requests successfully.

</details>

### Database and Migrations

**Question 4:** What problem do database migrations solve that manual SQL scripts do not?

<details>
<summary>Click to review</summary>

Migrations provide:
- Version control for schema changes
- Automatic tracking of applied changes
- Rollback capability
- Consistency across environments
- Audit trail of schema evolution
- Conflict detection between developers

Manual scripts lack tracking and can be applied incorrectly or multiple times.

</details>

**Question 5:** When should you create a new migration versus modifying an existing one?

<details>
<summary>Click to review</summary>

Create a new migration when:
- The previous migration has been applied to any environment
- The previous migration has been committed to version control
- Other developers may have applied the migration

Modify an existing migration only when:
- It has not been applied anywhere
- It has not been shared with other developers
- You are still in active development

Once applied, migrations should be treated as immutable.

</details>

### Docker and Containerization

**Question 6:** Why does the Dockerfile copy `requirements.txt` before copying the application code?

<details>
<summary>Click to review</summary>

This pattern leverages Docker's layer caching:
- Dependencies change less frequently than code
- Docker caches the pip install layer
- Subsequent builds skip dependency installation if requirements.txt unchanged
- Significantly faster build times during development

Copying code first would invalidate the cache on every code change.

</details>

**Question 7:** What is the difference between `EXPOSE` and port mapping in Docker?

<details>
<summary>Click to review</summary>

- `EXPOSE`: Documents which port the container listens on (metadata only)
- Port mapping (`-p 8000:8000`): Actually publishes the port to the host

`EXPOSE` does not make the port accessible. It serves as documentation and is used by Docker Compose for automatic port mapping.

</details>

### Testing and Validation

**Question 8:** Why test the API with a `TestClient` instead of running the actual server?

<details>
<summary>Click to review</summary>

`TestClient` provides:
- Faster test execution (no network overhead)
- No port conflicts
- Easier test isolation
- Synchronous testing of async code
- No cleanup of running processes

Tests run in-process, making them faster and more reliable.

</details>

**Question 9:** What should happen when a test fails in the CI pipeline?

<details>
<summary>Click to review</summary>

When tests fail:
- The pipeline should stop immediately
- Deployment should be blocked
- Developers should be notified
- The commit should not be merged
- No changes should reach production

Automated testing only provides value if failures prevent deployment.

</details>

## Final Self-Assessment

Before completing this lab, verify you can answer these questions:

- [ ] Why use environment variables for configuration?
- [ ] How do database migrations improve schema management?
- [ ] What benefits do containers provide over traditional deployment?
- [ ] Why is infrastructure as code better than manual provisioning?
- [ ] How does CI/CD improve deployment reliability?
- [ ] What is the purpose of health checks at different layers?
- [ ] Why collect metrics in addition to logs?
- [ ] How do load balancers enable zero-downtime deployments?

If you can explain these concepts, you have successfully completed the lab.
