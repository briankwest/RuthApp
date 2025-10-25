#!/bin/bash

# Production Setup Script for Ruth Platform
# This script helps set up the production environment with Docker

set -e

echo "=========================================="
echo "Ruth Platform - Production Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
   echo -e "${YELLOW}Warning: Running as root is not recommended${NC}"
fi

# Function to generate secure random strings
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
}

# Function to create production .env file
create_env_file() {
    if [ -f "backend/.env.production" ]; then
        echo -e "${YELLOW}Production .env file already exists. Skipping...${NC}"
        return
    fi

    echo "Creating production environment file..."

    # Generate secrets
    SECRET_KEY=$(generate_secret)
    JWT_SECRET=$(generate_secret)
    DB_PASSWORD=$(generate_secret)
    REDIS_PASSWORD=$(generate_secret)
    GRAFANA_PASSWORD=$(generate_secret)

    cat > backend/.env.production << EOF
# Production Environment Configuration
# Generated on $(date)

# Application Settings
APP_NAME="Ruth - Civic Letter Platform"
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database
DATABASE_URL=postgresql://ruth_user:${DB_PASSWORD}@postgres:5432/ruth_db
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_PREFIX=ruth:prod:

# JWT Settings
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# External APIs (Add your production keys)
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4-turbo-preview

GEOCODIO_API_KEY=your-production-geocodio-key
GEOCODIO_VERSION=1.7

MAILGUN_API_KEY=your-production-mailgun-key
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_FROM_NAME="Ruth Platform"

SIGNALWIRE_PROJECT_ID=your-production-signalwire-project
SIGNALWIRE_TOKEN=your-production-signalwire-token
SIGNALWIRE_SPACE_URL=yourspace.signalwire.com
SIGNALWIRE_FAX_FROM=+1234567890

# File Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=10485760

# Celery Configuration
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2

# Security
BCRYPT_ROUNDS=14
RATE_LIMIT_PER_MINUTE=30

# Monitoring
SENTRY_DSN=your-sentry-dsn
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# Backup
BACKUP_S3_BUCKET=ruth-backups
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# Feature Flags
ENABLE_REGISTRATION=True
ENABLE_FAX_DELIVERY=True
ENABLE_EMAIL_DELIVERY=True
REQUIRE_EMAIL_VERIFICATION=True

# Cache TTL (in seconds)
GEOCODING_CACHE_TTL=2592000
REPRESENTATIVE_CACHE_TTL=604800
SESSION_CACHE_TTL=3600

# Generated Passwords (Save these securely!)
DB_PASSWORD=${DB_PASSWORD}
EOF

    echo -e "${GREEN}✓ Production environment file created${NC}"
    echo -e "${YELLOW}IMPORTANT: Save these generated passwords securely:${NC}"
    echo "  Database Password: ${DB_PASSWORD}"
    echo "  Redis Password: ${REDIS_PASSWORD}"
    echo "  Grafana Password: ${GRAFANA_PASSWORD}"
    echo ""
    echo -e "${YELLOW}Please edit backend/.env.production and add your API keys${NC}"
}

# Function to create Docker secrets
create_docker_secrets() {
    echo "Setting up Docker secrets..."

    # Check if running in swarm mode
    if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
        echo "Initializing Docker Swarm..."
        docker swarm init
    fi

    # Create secrets from .env.production
    if [ -f "backend/.env.production" ]; then
        # Extract passwords from .env file
        DB_PASSWORD=$(grep "^DB_PASSWORD=" backend/.env.production | cut -d'=' -f2)

        # Create Docker secret
        echo "$DB_PASSWORD" | docker secret create db_password - 2>/dev/null || \
            echo -e "${YELLOW}Secret 'db_password' already exists${NC}"
    fi

    echo -e "${GREEN}✓ Docker secrets configured${NC}"
}

# Function to set up SSL certificates
setup_ssl() {
    echo "Setting up SSL certificates..."

    mkdir -p ssl

    if [ ! -f "ssl/cert.pem" ]; then
        echo -e "${YELLOW}No SSL certificates found.${NC}"
        echo "Options:"
        echo "1. Use Let's Encrypt (recommended for production)"
        echo "2. Generate self-signed certificate (for testing only)"
        echo "3. Skip (add certificates manually later)"

        read -p "Choose option (1-3): " ssl_option

        case $ssl_option in
            1)
                echo "Please set up Let's Encrypt certificates using certbot"
                echo "Run: docker run -it --rm -v $PWD/ssl:/etc/letsencrypt certbot/certbot certonly"
                ;;
            2)
                echo "Generating self-signed certificate..."
                openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                    -keyout ssl/key.pem \
                    -out ssl/cert.pem \
                    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
                echo -e "${GREEN}✓ Self-signed certificate generated${NC}"
                ;;
            3)
                echo "Skipping SSL setup. Add certificates to ssl/ directory before starting."
                ;;
        esac
    else
        echo -e "${GREEN}✓ SSL certificates found${NC}"
    fi
}

# Function to create backup script
create_backup_script() {
    mkdir -p docker/scripts

    cat > docker/scripts/backup.sh << 'EOF'
#!/bin/sh
# Automated backup script for Ruth platform

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ruth_backup_${TIMESTAMP}.sql"

echo "Starting backup at $(date)"

# Backup PostgreSQL
PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
    -h $POSTGRES_HOST \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    > /backups/$BACKUP_FILE

# Compress backup
gzip /backups/$BACKUP_FILE

# Upload to S3 if configured
if [ ! -z "$S3_BUCKET" ]; then
    aws s3 cp /backups/${BACKUP_FILE}.gz s3://$S3_BUCKET/
    echo "Backup uploaded to S3"
fi

# Clean old local backups (keep last 7 days)
find /backups -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed at $(date)"
EOF

    chmod +x docker/scripts/backup.sh
    echo -e "${GREEN}✓ Backup script created${NC}"
}

# Function to create monitoring configuration
setup_monitoring() {
    echo "Setting up monitoring configuration..."

    # Create Prometheus configuration
    cat > docker/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
EOF

    echo -e "${GREEN}✓ Monitoring configuration created${NC}"
}

# Function to perform system checks
system_checks() {
    echo "Performing system checks..."

    # Check available disk space
    AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
    echo "  Available disk space: $AVAILABLE_SPACE"

    # Check available memory
    if command -v free &> /dev/null; then
        AVAILABLE_MEM=$(free -h | awk 'NR==2 {print $7}')
        echo "  Available memory: $AVAILABLE_MEM"
    fi

    # Check Docker daemon
    if docker info &> /dev/null; then
        echo -e "  Docker daemon: ${GREEN}Running${NC}"
    else
        echo -e "  Docker daemon: ${RED}Not running${NC}"
        exit 1
    fi

    # Check ports
    for port in 80 443 3000 8000 5432 6379; do
        if lsof -i :$port &> /dev/null; then
            echo -e "  Port $port: ${YELLOW}In use${NC}"
        else
            echo -e "  Port $port: ${GREEN}Available${NC}"
        fi
    done
}

# Function to start production environment
start_production() {
    echo "Starting production environment..."

    # Build images
    echo "Building Docker images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

    # Start services
    echo "Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

    # Wait for services to be healthy
    echo "Waiting for services to be healthy..."
    sleep 30

    # Run migrations
    echo "Running database migrations..."
    docker-compose exec backend alembic upgrade head

    echo -e "${GREEN}✓ Production environment started successfully!${NC}"
    echo ""
    echo "Access points:"
    echo "  - Main application: https://yourdomain.com"
    echo "  - Monitoring (Grafana): http://yourdomain.com:3001"
    echo "  - Metrics (Prometheus): http://yourdomain.com:9090"
    echo ""
    echo "Next steps:"
    echo "  1. Update DNS records to point to this server"
    echo "  2. Configure firewall rules"
    echo "  3. Set up regular backups"
    echo "  4. Configure monitoring alerts"
}

# Main execution
main() {
    echo ""
    check_docker
    echo ""

    echo "This script will set up the Ruth platform for production."
    echo "Make sure you have:"
    echo "  - Domain name configured"
    echo "  - API keys ready"
    echo "  - Backup destination configured"
    echo ""

    read -p "Continue with production setup? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Setup cancelled."
        exit 0
    fi

    echo ""
    create_env_file
    echo ""
    create_docker_secrets
    echo ""
    setup_ssl
    echo ""
    create_backup_script
    echo ""
    setup_monitoring
    echo ""
    system_checks
    echo ""

    read -p "Start production environment now? (y/n): " start_now
    if [ "$start_now" = "y" ]; then
        start_production
    else
        echo ""
        echo "To start production environment later, run:"
        echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
    fi

    echo ""
    echo -e "${GREEN}=========================================="
    echo "Production setup complete!"
    echo "==========================================${NC}"
}

# Run main function
main