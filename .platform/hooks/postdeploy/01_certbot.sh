#!/bin/bash
set -euo pipefail

DOMAIN="url_app"
APP="Prueba DOCG"
S3_BUCKET="rgv"
S3_PREFIX="ssl/$APP/letsencrypt"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
EMAIL="tecnologias@rgvsoluciones.com"

echo "=== [$(date)] Starting Certbot setup for $DOMAIN ==="

# Ensure tools are installed
sudo dnf install -y certbot python3-certbot-nginx awscli

echo "Cleaning old accounts to avoid duplicate-account prompt..."
sudo rm -rf /etc/letsencrypt/accounts/

echo "Trying to download existing certs from s3://$S3_BUCKET/$S3_PREFIX/ ..."
aws s3 sync "s3://$S3_BUCKET/$S3_PREFIX/" /etc/letsencrypt/ || true

if [ -f "$CERT_PATH" ]; then
  echo "✅ Certificate for $DOMAIN found locally. Skipping certbot issuance."
else
  echo "⚠️ Certificate not found locally. Checking if S3 download missed it..."
  sleep 5
  aws s3 sync "s3://$S3_BUCKET/$S3_PREFIX/" /etc/letsencrypt/ || true

  if [ -f "$CERT_PATH" ]; then
    echo "✅ Certificate found after second sync attempt."
  else
    echo "🚀 Running certbot to generate new certificate..."
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

    echo "⬆️ Uploading newly created certs to S3..."
    aws s3 sync /etc/letsencrypt/ "s3://$S3_BUCKET/$S3_PREFIX/"
  fi
fi

echo "Restarting NGINX to apply certificates..."
sudo systemctl restart nginx || echo "⚠️ NGINX restart failed, please check manually."

echo "=== [$(date)] Certbot script completed successfully ==="
