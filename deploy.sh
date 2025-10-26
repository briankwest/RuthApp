#!/bin/bash

# Deployment script for Ruth application
# Usage: ./deploy.sh [service]
#   ./deploy.sh frontend  - Deploy only frontend
#   ./deploy.sh backend   - Deploy only backend
#   ./deploy.sh all       - Deploy all services (default)

set -e  # Exit on error

SERVICE=${1:-all}

echo "🚀 Deploying Ruth - Service: $SERVICE"

case $SERVICE in
  frontend)
    echo "📦 Building frontend..."
    docker-compose build frontend
    echo "🔄 Recreating frontend container..."
    docker-compose up -d frontend
    echo "🔄 Restarting nginx..."
    docker-compose restart nginx
    echo "✅ Frontend deployed successfully!"
    ;;

  backend)
    echo "📦 Building backend services..."
    docker-compose build backend celery_worker celery_beat
    echo "🔄 Recreating backend containers..."
    docker-compose up -d backend celery_worker celery_beat
    echo "🔄 Restarting nginx..."
    docker-compose restart nginx
    echo "✅ Backend deployed successfully!"
    ;;

  all)
    echo "📦 Building all services..."
    docker-compose build
    echo "🔄 Recreating all containers..."
    docker-compose up -d
    echo "✅ All services deployed successfully!"
    ;;

  *)
    echo "❌ Unknown service: $SERVICE"
    echo "Usage: ./deploy.sh [frontend|backend|all]"
    exit 1
    ;;
esac

echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "🔍 Verifying deployment..."
sleep 2
curl -s https://ruthapp.us/health && echo " - Health check passed ✅" || echo " - Health check failed ❌"
