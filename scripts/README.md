# Scripts

This folder contains utility scripts for the Real Estate Management API project.

## migrate_database.py

Script for database migration and initialization.

### Usage:

```bash
# Run migrations (interactive)
python scripts/migrate_database.py

# Force run migrations (without confirmation)
python scripts/migrate_database.py --force

# Check database status only
python scripts/migrate_database.py --check
```

### When to use:
- **First installation**: Run before starting the application for the first time
- **After model changes**: Run whenever you modify database models
- **Synchronization issues**: Run when database is out of sync

### What the script does:
1. Validates SQLAlchemy models
2. Applies necessary migrations
3. Creates/updates tables
4. Checks database connectivity

## Recommended execution order:

1. **Normal usage (automatic):**
   ```bash
   # Automatic migration in Docker Compose
   docker-compose up --build -d
   ```

2. **First installation (manual control):**
   ```bash
   # 1. Start the database with Docker
   docker-compose up -d postgres
   
   # 2. Run migrations manually
   python scripts/migrate_database.py
   
   # 3. Start the application
   docker-compose up -d api
   ```

## Important notes:

- ✅ **Automatic migration**: Docker Compose runs `migrate_database.py` automatically
- ✅ **No manual intervention**: `docker-compose up` handles everything
- ✅ **Scripts available**: For special cases and debugging
- ✅ **Order guaranteed**: API only starts after successful migration
- ⚠️ **Use `--build`**: To apply code changes after modifications

---

**Note**: Authentication-related scripts (like `create_admin.py`) have been removed as all authentication is now delegated to the `sexto-andar-auth` service.
