#!/bin/bash
# eBIOS Database Backup Script
# Performs automated PostgreSQL backups with compression and retention

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ebios}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"  # Optional S3/Spaces bucket
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ebios_$TIMESTAMP.sql.gz"

# Database connection (from environment or defaults)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ebios}"
DB_USER="${DB_USER:-ebios}"
# DB_PASSWORD should be in environment or .pgpass

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "========================================="
echo "eBIOS Database Backup"
echo "========================================="
echo "Timestamp: $(date)"
echo "Database: $DB_NAME@$DB_HOST:$DB_PORT"
echo "Backup file: $BACKUP_FILE"
echo ""

# Perform backup
echo "Creating backup..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

# Check backup was created
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file was not created!"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3/Spaces if configured
if [ -n "$S3_BUCKET" ]; then
    echo "Uploading to S3/Spaces..."
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename $BACKUP_FILE)"
        echo "✅ Uploaded to S3: s3://$S3_BUCKET/backups/$(basename $BACKUP_FILE)"
    else
        echo "⚠️  AWS CLI not found, skipping S3 upload"
    fi
fi

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "ebios_*.sql.gz" -mtime +$RETENTION_DAYS -delete
REMAINING=$(find "$BACKUP_DIR" -name "ebios_*.sql.gz" | wc -l)
echo "✅ Cleanup complete. $REMAINING backups remaining."

echo ""
echo "========================================="
echo "Backup completed successfully"
echo "========================================="
