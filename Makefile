.PHONY: help install test lint format docker-build docker-up docker-down deploy clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start local stack"
	@echo "  make docker-down   - Stop local stack"
	@echo "  make deploy        - Deploy to AWS"
	@echo "  make clean         - Clean up"

install:
	pip install -r app/requirements.txt
	pip install black flake8 pytest-cov
	cd infra && pip install -r requirements.txt

test:
	POSTGRES_HOST=localhost pytest app/test_main.py -v --cov=app

lint:
	flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 app --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black app/

docker-build:
	docker build -t fastapi-app .

docker-up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Services available at:"
	@echo "  FastAPI: http://localhost:8000"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3000"

docker-down:
	docker-compose down -v

deploy:
	cd infra && pulumi up

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v
	docker system prune -f
