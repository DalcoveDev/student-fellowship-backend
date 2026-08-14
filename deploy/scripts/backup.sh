#!/bin/sh
set -eu

DEPLOY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BACKUP_DIR="${BACKUP_DIR:-$DEPLOY_DIR/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
COMPOSE="docker compose --env-file $DEPLOY_DIR/.env -f $DEPLOY_DIR/docker-compose.prod.yml"

mkdir -p "$BACKUP_DIR"

echo "Backing up PostgreSQL..."
$COMPOSE exec -T db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip > "$BACKUP_DIR/database-$TIMESTAMP.sql.gz"

echo "Backing up local media volume..."
$COMPOSE exec -T backend tar -C /app/media -czf - . \
  > "$BACKUP_DIR/media-$TIMESTAMP.tar.gz"

find "$BACKUP_DIR" -type f -mtime "+$RETENTION_DAYS" -delete

echo "Backup complete: $BACKUP_DIR"
