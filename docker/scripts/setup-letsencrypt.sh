#!/bin/bash

# Ruth Platform - Let's Encrypt SSL Setup Script
# This script helps you obtain SSL certificates for ruthapp.us using Certbot

set -e

echo "========================================="
echo "Ruth Platform - Let's Encrypt Setup"
echo "========================================="
echo ""

# Configuration
DOMAIN="ruthapp.us"
WWW_DOMAIN="www.ruthapp.us"
EMAIL="${SSL_EMAIL:-admin@ruthapp.us}"
STAGING="${STAGING:-0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in project directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}Error: This script must be run from the ruth project root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Domain: $DOMAIN"
echo "  WWW Domain: $WWW_DOMAIN"
echo "  Email: $EMAIL"
echo "  Staging Mode: $STAGING (0=production, 1=staging)"
echo ""

# Ask for confirmation
read -p "Continue with these settings? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${GREEN}Step 1: Preparing environment...${NC}"

# Create necessary directories
mkdir -p docker/letsencrypt
mkdir -p uploads

echo -e "${GREEN}Step 2: Starting nginx in HTTP-only mode...${NC}"

# Start nginx without SSL first (it will redirect to HTTPS but allow ACME challenge)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
echo "Waiting for nginx to start..."
sleep 5

echo ""
echo -e "${GREEN}Step 3: Obtaining SSL certificate...${NC}"
echo "This may take a few minutes..."

# Build certbot command
CERTBOT_CMD="certbot certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d $WWW_DOMAIN"

# Add staging flag if requested
if [ "$STAGING" = "1" ]; then
    echo -e "${YELLOW}Using Let's Encrypt staging environment (test certificates)${NC}"
    CERTBOT_CMD="$CERTBOT_CMD --staging"
fi

# Run certbot
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot $CERTBOT_CMD

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ SSL certificate obtained successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to obtain SSL certificate${NC}"
    echo "Please check the error messages above."
    echo ""
    echo "Common issues:"
    echo "  1. Domain DNS not pointing to this server"
    echo "  2. Firewall blocking ports 80/443"
    echo "  3. Rate limiting (use STAGING=1 for testing)"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 4: Restarting nginx with SSL...${NC}"

# Restart nginx to load the new certificates
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx

echo ""
echo -e "${GREEN}========================================="
echo "✓ SSL Setup Complete!"
echo "=========================================${NC}"
echo ""
echo "Your site should now be available at:"
echo "  https://$DOMAIN"
echo "  https://$WWW_DOMAIN"
echo ""
echo "Certificates are stored in Docker volume: certbot-certs"
echo "Auto-renewal is configured to check twice daily"
echo ""
echo "To manually renew certificates:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew"
echo ""
echo "To check certificate expiration:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certificates"
echo ""
