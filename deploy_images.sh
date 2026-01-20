#!/bin/bash
set -e

# Default to seen0516 from README, but allow override
REPO_USER="${REPO_USER:-seen0516}"

echo "🚀 Starting Multi-Arch Build & Push for user: $REPO_USER"

# Check for docker login (basic check)
if ! docker system info | grep -q "Username"; then
    echo "⚠️  Warning: It doesn't look like you are logged in to Docker Hub."
    echo "   If the push fails, run 'docker login' and try again."
fi

# Ensure buildx builder exists and is ready
echo "🛠  Configuring Docker Buildx..."
# Create a builder instance if it doesn't exist, or just use the default one if it supports multi-platform (docker-container driver)
# We try to create a new one to be safe for multi-arch
if ! docker buildx inspect multiarch-builder > /dev/null 2>&1; then
    docker buildx create --name multiarch-builder --driver docker-container --use
else
    docker buildx use multiarch-builder
fi
docker buildx inspect --bootstrap

# Backend Build
echo "📦 Building Backend..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${REPO_USER}/jira-api-backend:latest" \
  -f Dockerfile.backend \
  --push .

# Frontend Build
echo "🎨 Building Frontend..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${REPO_USER}/jira-api-frontend:latest" \
  -f Dockerfile.frontend \
  --push .

echo "✅ All images built and pushed successfully!"
