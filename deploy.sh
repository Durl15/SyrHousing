#!/bin/bash
# SyrHousing VPS Deployment Script
# Run on a fresh Ubuntu/Debian VPS
#
# Usage:
#   1. Copy project to server: scp -r . user@server:/opt/syrhousing
#   2. SSH to server: ssh user@server
#   3. Run: cd /opt/syrhousing && chmod +x deploy.sh && sudo ./deploy.sh
#
# Prerequisites: Ubuntu 22.04+ or Debian 12+

set -e

echo "=== SyrHousing Deployment ==="
echo ""

# Check if .env.production is configured
if grep -q "CHANGE_ME" .env.production 2>/dev/null; then
    echo "ERROR: .env.production contains placeholder values."
    echo "Edit .env.production and replace all CHANGE_ME values before deploying."
    echo ""
    echo "Quick setup:"
    echo "  1. cp .env.production .env.production.bak"
    echo "  2. Generate secret: openssl rand -hex 32"
    echo "  3. Edit .env.production with your values"
    exit 1
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "Docker installed."
fi

# Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
    echo "Docker Compose installed."
fi

# Choose deployment mode
echo ""
echo "Select database mode:"
echo "  1) SQLite (simple, single-server, default)"
echo "  2) PostgreSQL (recommended for production)"
read -p "Choice [1]: " DB_MODE
DB_MODE=${DB_MODE:-1}

COMPOSE_FILE="docker-compose.yml"
if [ "$DB_MODE" = "2" ]; then
    COMPOSE_FILE="docker-compose.postgres.yml"
    echo "Using PostgreSQL deployment."
else
    echo "Using SQLite deployment."
fi

# Build and start
echo ""
echo "Building and starting containers..."
docker compose -f "$COMPOSE_FILE" build
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Health check
echo ""
if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "Backend is healthy."
else
    echo "WARNING: Backend health check failed. Check logs:"
    echo "  docker compose -f $COMPOSE_FILE logs backend"
fi

if curl -sf http://localhost:80 > /dev/null 2>&1; then
    echo "Frontend is serving."
else
    echo "WARNING: Frontend check failed. Check logs:"
    echo "  docker compose -f $COMPOSE_FILE logs frontend"
fi

# Seed data if database is empty
echo ""
echo "Checking if database needs seeding..."
docker compose -f "$COMPOSE_FILE" exec backend python -c "
from backend.database import SessionLocal
from backend.models.program import Program
db = SessionLocal()
count = db.query(Program).count()
db.close()
print(f'Programs in database: {count}')
if count == 0:
    print('NEEDS_SEED')
" 2>/dev/null | grep -q "NEEDS_SEED" && {
    echo "Seeding database with initial data..."
    docker compose -f "$COMPOSE_FILE" exec backend python -m backend.scripts.seed_data
    echo "Database seeded."
} || echo "Database already has data."

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Services:"
echo "  Frontend: http://$(hostname -I | awk '{print $1}')"
echo "  Backend:  http://$(hostname -I | awk '{print $1}'):8000"
echo "  API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "Useful commands:"
echo "  Logs:     docker compose -f $COMPOSE_FILE logs -f"
echo "  Stop:     docker compose -f $COMPOSE_FILE down"
echo "  Restart:  docker compose -f $COMPOSE_FILE restart"
echo "  Rebuild:  docker compose -f $COMPOSE_FILE up -d --build"
echo ""
echo "Next steps:"
echo "  1. Set up a domain and point DNS to this server"
echo "  2. Set up SSL with: certbot --nginx (install certbot first)"
echo "  3. Update CORS_ORIGINS and FRONTEND_URL in .env.production"
echo "  4. Create an admin user via the API or promote via database"
