# API Testing Guide

Complete guide to test your deployed FastAPI application on AWS EC2.

## Prerequisites

Get your EC2 public IP:
```bash
cd infra
pulumi stack output instance_public_ip
```

For this guide, we'll use: `http://13.212.149.148` (replace with your actual IP)

---

## 1. Testing with cURL

### 1.1 Health Check
```bash
curl http://13.212.149.148/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "database": "connected",
  "ml_model": "loaded"
}
```

### 1.2 Root Endpoint
```bash
curl http://13.212.149.148/
```

**Expected Output:**
```json
{
  "status": "online",
  "service": "FastAPI on AWS EC2",
  "version": "1.0.0",
  "ml_model_loaded": true
}
```

### 1.3 Create an Item (POST)
```bash
curl -X POST http://13.212.149.148:8000/items \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "description": "This is a test product"
  }'
```

**Expected Output:**
```json
{
  "id": 1,
  "name": "Test Product",
  "description": "This is a test product",
  "created_at": "2026-02-17T12:00:00.123456"
}
```

### 1.4 List All Items (GET)
```bash
curl http://13.212.149.148:8000/items
```

**Expected Output:**
```json
[
  {
    "id": 1,
    "name": "Test Product",
    "description": "This is a test product",
    "created_at": "2026-02-17T12:00:00.123456"
  }
]
```

### 1.5 Get Specific Item (GET)
```bash
curl http://13.212.149.148:8000/items/1
```

**Expected Output:**
```json
{
  "id": 1,
  "name": "Test Product",
  "description": "This is a test product",
  "created_at": "2026-02-17T12:00:00.123456"
}
```

### 1.6 Get Non-existent Item (404)
```bash
curl http://13.212.149.148/items/999
```

**Expected Output:**
```json
{
  "detail": "Item not found"
}
```

### 1.7 ML Model - Predict Sentiment (Positive)
```bash
curl -X POST http://13.212.149.148:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This product is absolutely amazing! Best purchase ever!"
  }'
```

**Expected Output:**
```json
{
  "text": "This product is absolutely amazing! Best purchase ever!",
  "sentiment": "positive",
  "confidence": 0.85
}
```

### 1.8 ML Model - Predict Sentiment (Negative)
```bash
curl -X POST http://13.212.149.148/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Terrible quality, complete waste of money. Very disappointed."
  }'
```

**Expected Output:**
```json
{
  "text": "Terrible quality, complete waste of money. Very disappointed.",
  "sentiment": "negative",
  "confidence": 0.82
}
```

### 1.9 ML Model Info
```bash
curl http://13.212.149.148/model/info
```

**Expected Output:**
```json
{
  "loaded": true,
  "model_type": "Sentiment Classifier",
  "algorithm": "Logistic Regression with TF-IDF",
  "classes": ["negative", "positive"]
}
```

### 1.10 Prometheus Metrics
```bash
curl http://13.212.149.148/metrics
```

**Expected Output:**
```
# HELP starlette_requests_total Total count of requests by method and path.
# TYPE starlette_requests_total counter
starlette_requests_total{method="GET",path_template="/"} 5.0
...
```

---

## 2. Testing with Swagger UI (Interactive API Docs)

### Access Swagger UI
Open in your browser:
```
http://13.212.149.148/docs
```

### What You'll See:
- **Interactive API documentation** with all endpoints
- **Try it out** buttons to test each endpoint
- **Request/Response schemas** automatically generated
- **Authentication** section (if configured)

### How to Use:
1. Click on any endpoint (e.g., `POST /items`)
2. Click **"Try it out"**
3. Edit the request body in the JSON editor
4. Click **"Execute"**
5. See the response below with status code and body

### Example: Create Item via Swagger
1. Navigate to `http://13.212.149.148/docs`
2. Find `POST /items`
3. Click "Try it out"
4. Replace the example JSON:
   ```json
   {
     "name": "Laptop",
     "description": "High-performance laptop"
   }
   ```
5. Click "Execute"
6. See the response with the created item

### Example: Test ML Prediction via Swagger
1. Find `POST /predict`
2. Click "Try it out"
3. Enter text:
   ```json
   {
     "text": "I love this product!"
   }
   ```
4. Click "Execute"
5. See sentiment prediction result

---

## 3. Testing with Postman

### 3.1 Setup Postman Collection

#### Create New Collection
1. Open Postman
2. Click **"New"** → **"Collection"**
3. Name it: `FastAPI AWS Deployment`
4. Add description: `Testing FastAPI application on EC2`

#### Set Base URL Variable
1. Click on your collection
2. Go to **"Variables"** tab
3. Add variable:
   - Variable: `base_url`
   - Initial Value: `http://13.212.149.148`
   - Current Value: `http://13.212.149.148`

### 3.2 Create Requests

#### Request 1: Health Check
- **Method:** GET
- **URL:** `{{base_url}}/health`
- **Tests Tab:**
  ```javascript
  pm.test("Status is healthy", function () {
      pm.response.to.have.status(200);
      pm.expect(pm.response.json().status).to.eql("healthy");
  });
  ```

#### Request 2: Create Item
- **Method:** POST
- **URL:** `{{base_url}}/items`
- **Headers:**
  - `Content-Type: application/json`
- **Body (raw JSON):**
  ```json
  {
    "name": "Gaming Mouse",
    "description": "RGB gaming mouse with 16000 DPI"
  }
  ```
- **Tests Tab:**
  ```javascript
  pm.test("Item created successfully", function () {
      pm.response.to.have.status(200);
      const response = pm.response.json();
      pm.expect(response).to.have.property("id");
      pm.expect(response.name).to.eql("Gaming Mouse");
      
      // Save item ID for later use
      pm.collectionVariables.set("item_id", response.id);
  });
  ```

#### Request 3: Get All Items
- **Method:** GET
- **URL:** `{{base_url}}/items`
- **Tests Tab:**
  ```javascript
  pm.test("Returns array of items", function () {
      pm.response.to.have.status(200);
      const items = pm.response.json();
      pm.expect(items).to.be.an('array');
      pm.expect(items.length).to.be.above(0);
  });
  ```

#### Request 4: Get Specific Item
- **Method:** GET
- **URL:** `{{base_url}}/items/{{item_id}}`
- **Tests Tab:**
  ```javascript
  pm.test("Returns specific item", function () {
      pm.response.to.have.status(200);
      const item = pm.response.json();
      pm.expect(item.id).to.eql(parseInt(pm.collectionVariables.get("item_id")));
  });
  ```

#### Request 5: Predict Positive Sentiment
- **Method:** POST
- **URL:** `{{base_url}}/predict`
- **Headers:**
  - `Content-Type: application/json`
- **Body (raw JSON):**
  ```json
  {
    "text": "Excellent product! Highly recommend to everyone!"
  }
  ```
- **Tests Tab:**
  ```javascript
  pm.test("Predicts positive sentiment", function () {
      pm.response.to.have.status(200);
      const prediction = pm.response.json();
      pm.expect(prediction.sentiment).to.eql("positive");
      pm.expect(prediction.confidence).to.be.above(0.5);
  });
  ```

#### Request 6: Predict Negative Sentiment
- **Method:** POST
- **URL:** `{{base_url}}/predict`
- **Headers:**
  - `Content-Type: application/json`
- **Body (raw JSON):**
  ```json
  {
    "text": "Worst purchase ever. Broke after one day. Total waste of money."
  }
  ```
- **Tests Tab:**
  ```javascript
  pm.test("Predicts negative sentiment", function () {
      pm.response.to.have.status(200);
      const prediction = pm.response.json();
      pm.expect(prediction.sentiment).to.eql("negative");
      pm.expect(prediction.confidence).to.be.above(0.5);
  });
  ```

#### Request 7: Model Info
- **Method:** GET
- **URL:** `{{base_url}}/model/info`
- **Tests Tab:**
  ```javascript
  pm.test("Model is loaded", function () {
      pm.response.to.have.status(200);
      const info = pm.response.json();
      pm.expect(info.loaded).to.be.true;
      pm.expect(info.model_type).to.eql("Sentiment Classifier");
  });
  ```

### 3.3 Run Collection
1. Click on your collection
2. Click **"Run"** button
3. Select all requests
4. Click **"Run FastAPI AWS Deployment"**
5. Watch all tests execute automatically
6. View results summary

### 3.4 Export Collection
1. Click on collection → **"..."** → **"Export"**
2. Choose **"Collection v2.1"**
3. Save as `FastAPI_AWS_Deployment.postman_collection.json`
4. Share with your team!

---

## 4. Alternative Testing Methods

### 4.1 Using HTTPie (prettier than cURL)
```bash
# Install httpie
pip install httpie

# Test endpoints
http GET http://13.212.149.148/health
http POST http://13.212.149.148/items name="Test" description="Test item"
http POST http://13.212.149.148/predict text="Amazing product!"
```

### 4.2 Using Python Requests
```python
import requests

BASE_URL = "http://13.212.149.148"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Create item
item_data = {"name": "Test", "description": "Test item"}
response = requests.post(f"{BASE_URL}/items", json=item_data)
print(response.json())

# Predict sentiment
text_data = {"text": "This is amazing!"}
response = requests.post(f"{BASE_URL}/predict", json=text_data)
print(response.json())
```

### 4.3 Using Browser
Simply open in your browser:
- API Docs: `http://13.212.149.148/docs`
- Alternative Docs: `http://13.212.149.148/redoc`
- Health Check: `http://13.212.149.148/health`
- Root: `http://13.212.149.148/`

---

## 5. Load Testing (Optional)

### Using Apache Bench
```bash
# Install
sudo apt-get install apache2-utils

# Test 1000 requests with 10 concurrent
ab -n 1000 -c 10 http://13.212.149.148/health
```

### Using wrk
```bash
# Install
sudo apt-get install wrk

# Test for 30 seconds with 10 connections
wrk -t10 -c10 -d30s http://13.212.149.148/health
```

---

## 6. Monitoring Endpoints

### Prometheus Metrics
```bash
curl http://13.212.149.148/metrics
```

### Health Status
```bash
# Continuous monitoring
watch -n 5 'curl -s http://13.212.149.148/health | jq'
```

---

## 7. Expected Response Codes

| Endpoint | Method | Success Code | Error Codes |
|----------|--------|--------------|-------------|
| `/` | GET | 200 | - |
| `/health` | GET | 200 | - |
| `/items` | GET | 200 | - |
| `/items` | POST | 200 | 422 (validation) |
| `/items/{id}` | GET | 200 | 404 (not found) |
| `/predict` | POST | 200 | 422 (validation), 503 (model not loaded) |
| `/model/info` | GET | 200 | 503 (model not loaded) |
| `/metrics` | GET | 200 | - |

---

## 8. Troubleshooting

### Connection Refused
```bash
# Check if container is running
ssh -i fastapi-ec2-key.pem ubuntu@13.212.149.148 'docker ps'

# Check container logs
ssh -i fastapi-ec2-key.pem ubuntu@13.212.149.148 'docker logs fastapi-app'
```

### 404 Not Found
- Verify the endpoint path is correct
- Check Swagger docs for available endpoints

### 422 Validation Error
- Check request body matches the schema
- Verify Content-Type header is `application/json`

### 503 Service Unavailable
- ML model might not be loaded
- Check `/model/info` endpoint
- Review container logs

---

## 9. Quick Test Script

Save as `test-api.sh`:
```bash
#!/bin/bash

BASE_URL="http://13.212.149.148"

echo "🔍 Testing FastAPI Deployment..."
echo ""

echo "1. Health Check:"
curl -s $BASE_URL/health | jq
echo ""

echo "2. Create Item:"
curl -s -X POST $BASE_URL/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Test item"}' | jq
echo ""

echo "3. List Items:"
curl -s $BASE_URL/items | jq
echo ""

echo "4. Predict Sentiment (Positive):"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Amazing product!"}' | jq
echo ""

echo "5. Model Info:"
curl -s $BASE_URL/model/info | jq
echo ""

echo "✅ All tests complete!"
```

Run it:
```bash
chmod +x test-api.sh
./test-api.sh
```

---

## Summary

You now have multiple ways to test your deployed API:
- ✅ **cURL** - Quick command-line testing
- ✅ **Swagger UI** - Interactive browser-based testing
- ✅ **Postman** - Professional API testing with collections
- ✅ **Python/HTTPie** - Programmatic testing
- ✅ **Load Testing** - Performance validation

All endpoints are working and accessible from outside the EC2 instance!
