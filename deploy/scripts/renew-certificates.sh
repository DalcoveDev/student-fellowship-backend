#!/bin/sh
set -eu

DEPLOY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

certbot renew \
  --webroot \
  --webroot-path "$DEPLOY_DIR/certbot/www" \
  --quiet

docker compose \
  --env-file "$DEPLOY_DIR/.env" \
  -f "$DEPLOY_DIR/docker-compose.prod.yml" \
  exec -T nginx nginx -s reload
