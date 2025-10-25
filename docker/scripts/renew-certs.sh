#!/bin/sh
set -e

# Ruth Platform - Certificate Renewal Script
# This script runs periodically to renew certificates and reload nginx

DOMAIN="${DOMAIN:-ruthapp.us}"

echo "========================================="
echo "Certificate Renewal Check"
echo "$(date)"
echo "========================================="

# Check if certificates exist
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "⚠ No certificates found. Skipping renewal check."
    echo "   Certificates must be obtained manually first."
    exit 0
fi

# Check certificate expiry
EXPIRY_DATE=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

echo "Current Date: $(date)"
echo "Certificate Expires: $EXPIRY_DATE"
echo "Days Remaining: $DAYS_LEFT days"

# Renew if less than 30 days remaining
if [ $DAYS_LEFT -lt 30 ]; then
    echo ""
    echo "⚠ Certificate expires in less than 30 days. Renewing..."

    # Attempt renewal
    if certbot renew --webroot --webroot-path=/var/www/certbot --quiet; then
        echo "✓ Certificate renewed successfully!"

        # Reload nginx to use new certificate
        echo "  Reloading nginx..."
        if command -v docker >/dev/null 2>&1; then
            # If docker is available (running from host)
            docker exec ruth_nginx_prod nginx -s reload 2>/dev/null || \
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload 2>/dev/null || \
            echo "  Note: Unable to reload nginx automatically. Please restart nginx container."
        else
            # If running inside container, just print instruction
            echo "  Note: Restart nginx container to load new certificates:"
            echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx"
        fi

        echo ""
        echo "✓ Renewal complete!"
    else
        echo "✗ Certificate renewal failed. Check logs above."
        exit 1
    fi
else
    echo ""
    echo "✓ Certificate is valid for $DAYS_LEFT more days. No renewal needed."
fi

echo "========================================="
