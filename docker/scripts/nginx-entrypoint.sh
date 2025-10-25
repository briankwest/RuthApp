#!/bin/sh
set -e

# Ruth Platform - Nginx Entrypoint with SSL Certificate Management
# This script handles the initial certificate request and proper nginx startup

echo "========================================="
echo "Ruth Platform - Nginx Startup"
echo "========================================="

DOMAIN="${DOMAIN:-ruthapp.us}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@ruthapp.us}"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
NGINX_CONF_PROD="/etc/nginx/nginx.conf.prod"
NGINX_CONF_INIT="/etc/nginx/nginx.conf.init"
NGINX_CONF="/etc/nginx/nginx.conf"

# Check if certificates exist
if [ -f "$CERT_PATH/fullchain.pem" ] && [ -f "$CERT_PATH/privkey.pem" ]; then
    echo "✓ SSL certificates found"
    echo "  Certificate: $CERT_PATH/fullchain.pem"
    echo "  Private Key: $CERT_PATH/privkey.pem"

    # Check certificate expiry
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$CERT_PATH/fullchain.pem" | cut -d= -f2)
    echo "  Expires: $EXPIRY_DATE"

    echo ""
    echo "Using SSL-enabled nginx configuration..."

    # Use production SSL config
    if [ -f "$NGINX_CONF_PROD" ]; then
        rm -f "$NGINX_CONF"
        cp "$NGINX_CONF_PROD" "$NGINX_CONF"
    fi

    echo "Starting nginx with SSL..."
    exec nginx -g 'daemon off;'
else
    echo "⚠ SSL certificates not found"
    echo "  Looking for: $CERT_PATH/fullchain.pem"
    echo ""
    echo "Using HTTP-only nginx configuration for certificate generation..."

    # Use init config (HTTP only, no SSL)
    if [ -f "$NGINX_CONF_INIT" ]; then
        rm -f "$NGINX_CONF"
        cp "$NGINX_CONF_INIT" "$NGINX_CONF"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TO OBTAIN SSL CERTIFICATES, RUN:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "docker-compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certonly \\"
    echo "  --webroot -w /var/www/certbot \\"
    echo "  --email $CERTBOT_EMAIL \\"
    echo "  --agree-tos --no-eff-email \\"
    echo "  -d $DOMAIN -d www.$DOMAIN"
    echo ""
    echo "THEN RESTART NGINX:"
    echo "docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Start nginx with HTTP-only config
    exec nginx -g 'daemon off;'
fi
