#!/bin/bash
# ZTNA Platform Setup Script

set -e

echo "🔒 ZTNA Platform Setup"
echo "======================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

echo "✅ docker-compose is available"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p infra/nginx/conf.d
mkdir -p infra/nginx/ssl

# Copy realm export if it doesn't exist in infra
if [ ! -f "infra/realm-export.json" ] && [ -f "realm-export.json" ]; then
    echo "📋 Copying Keycloak realm export..."
    cp realm-export.json infra/realm-export.json
fi

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚙️  Creating backend .env file..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Created backend/.env from .env.example"
    else
        echo "⚠️  backend/.env.example not found. Please create backend/.env manually."
    fi
else
    echo "✅ backend/.env already exists"
fi

# Start services
echo ""
echo "🚀 Starting services..."
cd infra
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Wait 30-60 seconds for Keycloak to fully start"
echo "2. Run database migrations: make migrate"
echo "3. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000/docs"
echo "   - Keycloak: http://localhost:8080"
echo ""
echo "📖 See QUICKSTART.md for detailed instructions"

