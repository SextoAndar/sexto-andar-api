# Real Estate Management API

A professional FastAPI for managing properties, visits, and proposals with **100% delegated authentication**.

> **Important**: This repository focuses on the real estate domain. All authentication, account management, and user administration is handled by the external [`sexto-andar-auth`](https://github.com/SextoAndar/sexto-andar-auth) service.

### Prerequisites
- Docker and Docker Compose
- Python 3.8+

### 1. Clone and setup environment

```bash
git clone git@github.com:SextoAndar/sexto-andar-api.git
cd sexto-andar-api

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows
```

### 2. Simple start (with automatic migration)

```bash
# Start everything at once - automatic migration included!
docker-compose up --build -d
```

Migration will run automatically before the API starts.

### 2.1. First installation (alternative manual)

If you prefer manual control over migrations:

```bash
# 1. Start database
docker-compose up -d postgres

# 2. Run migrations (manual)
python scripts/migrate_database.py

# 3. Start entire application
docker-compose up -d
```

### 3. Continuous development

For normal development, simply execute:
```bash
docker-compose up
```

## 📖 API Documentation

After starting the application, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🗄️ Database Management

### Automatic Migration

Docker Compose now executes migrations automatically:
- ✅ **Automatic**: `docker-compose up` runs migration before API
- ✅ **Safe**: Migration only executes if database is healthy
- ✅ **Clean**: Migration container stops after completion
- ✅ **Reliable**: API only starts after successful migration

### Migration Script

The `scripts/migrate_database.py` script is responsible for:
- Validating database models
- Applying necessary migrations
- Creating/updating tables
- Checking connectivity

#### Script commands:

```bash
# Run migrations (interactive)
python scripts/migrate_database.py

# Force run migrations
python scripts/migrate_database.py --force

# Check status only
python scripts/migrate_database.py --check
```

### When to run migrations manually:

- ✅ **Local development** - To debug migration issues
- ✅ **Specific problems** - If automatic migration fails
- ✅ **Verification** - To check status before deployment

## 🏗️ Architecture

### Technology Stack
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Validation**: Pydantic models
- **Containerization**: Docker Compose
- **Authentication**: Delegated to `sexto-andar-auth` service



## ️ Development

### Run in development mode

```bash
# With Docker
docker-compose up

# Or directly with Python (after migration)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### After model changes

```bash
# Simple: stop and restart (automatic migration)
docker-compose down
docker-compose up --build -d

# Or, for manual control:
docker-compose down
python scripts/migrate_database.py
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

```bash
# Authentication service (REQUIRED)
AUTH_SERVICE_URL=http://localhost:8001

# API configuration
API_BASE_PATH=/api
API_VERSION=v1

# CORS
ALLOW_ORIGINS=*

# Database (optional - uses default if not set)
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Debug
DEBUG=false
```

### pgAdmin Configuration

- **URL**: http://localhost:8080
- **Login Email**: admin@admin.com
- **Login Password**: admin

To connect to PostgreSQL in pgAdmin:
- **Host**: postgres
- **Port**: 5432
- **Database**: sexto_andar_db
- **Username**: sexto_andar_user
- **Password**: sexto_andar_pass

## 📊 Monitoring

### Health Checks
- `GET /` - Basic API status
- `GET /health` - Detailed status (API + database)

### Logs
Logs are configured to stdout and include:
- HTTP requests
- Application errors
- Migration status
- Database connectivity

## 🐳 Docker

### Available services:
- **migrate**: Runs migrations automatically (runs once then stops)
- **api**: FastAPI application (port 8000) - depends on migration
- **postgres**: PostgreSQL 15 (port 5432)
- **pgadmin**: PostgreSQL web interface (port 8080)

### Useful commands:

```bash
# Stop all services
docker-compose down

# View logs of a service
docker-compose logs api

# Rebuild images
docker-compose build

# Run only the database
docker-compose up -d postgres
```

## ⚠️ Important Notes

1. **Automatic migration**: `docker-compose up` handles migrations automatically
2. **Correct dependencies**: API only starts after successful migration
3. **Rebuilds**: Use `--build` after code changes to recreate containers
4. **Authentication**: All user authentication is handled by the `sexto-andar-auth` service

## 🤝 Contributing

1. Run migrations after checking out
2. Test your changes locally
3. Run migrations after model changes
4. Document new endpoints in OpenAPI documentation


**Note**: This repository focuses on real estate domain (Properties, Visits, Proposals). 
All authentication and account management is delegated to the `sexto-andar-auth` service.
