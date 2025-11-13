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

## seed_data.py

Data seeding script that populates both the auth service and the properties API with fictional test data.

### Features:
- Creates users with different roles (USER and PROPERTY_OWNER) in the auth service
- Creates fictional properties (houses and apartments)
- Schedules property visits
- Creates property proposals
- Automatically handles authentication and authorization
- Works both locally and inside Docker containers
- Colored output for easy tracking
- Complete error handling and status reporting

### Usage:

**Run locally (default ports):**
```bash
python scripts/seed_data.py
```

**Run locally with custom URLs:**
```bash
AUTH_SERVICE_URL=http://localhost:8001 API_BASE_URL=http://localhost:8000/api python scripts/seed_data.py
```

**Run inside Docker:**
```bash
docker-compose exec api python scripts/seed_data.py
```

**Make it executable and run directly:**
```bash
chmod +x scripts/seed_data.py
./scripts/seed_data.py
```

### Test Credentials Created:

**Property Owners:**
- john.doe@email.com / senha123
- maria.silva@email.com / senha123
- carlos.santos@email.com / senha123

**Regular Users:**
- alice.johnson@email.com / senha123
- bob.smith@email.com / senha123
- carol.white@email.com / senha123
- david.brown@email.com / senha123

### What the script does:
1. Creates 7 users in the auth service (3 property owners + 4 regular users)
2. Logs in each user to get JWT tokens
3. Creates 5 properties (2 houses + 3 apartments)
4. Schedules 1-3 visits per property from different users
5. Creates 1-2 proposals per property with varying values
6. Provides detailed summary of created data

### When to use:
- **After initial setup**: To quickly populate the database with test data
- **Development testing**: To test all endpoints with realistic data
- **Demo purposes**: To showcase the application with sample data
- **After database reset**: To quickly restore test data

---

**Note**: Authentication-related scripts (like `create_admin.py`) have been removed as all authentication is now delegated to the `sexto-andar-auth` service.
