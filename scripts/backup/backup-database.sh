#!/bin/bash
#
# eBIOS PostgreSQL Backup Script
#
# Automated database backup with retention policy, compression, and S3/cloud upload support.
# Can be run manually or via cron for scheduled backups.
#
# Usage:
#   ./backup-database.sh [OPTIONS]
#
# Options:
#   -d, --backup-dir DIR    Backup directory (default: ./backups)
#   -r, --retention DAYS    Retention period in days (default: 30)
#   -s, --s3-bucket BUCKET  S3 bucket for cloud backup (optional)
#   -c, --compress          Compress backup with gzip (default: true)
#   -v, --verbose           Verbose output
#   -h, --help              Show this help message
#
# Environment Variables (required):
#   POSTGRES_HOST           PostgreSQL host
#   POSTGRES_PORT           PostgreSQL port (default: 5432)
#   POSTGRES_DB             Database name
#   POSTGRES_USER           Database user
#   POSTGRES_PASSWORD       Database password
#
# Example:
#   # Load environment
#   source /path/to/.env
#
#   # Run backup
#   ./backup-database.sh --backup-dir /var/backups/ebios --retention 7
#
#   # With S3 upload
#   ./backup-database.sh --s3-bucket my-ebios-backups
#

set -euo pipefail

# Default configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESS=true
VERBOSE=false
S3_BUCKET=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -s|--s3-bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        -c|--compress)
            COMPRESS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            head -n 30 "$0" | tail -n +3 | sed 's/^# //'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${NC}[$(date +'%Y-%m-%d %H:%M:%S')] $*"
    fi
}

# Check required environment variables
check_env() {
    local missing=()

    for var in POSTGRES_HOST POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
        if [ -z "${!var:-}" ]; then
            missing+=("$var")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required environment variables: ${missing[*]}"
        log_error "Please set them in .env file or environment"
        exit 1
    fi
}

# Check required commands
check_commands() {
    local cmds=("pg_dump")

    if [ -n "$S3_BUCKET" ]; then
        cmds+=("aws")
    fi

    for cmd in "${cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Generate backup filename
get_backup_filename() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local filename="ebios_backup_${timestamp}.sql"

    if [ "$COMPRESS" = true ]; then
        filename="${filename}.gz"
    fi

    echo "$filename"
}

# Perform database backup
backup_database() {
    local filename=$1
    local filepath="${BACKUP_DIR}/${filename}"

    log "Starting backup: $filename"
    log_verbose "Database: ${POSTGRES_DB}"
    log_verbose "Host: ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}"

    # Set PostgreSQL password for pg_dump
    export PGPASSWORD="$POSTGRES_PASSWORD"

    # Build pg_dump command
    local pg_dump_cmd="pg_dump -h ${POSTGRES_HOST} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER} -d ${POSTGRES_DB}"
    pg_dump_cmd+=" --format=plain --no-owner --no-acl"
    pg_dump_cmd+=" --verbose"

    # Execute backup
    if [ "$COMPRESS" = true ]; then
        log_verbose "Compressing backup with gzip..."
        if $pg_dump_cmd | gzip > "$filepath" 2>&1; then
            log "✅ Backup created: $filepath"
        else
            log_error "Backup failed"
            rm -f "$filepath"
            exit 1
        fi
    else
        if $pg_dump_cmd > "$filepath" 2>&1; then
            log "✅ Backup created: $filepath"
        else
            log_error "Backup failed"
            rm -f "$filepath"
            exit 1
        fi
    fi

    # Unset password
    unset PGPASSWORD

    # Show backup size
    local size=$(du -h "$filepath" | cut -f1)
    log "Backup size: $size"

    echo "$filepath"
}

# Upload to S3
upload_to_s3() {
    local filepath=$1
    local filename=$(basename "$filepath")

    if [ -z "$S3_BUCKET" ]; then
        return 0
    fi

    log "Uploading to S3: s3://${S3_BUCKET}/${filename}"

    if aws s3 cp "$filepath" "s3://${S3_BUCKET}/${filename}" --storage-class STANDARD_IA; then
        log "✅ Uploaded to S3 successfully"
    else
        log_warn "S3 upload failed (backup still available locally)"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."

    local count=0
    while IFS= read -r -d '' file; do
        log_verbose "Deleting: $file"
        rm -f "$file"
        ((count++))
    done < <(find "$BACKUP_DIR" -name "ebios_backup_*.sql*" -type f -mtime +${RETENTION_DAYS} -print0)

    if [ $count -gt 0 ]; then
        log "Deleted $count old backup(s)"
    else
        log_verbose "No old backups to delete"
    fi
}

# Verify backup integrity
verify_backup() {
    local filepath=$1

    log "Verifying backup integrity..."

    if [ "$COMPRESS" = true ]; then
        if gzip -t "$filepath" 2>/dev/null; then
            log "✅ Backup integrity verified (gzip)"
        else
            log_error "Backup file is corrupted!"
            exit 1
        fi
    else
        if [ -s "$filepath" ]; then
            log "✅ Backup file is not empty"
        else
            log_error "Backup file is empty!"
            exit 1
        fi
    fi
}

# Main execution
main() {
    log "=== eBIOS Database Backup ==="

    check_env
    check_commands
    create_backup_dir

    local filename=$(get_backup_filename)
    local filepath=$(backup_database "$filename")

    verify_backup "$filepath"
    upload_to_s3 "$filepath"
    cleanup_old_backups

    log "=== Backup Complete ==="
    log "Backup location: $filepath"

    # Show all backups
    local backup_count=$(find "$BACKUP_DIR" -name "ebios_backup_*.sql*" -type f | wc -l)
    log "Total backups: $backup_count"
}

# Run main function
main "$@"
