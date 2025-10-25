#!/bin/bash
set -e

# Ruth Platform - Complete SSL Setup Script
# This script handles the entire SSL certificate setup process

DOMAIN="${DOMAIN:-ruthapp.us}"
EMAIL="${CERTBOT_EMAIL:-admin@ruthapp.us}"
STAGING="${STAGING:-0}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================="
echo "Ruth Platform - SSL Setup"
echo "========================================="
echo ""
echo -e "${BLUE}Domain:${NC} $DOMAIN"
echo -e "${BLUE}Email:${NC} $EMAIL"
echo -e "${BLUE}Mode:${NC} $([ "$STAGING" = "1" ] && echo "STAGING (test)" || echo "PRODUCTION")"
echo ""

# Confirm
read -p "Continue with SSL setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1/5: Building nginx with SSL support...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build nginx

echo ""
echo -e "${GREEN}Step 2/5: Starting nginx (HTTP-only mode for certificate generation)...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
echo "Waiting for nginx to start..."
sleep 5

# Check nginx is running
if ! docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
    echo -e "${RED}Error: Nginx failed to start${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx
    exit 1
fi

echo -e "${GREEN}✓ Nginx started successfully in HTTP-only mode${NC}"

echo ""
echo -e "${GREEN}Step 3/5: Requesting SSL certificate from Let's Encrypt...${NC}"
echo "This may take a few minutes..."

# Build certbot command
CERTBOT_CMD="certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN"

# Add staging flag if requested
if [ "$STAGING" = "1" ]; then
    echo -e "${YELLOW}Using Let's Encrypt staging environment (test certificates)${NC}"
    CERTBOT_CMD="$CERTBOT_CMD --staging"
fi

# Request certificate
if docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot $CERTBOT_CMD; then
    echo ""
    echo -e "${GREEN}✓ SSL certificate obtained successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to obtain SSL certificate${NC}"
    echo ""
    echo "Common issues:"
    echo "  1. DNS not pointing to this server (check: dig $DOMAIN)"
    echo "  2. Ports 80/443 not accessible (firewall/port forwarding)"
    echo "  3. Rate limiting (use STAGING=1 for testing)"
    echo ""
    echo "Nginx logs:"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=20 nginx
    exit 1
fi

echo ""
echo -e "${GREEN}Step 4/5: Restarting nginx with SSL enabled...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx

# Wait for nginx to restart
sleep 3

# Verify nginx is running
if ! docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
    echo -e "${RED}Error: Nginx failed to restart with SSL${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx
    exit 1
fi

echo -e "${GREEN}✓ Nginx restarted with SSL enabled${NC}"

echo ""
echo -e "${GREEN}Step 5/5: Starting certificate auto-renewal service...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d certbot

echo ""
echo -e "${GREEN}========================================="
echo "✓ SSL Setup Complete!"
echo "=========================================${NC}"
echo ""
echo "Your site is now secured with HTTPS:"
echo -e "  ${BLUE}https://$DOMAIN${NC}"
echo -e "  ${BLUE}https://www.$DOMAIN${NC}"
echo ""
echo "Certificate details:"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certificates 2>/dev/null | grep -A 5 "Certificate Name: $DOMAIN" || echo "  (Run 'docker-compose run --rm certbot certificates' to view details)"
echo ""
echo "Auto-renewal:"
echo "  ✓ Certbot checks for renewal every 12 hours"
echo "  ✓ Certificates renew automatically 30 days before expiry"
echo "  ✓ No manual intervention required"
echo ""
echo "Verify your setup:"
echo "  curl -I https://$DOMAIN"
echo "  curl -I http://$DOMAIN  # Should redirect to HTTPS"
echo ""
echo -e "${GREEN}Setup complete! Your site is production-ready.${NC}"
echo ""
