"""
FastAPI Application Documentation Configuration
All API documentation strings and metadata are centralized here.
"""

# API Metadata
API_TITLE = "Real Estate Management API"
API_VERSION = "1.0.0"

# API Description (shown in /docs and /redoc)
API_DESCRIPTION = """Professional FastAPI-based system for managing real estate properties, visits, and proposals.

⚠️ **AUTHENTICATION DELEGATED**: This API delegates 100% of authentication to the external `sexto-andar-auth` service.
All account management, registration, and login are handled by that service.

## Authentication
This API validates JWT tokens by calling the external `sexto-andar-auth` service:
- All endpoints requiring auth send tokens to `AUTH_SERVICE_URL/api/v1/auth/introspect`
- User registration & login: Use `sexto-andar-auth` service endpoints
- Token validation: Automatic via dependency injection
- Role-based access control: Managed by `sexto-andar-auth`

## User Roles (managed by sexto-andar-auth)
- **USER**: Browse properties, schedule visits, make proposals
- **PROPERTY_OWNER**: Manage properties and view proposals  
- **ADMIN**: Full system access and user management

## Security Features
- JWT token validation via remote service
- Role-based access control
- CORS protection
- Input validation with Pydantic

## Core Features
- Property listing CRUD operations
- Visit scheduling system
- Proposal management

## Technical Stack
- Framework: FastAPI with async/await support
- Database: PostgreSQL with SQLAlchemy ORM
- Authentication: Remote JWT validation via `sexto-andar-auth`
- Validation: Pydantic models
- Documentation: Auto-generated OpenAPI/Swagger

## Getting Started
1. Start both services: `sexto-andar-auth` and this API
2. Set `AUTH_SERVICE_URL` environment variable pointing to auth service
3. All endpoints requiring auth will validate tokens with the auth service
4. Register accounts and login via `sexto-andar-auth` service

## Related Services
- **sexto-andar-auth**: https://github.com/SextoAndar/sexto-andar-auth
  - Handles: Account registration, login, JWT tokens, user management
  - Database: Shared PostgreSQL with this API

## Documentation
- Interactive API docs: /docs (Swagger UI)
- Alternative docs: /redoc (ReDoc)
- OpenAPI schema: /openapi.json
"""

# Server Configuration for API docs
API_SERVERS = [
    {
        "url": "http://localhost:8000",
        "description": "Development server"
    },
    {
        "url": "http://localhost:8000",
        "description": "Docker container"
    },
    {
        "url": "https://api.sextoandar.com",
        "description": "Production server"
    }
]

# API Tags for endpoint grouping
API_TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and service status endpoints",
    },
    {
        "name": "properties",
        "description": "Property management endpoints (CRUD operations)",
    },
    {
        "name": "visits",
        "description": "Visit scheduling and management endpoints",
    },
    {
        "name": "proposals",
        "description": "Property proposal management endpoints",
    },
]

# Contact and License info
API_CONTACT = {
    "name": "SextoAndar Team",
    "url": "https://github.com/SextoAndar/sexto-andar-api",
}

API_LICENSE_INFO = {
    "name": "MIT",
    "url": "https://github.com/SextoAndar/sexto-andar-api/blob/main/LICENSE",
}
