# Machine Learning Model Integration Guide

## Overview

This application includes a simple sentiment analysis model that classifies text as positive or negative.

## Model Details

- **Type**: Sentiment Classifier
- **Algorithm**: Logistic Regression with TF-IDF vectorization
- **Classes**: Positive (1) and Negative (0)
- **Training Data**: 16 sample reviews (8 positive, 8 negative)
- **Features**: TF-IDF with max 100 features and bigrams

## Quick Start

### 1. Train the Model Locally

```bash
cd app
python train_model.py
```

This creates `models/sentiment_model.joblib`.

### 2. Test Locally

```bash
# Start the application
uvicorn main:app --reload

# Test the prediction endpoint
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing!"}'
```

Expected response:
```json
{
  "text": "This product is amazing!",
  "sentiment": "positive",
  "confidence": 0.85
}
```

## API Endpoints

### 1. Predict Sentiment

**POST** `/predict`

Request:
```json
{
  "text": "Your text here"
}
```

Response:
```json
{
  "text": "Your text here",
  "sentiment": "positive",
  "confidence": 0.92
}
```

### 2. Model Information

**GET** `/model/info`

Response:
```json
{
  "loaded": true,
  "model_type": "Sentiment Classifier",
  "algorithm": "Logistic Regression with TF-IDF",
  "classes": ["negative", "positive"]
}
```

### 3. Health Check (includes model status)

**GET** `/health`

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "ml_model": "loaded"
}
```

## Testing Examples

### Positive Sentiment
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Excellent product, highly recommend!"}'
```

### Negative Sentiment
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Terrible quality, very disappointed"}'
```

### Neutral/Mixed Text
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "The product arrived on time"}'
```

## Docker Deployment

The model is automatically trained during Docker image build:

```bash
# Build image (trains model automatically)
docker build -t fastapi-app .

# Run container
docker run -p 8000:8000 fastapi-app

# Test
curl http://localhost:8000/model/info
```

## Kubernetes Deployment

The model is included in the container image and loaded on startup:

```bash
# Deploy to EKS
kubectl apply -f k8s/deployment.yaml

# Check if model is loaded
kubectl logs -l app=fastapi | grep "ML model"

# Test via Load Balancer
LB_URL=$(kubectl get service fastapi-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$LB_URL/model/info
```

## Model Performance

This is a **minimal demonstration model** with limited training data. For production use:

### Improvements Needed:
1. **More Training Data**: Use thousands of labeled examples
2. **Better Features**: Use word embeddings (Word2Vec, GloVe) or transformers
3. **Model Validation**: Split data into train/validation/test sets
4. **Hyperparameter Tuning**: Optimize model parameters
5. **Model Versioning**: Track model versions with MLflow or similar
6. **A/B Testing**: Compare model versions in production
7. **Monitoring**: Track prediction accuracy over time

### Production-Ready Alternatives:
- **Hugging Face Transformers**: Pre-trained BERT, RoBERTa models
- **spaCy**: Industrial-strength NLP
- **TensorFlow/PyTorch**: Deep learning models
- **Cloud ML Services**: AWS Comprehend, Google Cloud NLP

## Upgrading the Model

### Option 1: Replace with Better Model

```python
# app/train_model.py
from transformers import pipeline

# Use pre-trained transformer
classifier = pipeline("sentiment-analysis")

# Save for later use
import joblib
joblib.dump(classifier, 'models/sentiment_model.joblib')
```

### Option 2: Add More Training Data

```python
# Expand training data in train_model.py
texts = [
    # Add hundreds or thousands of examples
    "...",
]
labels = [1, 0, 1, ...]  # Corresponding labels
```

### Option 3: Use Transfer Learning

```python
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

# Use pre-trained embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedder.encode(texts)

# Train classifier on embeddings
classifier = LogisticRegression()
classifier.fit(embeddings, labels)
```

## Monitoring Model Performance

### Track Predictions

Add logging to track predictions:

```python
import logging

@app.post("/predict")
def predict_sentiment(request: PredictionRequest):
    result = ml_model.predict([request.text])[0]
    
    # Log prediction
    logging.info(f"Prediction: {request.text[:50]} -> {result}")
    
    return result
```

### Add Metrics

Track prediction metrics with Prometheus:

```python
from prometheus_client import Counter, Histogram

prediction_counter = Counter('predictions_total', 'Total predictions', ['sentiment'])
prediction_confidence = Histogram('prediction_confidence', 'Prediction confidence')

@app.post("/predict")
def predict_sentiment(request: PredictionRequest):
    result = ml_model.predict([request.text])[0]
    confidence = max(ml_model.predict_proba([request.text])[0])
    
    # Track metrics
    sentiment = "positive" if result == 1 else "negative"
    prediction_counter.labels(sentiment=sentiment).inc()
    prediction_confidence.observe(confidence)
    
    return result
```

## Troubleshooting

### Model Not Loading

**Error**: `ML model not loaded`

**Solution**:
```bash
# Train the model
cd app
python train_model.py

# Verify model file exists
ls -lh models/sentiment_model.joblib

# Rebuild Docker image
docker build -t fastapi-app .
```

### Low Confidence Predictions

**Issue**: Model returns low confidence scores

**Causes**:
- Input text very different from training data
- Model needs more training data
- Text preprocessing issues

**Solution**: Retrain with more diverse examples

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'sklearn'`

**Solution**:
```bash
pip install -r app/requirements.txt
```

## Next Steps

1. **Collect Real Data**: Gather actual user reviews or feedback
2. **Label Data**: Create a labeled dataset for training
3. **Experiment**: Try different algorithms and features
4. **Validate**: Use cross-validation to assess performance
5. **Deploy**: Update the model in production
6. **Monitor**: Track accuracy and retrain as needed

## Resources

- [Scikit-learn Documentation](https://scikit-learn.org/)
- [FastAPI ML Tutorial](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [MLflow for Model Tracking](https://mlflow.org/)
