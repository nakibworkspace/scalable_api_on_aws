Introduction to FastAPI for Model Deployment

Introduction

This lab teaches you to build APIs with FastAPI for serving machine learning models. FastAPI is a high-performance Python web framework designed for production-ready APIs with automatic documentation, type validation, and asynchronous support.

Approach: Rather than building disconnected scripts, you will create one cohesive FastAPI application that progressively adds features. By the end, you will have a complete ML Model Management API capable of registering models, retrieving metadata, and serving predictions from a single running server.



Learning Objectives

By the end of this lab, you will be able to:

Create a FastAPI application with health and readiness checks
Implement GET endpoints to retrieve model metadata
Implement POST endpoints to register models with validation
Load and serve predictions from a pre-trained ML model using startup hooks
Use Pydantic models for automatic request/response validation
Handle errors appropriately with HTTP status codes
Test API endpoints using cURL
(Optional) Log model metadata to MLflow Tracking
Prerequisites: Basic Python knowledge and familiarity with machine learning concepts.

Prologue: The Challenge

You join a machine learning team at a growing technology company. The team has built several production-quality models: a Sentiment Analyzer for customer feedback, a Product Categorizer for inventory management, and a Churn Predictor for customer retention.

However, these models exist only on data scientists' development machines. The product team cannot integrate them into dashboards. The mobile application cannot access predictions. The analytics pipeline remains disconnected from the intelligence the models provide.

Your task: Build a Model Management API—a centralized service that exposes these models to the rest of the organization.

This API will allow team members to:

Register new models with metadata (name, version, accuracy)
Retrieve information about deployed models
Serve predictions from registered models
Validate all inputs and outputs
Environment Setup

Update your environment and install required packages:

sudo apt update
sudo apt install -y python3-venv
Create a virtual environment:

python3 -m venv venv
source venv/bin/activate
Install required libraries:

pip install fastapi uvicorn joblib scikit-learn
Create project structure:

mkdir -p models optional
Chapter 1: Establishing the Foundation

Every production service begins with the same question: Is it running?

Before adding any business logic, you establish a health check endpoint. This simple endpoint serves a critical purpose—it allows orchestration systems, load balancers, and monitoring tools to verify the service is operational.

1.1 What You Will Build

A minimal FastAPI application with a /health endpoint. This forms the foundation for all subsequent features.

Key Concept: FastAPI uses Python type hints to automatically validate data, generate documentation, and provide IDE support.

1.2 Think First: Why Health Checks Matter

Before writing code, consider these questions:

Question 1: In a production environment, what systems need to know if your API is running?

Question 2: What should happen if the health check fails?

Click to review answers
1.3 Implementation: Build Your First Endpoint

Create a file called app.py. Before copying the solution, attempt to fill in the blanks:

from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="___",  # Q1: What should you name this API?
    description="API for managing and serving ML models",
    version="1.0.0"
)

@app.___("/health")  # Q2: What HTTP method for retrieving status?
async def health_check():
    """Basic health check endpoint"""
    return {"status": "___", "service": "model-api"}  # Q3: What status indicates success?

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=___)  # Q4: What is the standard HTTP port?
Click to see the complete solution
1.4 Understanding the Code

Match each code element to its purpose:

Code Element	Purpose (A-D)
FastAPI()	___
@app.get("/health")	___
async def	___
uvicorn.run()	___
Options:

A: Starts the ASGI server
B: Creates your application instance
C: Decorator that creates a GET endpoint
D: Enables asynchronous request handling
Click to check your answers
1.5 Run and Verify

Start the application:

python3 app.py
You should see output similar to:

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
1.6 Checkpoint

Open a new terminal (keep the server running) and test:

curl http://localhost:8000/health
Expected output:

{"status":"healthy","service":"model-api"}
Explore automatic documentation:

FastAPI generates interactive API documentation automatically. Open your browser to:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Self-Assessment:

Server starts without errors
Health endpoint returns expected JSON
Documentation is accessible at /docs
Chapter 2: Building the Catalog

The organization needs visibility into available models. Which models exist? What are their versions and performance metrics? Before anyone can use a model, they must first discover it.

You implement a model catalog—a queryable inventory of all registered models. The catalog answers two fundamental questions:

What models are available? (list all)
What are the details of a specific model? (retrieve one)
Error handling becomes essential. When a requested model does not exist, the API responds with a clear 404 status rather than failing silently or returning misleading data.

2.1 What You Will Build

Add endpoints to list all models and retrieve specific model information. This teaches you to:

Use path parameters ({model_id})
Handle 404 errors
Work with in-memory data storage


2.2 Think First: Error Scenarios

Before implementing, consider what could go wrong:

Question 1: A user requests /models/999. The model does not exist. What HTTP status code should the API return?

Question 2: What is the difference between returning null and raising an HTTP exception?

Click to review answers
2.3 Implementation: Add GET Endpoints

Add these imports and code to your app.py (after your health check endpoint):

First, attempt to complete the missing parts:

from fastapi import HTTPException

# In-memory model database
model_database = {
    1: {"name": "Sentiment Analyzer", "version": "1.0", "accuracy": 0.92, "status": "production"},
    2: {"name": "Product Categorizer", "version": "2.1", "accuracy": 0.88, "status": "production"},
    3: {"name": "Churn Predictor", "version": "1.5", "accuracy": 0.85, "status": "staging"}
}

@app.get("/models")
async def list_models():
    """List all registered models"""
    return {"models": model_database, "count": ___(model_database)}  # Q1: How to get the count?

@app.get("/models/{model_id}")
async def get_model_info(model_id: ___):  # Q2: What type should model_id be?
    """Retrieve information about a specific model"""
    if model_id ___ model_database:  # Q3: How to check if key is missing?
        raise HTTPException(status_code=___, detail=f"Model {model_id} not found")  # Q4: What code?

    return {"model_id": model_id, "details": model_database[model_id]}
Click to see the complete solution
2.4 Predict the Output

Before running the tests, predict what each command will return:

Test A: curl http://localhost:8000/models

Your prediction: _______________
Test B: curl http://localhost:8000/models/1

Your prediction: _______________
Test C: curl http://localhost:8000/models/99

Your prediction: _______________
2.5 Restart and Test

Stop your server (Ctrl+C) and restart:

python3 app.py
Run the tests and compare with your predictions:

# Test A: List all models
curl http://localhost:8000/models
Click to see expected output
# Test B: Get specific model
curl http://localhost:8000/models/1
Click to see expected output
# Test C: Non-existent model
curl http://localhost:8000/models/99
Click to see expected output
2.6 Checkpoint

Self-Assessment:

/models returns all three pre-loaded models
/models/1 returns the Sentiment Analyzer details
/models/99 returns a 404 error with clear message
You can explain why we use HTTPException instead of returning None
Chapter 3: The Registration System

Viewing existing models is useful, but the catalog becomes stale without a way to register new ones. The data science team trains new models weekly, and each needs to be added to the system.

However, registration introduces risk. What prevents someone from submitting invalid data—an accuracy score of "excellent" instead of a decimal, or a model without a name?

This is where Pydantic validation becomes essential. You define explicit schemas that describe exactly what a valid registration looks like. The API rejects malformed requests before they can corrupt the database, providing clear error messages that explain precisely what went wrong.

3.1 What You Will Build

A POST endpoint that allows registering new models with automatic validation. This introduces Pydantic, FastAPI's data validation layer.

Key Concept: Pydantic models define the shape of your data with type hints. FastAPI uses them to automatically:

Validate incoming requests
Generate API documentation
Provide clear error messages
Serialize responses


3.2 Think First: Why Validation Matters

Consider this incoming request:

{
  "model_id": "not-a-number",
  "name": "",
  "accuracy": 1.5
}
Question: Identify at least three problems with this data.

Click to review answers
3.3 Implementation: Define the Pydantic Model

Add the import at the top of your file:

from pydantic import BaseModel, Field
Now complete the Pydantic model definition:

class ModelRegistration(BaseModel):
    """Schema for registering a new model"""
    
    model_id: ___  # Q1: What type for a unique identifier?
    
    name: str = Field(..., ___=1)  # Q2: What constraint ensures name is not empty?
    
    version: str = Field(..., description="Model version (e.g., 1.0, 2.3.1)")
    
    accuracy: float = Field(..., ___=0.0, ___=1.0)  # Q3: What constraints for 0-100%?
    
    status: str = Field(default="staging")  # This one is complete
Hints:

... indicates a required field (no default)
min_length sets minimum string length
ge = greater than or equal, le = less than or equal
Click to see the complete solution
3.4 Implementation: Create the POST Endpoint

Complete the registration endpoint:

@app.post("/models", status_code=___)  # Q1: What code means "resource created"?
async def register_model(model: ___):  # Q2: What Pydantic class validates input?
    """Register a new model in the system"""
    
    if model.model_id in model_database:
        raise HTTPException(
            status_code=___,  # Q3: What code for "client made an error"?
            detail=f"Model {model.model_id} already exists. Use PUT to update."
        )

    # Add to database
    model_database[model.model_id] = model.model_dump(exclude={'model_id'})

    return ModelRegistrationResponse(
        message="Model registered successfully",
        model_id=model.model_id,
        details=model_database[model.model_id]
    )
Click to see the complete solution
3.5 Predict the Validation Behavior

Before testing, predict what happens in each scenario:

Scenario	Status Code	Reason
Valid data with all fields	___	___
Missing name field	___	___
accuracy = "high" (string)	___	___
accuracy = 1.5 (out of range)	___	___
Duplicate model_id	___	___
Click to check your predictions
3.6 Restart and Test

Restart your server and test successful registration:

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 4,
    "name": "Review Sentiment Classifier",
    "version": "1.0",
    "accuracy": 0.91,
    "status": "production"
  }'
Expected output:

{
  "message": "Model registered successfully",
  "model_id": 4,
  "details": {
    "name": "Review Sentiment Classifier",
    "version": "1.0",
    "accuracy": 0.91,
    "status": "production"
  }
}


Verify the model was added:

curl http://localhost:8000/models
You should now see 4 models.



3.7 Experiment: Break the Validation

Run each command and observe the error responses:

Experiment 1: Invalid type

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_id": 5, "name": "Test", "version": "1.0", "accuracy": "high"}'
Record: What status code did you receive? What does the error message say?

Experiment 2: Out-of-range value

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_id": 6, "name": "Test", "version": "1.0", "accuracy": -0.5}'
Record: Which validation rule caught this error?

Experiment 3: Empty name

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_id": 7, "name": "", "version": "1.0", "accuracy": 0.9}'
Record: What constraint prevented this registration?

3.8 Checkpoint

Self-Assessment:

Valid registrations return 201 and appear in the model list
Invalid types return 422 with descriptive errors
Out-of-range values are rejected
Empty names are rejected due to min_length=1
You can explain why we validate at the API boundary
Chapter 4: The Prediction Engine

The catalog and registration system serve an administrative purpose. The core value lies in predictions—the ability to send data and receive intelligent analysis in return.

Loading machine learning models presents an architectural decision. Models are often large—hundreds of megabytes of trained weights and parameters. Loading them on every request would create unacceptable latency.

The solution is lifecycle management. The model loads once when the server starts, remains in memory for the duration of the process, and unloads cleanly on shutdown. This pattern—implemented through FastAPI's lifespan hooks—is standard practice in production ML systems.

You also implement a readiness check. Unlike the health endpoint (which confirms the process is running), the readiness endpoint confirms the service can fulfill its purpose. If the model fails to load, the readiness check returns a 503 status, signaling that the service should not receive traffic.

4.1 What You Will Build

This section teaches you to:

Load a model at application startup (not on every request)
Use lifespan events for initialization
Create readiness checks
Serve predictions with proper error handling


4.2 Think First: Why Load at Startup?

Consider two approaches:

Approach A: Load per request

@app.post("/predict")
def predict(text: str):
    model = load_model()  # Load on every request
    return model.predict(text)
Approach B: Load at startup

# Load once at startup
ml_model = None

@asynccontextmanager
async def lifespan(app):
    global ml_model
    ml_model = load_model()
    yield
    ml_model = None
Question 1: If load_model() takes 2 seconds, and you receive 100 requests per second, what happens with Approach A?

Question 2: Why do we set ml_model = None after yield?

Click to review answers
4.3 Prepare the Model Artifact

Before the API can serve predictions, it needs a trained model.

Create optional/train_model.py:

"""
Simple sentiment classifier for demonstration purposes.
"""
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
    "Wonderful experience, highly recommend",
    "Outstanding product, exceeded expectations",
    "Terrible product, waste of money",
    "Poor quality and broke after one use",
    "Very disappointed with this purchase",
    "Awful experience, do not buy",
    "Complete garbage, total waste"
]
labels = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]  # 1=positive, 0=negative

# Train pipeline
model = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=100)),
    ('clf', LogisticRegression(random_state=42))
])
model.fit(texts, labels)

# Save model
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/sentiment_classifier.joblib')
print("Model saved to models/sentiment_classifier.joblib")
Run the training script:

python3 optional/train_model.py
Expected output: Model saved to models/sentiment_classifier.joblib

4.4 Implementation: Add Lifespan Management

Add new imports at the top of app.py:

from contextlib import asynccontextmanager
import joblib
from pathlib import Path
Add global model variable (before your FastAPI app initialization):

# Global model variable
ml_model = None
Replace your app = FastAPI(...) initialization with this lifespan-managed version:

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup, cleanup at shutdown"""
    global ml_model
    model_path = Path("models/sentiment_classifier.joblib")

    if model_path.exists():
        ml_model = joblib.load(model_path)
        print(f"Model loaded from {model_path}")
    else:
        print(f"Warning: Model not found at {model_path}")

    yield  # Application runs here

    # Cleanup
    ml_model = None
    print("Model unloaded")

app = FastAPI(
    title="ML Model Management API",
    description="API for managing and serving ML models",
    version="1.0.0",
    lifespan=lifespan
)
4.5 Implementation: Add Readiness Check

Add after your health check endpoint:

@app.get("/ready")
async def readiness_check():
    """Check if API is ready to serve predictions"""
    if ml_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready", "model_loaded": True}
Question: Why use status code 503 instead of 500?

Click for the answer
4.6 Implementation: Add Prediction Endpoint

Add the prediction schemas and endpoint:

class PredictionRequest(BaseModel):
    """Schema for prediction requests"""
    text: str = Field(..., min_length=1, description="Text to analyze")

class PredictionResponse(BaseModel):
    """Schema for prediction responses"""
    text: str
    sentiment: str
    confidence: float

@app.post("/predict", response_model=PredictionResponse)
async def predict_sentiment(request: PredictionRequest):
    """Predict sentiment of input text"""
    if ml_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Get prediction
    prediction = ml_model.predict([request.text])[0]
    probabilities = ml_model.predict_proba([request.text])[0]
    confidence = float(max(probabilities))

    sentiment = "positive" if prediction == 1 else "negative"

    return PredictionResponse(
        text=request.text,
        sentiment=sentiment,
        confidence=confidence
    )
4.7 Understanding the Prediction Logic

Match each method to its purpose:

Method	Returns
predict()	___
predict_proba()	___
max(probabilities)	___
Options:

A: The class label (0 or 1)
B: Probability scores for each class
C: The confidence of the predicted class
Click to check your answers
4.8 Restart and Test

Restart your server:

python3 app.py
You should see: Model loaded from models/sentiment_classifier.joblib

4.9 Checkpoint

Test readiness:

curl http://localhost:8000/ready
Expected output:

{"status": "ready", "model_loaded": true}
Test positive sentiment:

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is absolutely amazing and works perfectly!"}'
Expected output (confidence may vary):

{
  "text": "This product is absolutely amazing and works perfectly!",
  "sentiment": "positive",
  "confidence": 0.85
}


Test negative sentiment:

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Terrible quality and broke immediately, complete waste of money"}'
Expected output:

{
  "text": "Terrible quality and broke immediately, complete waste of money",
  "sentiment": "negative",
  "confidence": 0.87
}
4.10 Experiment: Model Loading Failure

To understand why readiness checks matter, simulate a missing model:

Rename the model file:
mv models/sentiment_classifier.joblib models/sentiment_classifier.joblib.backup
Restart the server and observe the startup message

Test the readiness endpoint:

curl http://localhost:8000/ready
Record: What status code do you receive? What is the error message?

Restore the model:
mv models/sentiment_classifier.joblib.backup models/sentiment_classifier.joblib
Restart and verify the readiness check succeeds
Self-Assessment:

Model loads successfully at startup
Readiness endpoint returns 200 when model is loaded
Readiness endpoint returns 503 when model is missing
Predictions return correct sentiment labels
You can explain why we load at startup instead of per-request
Chapter 5: Defensive Design

Production systems must handle incorrect input gracefully. Users will submit malformed requests—sometimes by accident, sometimes through integration errors, occasionally through deliberate probing.

The validation layer you built in Chapter 3 now demonstrates its value. Invalid accuracy values, missing required fields, empty prediction text—each triggers a specific, informative error response. The API never accepts bad data, and callers always understand why their request failed.

5.1 Understanding Request/Response Validation

FastAPI and Pydantic provide automatic validation for both incoming requests and outgoing responses.



5.2 HTTP Status Code Reference

Complete this reference table:

Status Code	Meaning	When to Use
200	___	Successful GET request
201	___	Resource created via POST
400	___	Client sent invalid request
404	___	___
422	___	___
500	___	Server-side error
503	___	___
Click to see completed table
5.3 Validation Testing

Run each test and record the results:

Test 1: Invalid data type

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 10,
    "name": "Test Model",
    "version": "1.0",
    "accuracy": "very high"
  }'
Record: Status code: ___ Error field: ___

Test 2: Out-of-range value

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 11,
    "name": "Test Model",
    "version": "1.0",
    "accuracy": 1.5
  }'
Record: Status code: ___ Constraint violated: ___

Test 3: Missing required field

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 12,
    "version": "1.0",
    "accuracy": 0.9
  }'
Record: Status code: ___ Missing field: ___

Test 4: Empty prediction text

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": ""}'
Record: Status code: ___ Constraint violated: ___

5.4 Valid Data Verification

Confirm the system accepts valid data:

curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 20,
    "name": "Image Classifier",
    "version": "2.0",
    "accuracy": 0.94,
    "status": "production"
  }'


5.5 Checkpoint

Self-Assessment:

You can predict which status code will be returned for different error types
You understand the difference between 400 (business logic) and 422 (validation)
You can explain why validation at the API boundary prevents downstream errors
Chapter 6: Operational Visibility (Optional)

As the system grows, questions arise. Which model versions have been registered? How have accuracy metrics changed over time? Who registered what, and when?

MLflow Tracking provides this operational visibility. Each registration creates a tracked record—parameters, metrics, and artifacts preserved for later analysis. This is experiment tracking, not model deployment (MLflow's Model Registry serves that separate purpose).

6.1 What is MLflow Tracking?

MLflow Tracking allows you to:

Log parameters (hyperparameters, configuration values)
Log metrics (accuracy, loss, latency)
Store artifacts (files, models, plots)
Track experiments over time
Important: This section demonstrates MLflow's experiment tracking feature. Model Registry, which manages versioned model artifacts for deployment, is an advanced topic covered in later labs.

6.2 Install MLflow

pip install mlflow
6.3 Add MLflow Integration

Add import at the top of app.py:

import mlflow
Add MLflow configuration after your FastAPI app initialization:

mlflow.set_tracking_uri("file:./mlruns")
Add a new endpoint for registration with tracking:

@app.post("/models/track", status_code=201)
async def register_model_with_tracking(model: ModelRegistration):
    """Register model and log metadata to MLflow Tracking"""
    if model.model_id in model_database:
        raise HTTPException(status_code=400, detail="Model already exists")

    # Log to MLflow Tracking
    with mlflow.start_run(run_name=f"register_{model.name}"):
        mlflow.log_param("model_name", model.name)
        mlflow.log_param("version", model.version)
        mlflow.log_metric("accuracy", model.accuracy)
        mlflow.log_dict(model.model_dump(), "model_metadata.json")

        run_id = mlflow.active_run().info.run_id

    # Add to database
    model_database[model.model_id] = {
        **model.model_dump(exclude={'model_id'}),
        "mlflow_run_id": run_id
    }

    return {
        "message": "Model registered and logged to MLflow Tracking",
        "model_id": model.model_id,
        "mlflow_run_id": run_id,
        "details": model_database[model.model_id]
    }
6.4 Test MLflow Integration

Restart your server and test:

curl -X POST http://localhost:8000/models/track \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 30,
    "name": "Deep Learning Classifier",
    "version": "3.0",
    "accuracy": 0.96,
    "status": "production"
  }'


Verify:

curl http://localhost:8000/models


6.5 View MLflow UI

Start the MLflow UI server in a new terminal:

mlflow server --host 0.0.0.0 --port 5000 --allowed-hosts '*' --cors-allowed-origins '*'
Access the UI at http://localhost:5000 (or through your VM's exposed port).



Click on an experiment to see parameters and metrics:



View artifacts:



Epilogue: The Complete System

You step back to assess what you have built. A single file. A single server. Seven endpoints working in concert:

Method	Endpoint	Purpose
GET	/health	Process liveness verification
GET	/ready	Service readiness verification
GET	/models	Model catalog listing
GET	/models/{model_id}	Individual model details
POST	/models	Model registration
POST	/predict	Prediction serving
POST	/models/track	Registration with tracking (optional)
End-to-End Verification

Run all endpoints in sequence to verify your complete API:

curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/models
curl http://localhost:8000/models/1
curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_id":50,"name":"Final Test","version":"1.0","accuracy":0.95}'
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"This is an excellent product!"}'
All commands should succeed without restarting the server.

View your automatic documentation at http://localhost:8000/docs:



The Principles

Building an ML API follows a deliberate progression:

Start with operational endpoints — Health and readiness checks come first
Build features incrementally — Read operations before write operations, metadata before predictions
Validate at the boundary — Reject invalid input before it reaches business logic
Manage resources efficiently — Load expensive resources once, not per-request
Report failures honestly — Readiness checks prevent serving requests the system cannot fulfill
Maintain operational visibility — Tracking enables debugging and auditing
Final Self-Assessment

Before completing this lab, verify you can answer these questions:

Why do we implement /health and /ready as separate endpoints?

What is the difference between status codes 400, 404, and 422?

Why is loading ML models at startup preferable to loading per-request?

How does Pydantic's Field() function help with data validation?

What happens if a client sends a request while the model is still loading?

Click to review answers
Troubleshooting

Model not loading

Error: Warning: Model not found at models/sentiment_classifier.joblib

Solution:

python3 optional/train_model.py
Port already in use

Error: Address already in use

Solution:

lsof -ti:8000 | xargs kill -9
Import errors

Error: ModuleNotFoundError: No module named 'fastapi'

Solution:

source venv/bin/activate
pip install fastapi uvicorn joblib scikit-learn
Next Steps

To continue developing your FastAPI expertise, consider:

Database integration: Replace in-memory storage with PostgreSQL or MongoDB
Authentication: Implement JWT tokens or API keys
Multiple model types: Support classification, regression, and clustering
Containerization: Create a Dockerfile for deployment
Caching: Add Redis for response caching
Monitoring: Integrate Prometheus metrics
Cloud deployment: Deploy on AWS, GCP, or Azure
Additional Resources

FastAPI Documentation
Pydantic Documentation
MLflow Documentation
Uvicorn Documentation