# ML Model Quick Start

## What Was Added

A simple sentiment analysis model that classifies text as positive or negative.

## Files Created/Modified

### New Files:
- `app/train_model.py` - Script to train the sentiment model
- `ML_MODEL_GUIDE.md` - Complete documentation
- `test_ml_model.sh` - Test script for all ML endpoints
- `ML_QUICKSTART.md` - This file

### Modified Files:
- `app/main.py` - Added ML model loading and prediction endpoints
- `app/requirements.txt` - Added scikit-learn and joblib
- `Dockerfile` - Added model training step during build

## Quick Test (Local)

```bash
# 1. Install dependencies
cd app
pip install -r requirements.txt

# 2. Train the model
python train_model.py

# 3. Start the app
uvicorn main:app --reload

# 4. Test in another terminal
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing!"}'
```

## New API Endpoints

### 1. POST /predict
Predict sentiment of text

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here"}'
```

Response:
```json
{
  "text": "Your text here",
  "sentiment": "positive",
  "confidence": 0.92
}
```

### 2. GET /model/info
Get model information

```bash
curl http://localhost:8000/model/info
```

Response:
```json
{
  "loaded": true,
  "model_type": "Sentiment Classifier",
  "algorithm": "Logistic Regression with TF-IDF",
  "classes": ["negative", "positive"]
}
```

### 3. GET /health (updated)
Now includes ML model status

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "ml_model": "loaded"
}
```

## Docker Deployment

The model is automatically trained during image build:

```bash
# Build (trains model automatically)
docker build -t fastapi-app .

# Run
docker run -p 8000:8000 fastapi-app

# Test
curl http://localhost:8000/model/info
```

## Kubernetes/EKS Deployment

Model is included in the container and loaded on startup:

```bash
# Build and push to ECR
docker build -t <ECR_URL>:latest .
docker push <ECR_URL>:latest

# Deploy to EKS
kubectl apply -f k8s/deployment.yaml
kubectl rollout restart deployment fastapi-deployment

# Test
LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/model/info
curl -X POST http://$LB_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Great product!"}'
```

## Run All Tests

```bash
# Make script executable
chmod +x test_ml_model.sh

# Test locally
./test_ml_model.sh

# Test on EKS
./test_ml_model.sh http://<LOAD_BALANCER_URL>
```

## Important Notes

1. **This is a minimal demo model** - Only trained on 16 examples
2. **Not production-ready** - Use for learning/testing only
3. **For production**: Use more data, better algorithms, proper validation
4. **Model is baked into Docker image** - Rebuild image to update model

## Next Steps

1. Read `ML_MODEL_GUIDE.md` for detailed documentation
2. Improve the model with more training data
3. Add model versioning and A/B testing
4. Monitor prediction accuracy in production
5. Consider using pre-trained models (Hugging Face)

## Troubleshooting

**Model not loading?**
```bash
# Check if model file exists
ls -lh app/models/sentiment_model.joblib

# Retrain
cd app && python train_model.py
```

**Import errors?**
```bash
pip install -r app/requirements.txt
```

**Low confidence predictions?**
- Model needs more training data
- Input text very different from training examples
- This is expected with a minimal demo model
