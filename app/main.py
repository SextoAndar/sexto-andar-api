"""
FastAPI Application Main File
Real Estate Management API
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings

# Import database functions
from app.database.connection import (
    connect_db, 
    disconnect_db, 
    check_database_connection
)

# Import models (this ensures they are registered with SQLAlchemy)
# Account é gerenciado pelo serviço sexto-andar-auth no mesmo banco
from app.models import Property, Address, Visit, Proposal

# Import controllers/routers
# Auth endpoints são gerenciados pelo serviço sexto-andar-auth (externo)
# Admin endpoints were previously exposed here, but account management is
# delegated to the auth service. If you still want admin routes in this
# repo, consider implementing proxy endpoints that call the auth service.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting FastAPI application...")
    
    try:
        # Connect to database
        await connect_db()
        
        # Verify database connection
        if not await check_database_connection():
            logger.error("Database connection failed. Please run migration script first.")
            logger.error("Run: python scripts/migrate_database.py")
            sys.exit(1)
            
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        sys.exit(1)
        
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await disconnect_db()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Create FastAPI application with professional documentation
app = FastAPI(
    title="Real Estate Management API",
    description="""A professional FastAPI-based system for managing real estate properties, user accounts, visits, and proposals.

## Authentication
This API uses JWT tokens with HTTP-only cookies for secure authentication:
- Registration: Create USER or PROPERTY_OWNER accounts
- Login: Authenticate and receive JWT token in cookie
- Logout: Clear authentication cookie
- Role-based access control for different user types

## User Roles
- USER: Browse properties, schedule visits, make proposals
- PROPERTY_OWNER: Manage properties and view proposals  
- ADMIN: Full system access and user management

## Security Features
- JWT tokens with secure HTTP-only cookies
- Bcrypt password hashing
- Role-based access control
- CORS protection
- Input validation with Pydantic

## Core Features
- Account management and authentication
- Property listing CRUD operations
- Visit scheduling system
- Proposal management
- Admin user management panel

## Technical Stack
- Framework: FastAPI with async/await support
- Database: PostgreSQL with SQLAlchemy ORM
- Authentication: JWT with HTTP-only cookies
- Validation: Pydantic models
- Documentation: Auto-generated OpenAPI/Swagger

## Getting Started
1. Run database migrations: python scripts/migrate_database.py
2. Most endpoints require authentication
3. Register account using /api/v1/auth/register endpoints
4. Login using /api/v1/auth/login
5. Admin users must be created via command-line script

## API Versioning
- Current Version: v1
- Base URL: /api/v1
- All endpoints are versioned for backwards compatibility
""",
    version="1.0.0",
    terms_of_service="https://github.com/moonshinerd/sexto-andar-api",
    contact={
        "name": "API Support",
        "url": "https://github.com/moonshinerd/sexto-andar-api/issues",
        "email": "support@sextoandar.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/moonshinerd/sexto-andar-api/blob/main/LICENSE",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.sextoandar.com",
            "description": "Production server"
        }
    ],
    lifespan=lifespan
)

# CORS middleware (read from settings / .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/", tags=["health"], summary="Root Health Check")
async def root():
    """Root endpoint health check. Returns basic API information and status."""
    return {
        "message": "Real Estate Management API is running",
        "status": "healthy",
        "version": "1.0.0",
        "api": "Real Estate Management API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["health"], summary="Detailed Health Check")
async def health_check():
    """Comprehensive health check including database connectivity status."""
    try:
        # Check database connection
        db_healthy = await check_database_connection()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "api": "running",
            "timestamp": "2025-09-05T15:00:00Z",
            "checks": {
                "database": "connected" if db_healthy else "disconnected",
                "api": "running",
                "authentication": "available"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# API Routes will be added here
# Example structure:
# app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
# app.include_router(properties.router, prefix="/api/v1/properties", tags=["Properties"])
# app.include_router(visits.router, prefix="/api/v1/visits", tags=["Visits"])
# app.include_router(proposals.router, prefix="/api/v1/proposals", tags=["Proposals"])

# Include API Routes using settings (root_prefix is configurable via environment/.env)
# Auth endpoints são delegados para sexto-andar-auth (AUTH_SERVICE_URL obrigatório)
# NOTE: admin router registration removed because account management and
# user administration are handled by the external auth service.
# To re-enable admin routes from this repo (not recommended), import the
# admin router and include it here using:
# app.include_router(admin_router, prefix=settings.api_route(settings.ADMIN_ROUTE))

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
