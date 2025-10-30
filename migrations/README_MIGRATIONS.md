# eBIOS Database Migrations

This directory contains Alembic database migrations for eBIOS.

## Setup

Migrations are configured to read database credentials from environment variables:
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_SSLMODE`

Make sure these are set in your `.env` file or environment before running migrations.

## Common Commands

### Apply All Pending Migrations
```bash
# Source your environment first
source .env

# Run all pending migrations
alembic upgrade head
```

### Rollback Last Migration
```bash
alembic downgrade -1
```

### Rollback All Migrations
```bash
alembic downgrade base
```

### Show Current Migration Status
```bash
alembic current
```

### Show Migration History
```bash
alembic history
```

### Create New Migration
```bash
# Create empty migration
alembic revision -m "description_of_change"

# Auto-generate migration from model changes (requires SQLAlchemy models)
alembic revision --autogenerate -m "description_of_change"
```

## Migration Files

Migrations are stored in `migrations/versions/` and are applied in chronological order.

Current migrations:
1. `5e1db40d8352` - Create users table (v1.2.0)

## Production Workflow

1. **Development**: Create and test migrations locally
   ```bash
   source .env
   alembic upgrade head
   # Test your changes
   alembic downgrade -1  # Rollback if needed
   ```

2. **Staging**: Test migrations on staging environment
   ```bash
   export POSTGRES_HOST=staging-db.example.com
   export POSTGRES_DB=ebios_staging
   # ... other vars
   alembic upgrade head
   ```

3. **Production**: Apply migrations with backup
   ```bash
   # 1. Backup database first!
   pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB > backup_$(date +%Y%m%d_%H%M%S).sql

   # 2. Apply migrations
   alembic upgrade head

   # 3. Verify application works

   # 4. If problems, rollback
   # alembic downgrade -1
   ```

## Best Practices

1. **Always backup before migrating production**
2. **Test migrations on staging first**
3. **Keep migrations small and focused**
4. **Never modify existing migrations** - create new ones instead
5. **Always provide downgrade logic** - make migrations reversible
6. **Test both upgrade and downgrade paths**

## Troubleshooting

### "Can't locate revision"
The database's migration version doesn't match the available migration files.
```bash
# Check current version
alembic current

# Check available versions
alembic history

# If needed, manually stamp database to correct version
alembic stamp <revision_id>
```

### "Multiple head revisions"
Multiple migration branches exist. Merge them:
```bash
alembic merge -m "merge branches" <rev1> <rev2>
```

### Connection Errors
Ensure environment variables are set correctly:
```bash
echo $POSTGRES_HOST
echo $POSTGRES_DB
# ... check all vars
```

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [eBIOS Database Schema](../docs/database_schema.md)
