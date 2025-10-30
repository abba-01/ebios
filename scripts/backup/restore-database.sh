#!/bin/bash
#
# eBIOS PostgreSQL Restore Script
#
# Restore database from backup file.
#
# Usage:
#   ./restore-database.sh BACKUP_FILE [OPTIONS]
#
# Options:
#   -f, --force             Skip confirmation prompt
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
#   # Restore from backup
#   ./restore-database.sh ./backups/ebios_backup_20251029_120000.sql.gz
#
# WARNING: This will REPLACE the current database content!
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FORCE=false
VERBOSE=false
BACKUP_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            head -n 25 "$0" | tail -n +3 | sed 's/^# //'
            exit 0
            ;;
        *)
            if [ -z "$BACKUP_FILE" ]; then
                BACKUP_FILE="$1"
            else
                echo "Unknown option: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"
}

# Validate inputs
if [ -z "$BACKUP_FILE" ]; then
    log_error "No backup file specified"
    echo "Usage: $0 BACKUP_FILE"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check environment
for var in POSTGRES_HOST POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        log_error "Missing environment variable: $var"
        exit 1
    fi
done

# Check commands
if ! command -v psql &> /dev/null; then
    log_error "psql command not found"
    exit 1
fi

# Confirmation prompt
if [ "$FORCE" != true ]; then
    log_warn "WARNING: This will REPLACE all data in database '${POSTGRES_DB}'"
    log_warn "Database: ${POSTGRES_DB}@${POSTGRES_HOST}"
    log_warn "Backup file: $BACKUP_FILE"
    echo -n "Are you sure you want to continue? (yes/no): "
    read -r response

    if [ "$response" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
fi

# Perform restore
log "=== eBIOS Database Restore ==="
log "Backup file: $BACKUP_FILE"
log "Target database: ${POSTGRES_DB}@${POSTGRES_HOST}"

export PGPASSWORD="$POSTGRES_PASSWORD"

# Drop existing connections
log "Terminating existing connections..."
psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();
EOF

# Drop and recreate database
log "Recreating database..."
psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d postgres <<EOF
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB};
EOF

# Restore from backup
log "Restoring data..."

if [[ "$BACKUP_FILE" == *.gz ]]; then
    log "Decompressing and restoring..."
    gunzip -c "$BACKUP_FILE" | psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB"
else
    psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$BACKUP_FILE"
fi

unset PGPASSWORD

log "✅ Restore complete!"
log "=== Restore Complete ==="

# Show database size
export PGPASSWORD="$POSTGRES_PASSWORD"
DB_SIZE=$(psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'))" | tr -d ' ')
unset PGPASSWORD

log "Database size: $DB_SIZE"
