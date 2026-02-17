#!/bin/bash
set -e

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-your-dockerhub-username}"
IMAGE_NAME="fastapi-app"
TAG="${TAG:-latest}"
FULL_IMAGE="$DOCKER_USERNAME/$IMAGE_NAME:$TAG"

echo "🐳 Building Docker image..."
docker build -t $FULL_IMAGE .

echo "📤 Pushing to Docker Hub..."
docker push $FULL_IMAGE

echo "✅ Image pushed: $FULL_IMAGE"
echo ""
echo "🚀 To deploy to EC2, run:"
echo "   pulumi config set docker_image $FULL_IMAGE -C infra"
echo "   pulumi up --yes -C infra"
echo ""
echo "Or to update existing EC2 instance:"
echo "   ssh ec2-user@\$(pulumi stack output instance_public_ip -C infra) 'docker pull $FULL_IMAGE && docker stop fastapi-app && docker rm fastapi-app && docker run -d --name fastapi-app --restart unless-stopped -p 80:8000 -e DATABASE_URL=\"postgresql://postgres:postgres@100.84.183.142:5432/postgres\" $FULL_IMAGE'"
