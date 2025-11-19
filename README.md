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
docker-compose up -d
```

**What happens:**
1. 📦 Docker checks if postgres exists (uses existing from sexto-andar-auth or creates new)
2. 🔄 Migration service runs and creates/updates properties-api tables
3. 🚀 API service starts after migrations complete successfully
4. ✅ API ready at http://localhost:8000

**Note**: The `sexto-andar-api` migrations **do not affect** the `sexto-andar-auth` tables and vice-versa.

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
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

### Main Endpoints

#### Properties
- `POST /api/properties/houses` - Create house property (requires 1-15 images)
- `POST /api/properties/apartments` - Create apartment property (requires 1-15 images)
- `GET /api/properties/` - List all properties (paginated, with filters)
- `GET /api/properties/{id}` - Get property details (includes image metadata)
- `PATCH /api/properties/{id}` - Update property
- `DELETE /api/properties/{id}` - Delete property
- `GET /api/properties/owner/portfolio` - Owner's property portfolio with stats

#### Property Images
- `GET /api/properties/{property_id}/images` - List all images metadata for a property
- `GET /api/images/{image_id}` - **Download image binary** (JPEG/PNG/WebP)
- `GET /api/images/{image_id}/metadata` - Get image metadata only
- `POST /api/properties/{property_id}/images` - Add image to property (max 15)
- `DELETE /api/images/{image_id}` - Remove image from property
- `PATCH /api/images/{image_id}/set-primary` - Set image as primary/main
- `PUT /api/properties/{property_id}/images/reorder` - Reorder property images

#### Visits
- `POST /api/visits/` - Schedule property visit
- `GET /api/visits/` - List user's scheduled visits
- `GET /api/visits/{id}` - Get visit details
- `PATCH /api/visits/{id}/cancel` - Cancel visit
- `GET /api/visits/owner/properties` - Property owner's visit management

#### Proposals
- `POST /api/proposals/` - Create property proposal
- `GET /api/proposals/` - List user's proposals
- `GET /api/proposals/{id}` - Get proposal details
- `PATCH /api/proposals/{id}/status` - Update proposal status (owner only)
- `GET /api/proposals/owner/properties` - Property owner's proposal management

#### Favorites
- `POST /api/favorites/` - Add property to favorites
- `GET /api/favorites/` - List user's favorite properties
- `DELETE /api/favorites/{property_id}` - Remove from favorites

#### Admin (Admin role only)
- `GET /api/admin/properties` - List all properties (admin view)
- `PATCH /api/admin/properties/{id}/activate` - Activate property
- `PATCH /api/admin/properties/{id}/deactivate` - Deactivate property

### Image Handling

Properties **require 1-15 images** when created. Images are stored as BYTEA in PostgreSQL and served via REST API:

**Frontend Usage:**
```html
<!-- Property card with images -->
<img src="http://localhost:8000/api/images/{image_id}" alt="Property" />
```

**React Example:**
```jsx
function PropertyCard({ property }) {
  const primaryImage = property.images.find(img => img.is_primary);
  
  return (
    <div>
      <img src={`${API_URL}/images/${primaryImage.id}`} />
      <div className="thumbnails">
        {property.images.map(img => (
          <img key={img.id} src={`${API_URL}/images/${img.id}`} />
        ))}
      </div>
    </div>
  );
}
```

**Image Requirements:**
- Formats: JPEG, PNG, WebP
- Max size: 5MB per image
- Encoding: Base64 for upload
- Storage: Binary (BYTEA) in PostgreSQL
- Delivery: Binary via REST API with proper Content-Type headers

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

### Microservices Architecture

This project is part of a microservices architecture:

**Services:**
- **sexto-andar-auth** - Manages authentication and user accounts
- **sexto-andar-api** - Manages properties, visits, proposals, and property images (this project)

**Key Features:**
- 📸 **Image Management** - Properties require 1-15 images stored as BYTEA in PostgreSQL
- 🔐 **Delegated Authentication** - All auth handled by sexto-andar-auth service
- 🏠 **Property Management** - Houses and apartments with full CRUD operations
- 📅 **Visit Scheduling** - Users can schedule property visits
- 💰 **Proposal System** - Create and manage property proposals
- ⭐ **Favorites** - Users can favorite properties for quick access

**Shared Resources:**
- 🗄️ **PostgreSQL Database** - Shared database, segregated tables
- 🌐 **Docker Network** - Communication between services
- 💾 **Docker Volume** - Data persistence

### Database Table Segregation

Each service manages its own tables independently:

| Service | Managed Tables | Migration Script |
|---------|----------------|------------------|
| **sexto-andar-auth** | `accounts` | `sexto-andar-auth/scripts/migrate_database.py` |
| **sexto-andar-api** | `properties`, `addresses`, `visits`, `proposals`, `favorites`, `property_images` | `sexto-andar-api/scripts/migrate_database.py` |

**Benefits of this architecture:**
- ✅ Independent migrations - each service updates only its tables
- ✅ Independent deployment - services can start in any order
- ✅ Zero conflicts - completely segregated tables
- ✅ Scalability - each service can scale independently

### Technology Stack
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Validation**: Pydantic models
- **Containerization**: Docker Compose
- **Authentication**: Delegated to `sexto-andar-auth` service

## 🧪 Tests

The project has a comprehensive test suite with **147 tests** covering all layers:
- **Unit Tests**: 58 tests (validations, no database)
- **Integration Tests**: 20 tests (complete workflows with database)
- **Parametrized Tests**: 74 test variations

```bash
# Run all tests locally
pytest

# Run specific types
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests only

# With coverage report
pytest --cov=app --cov-report=html
```

**Status**: ✅ 147/147 tests passing (100%)

**Note**: The `test` service is defined in `docker-compose.yml` but is **disabled by default** in the compose pipeline.
If you want to run tests via Docker use the dedicated profile or run tests locally.

Run tests in Docker (optional):
```bash
docker-compose --profile test up
```
Or run tests locally:
```bash
pytest
```

For detailed test documentation, see [`tests/README.md`](tests/README.md).

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

### Deployment Scenarios

**Scenario 1: Auth service already running** (Recommended)
```bash
# sexto-andar-auth is already up, just start the API
cd sexto-andar-api
docker-compose up -d
```
- Uses postgres, network and volume from auth service
- Runs migrations only for properties-api tables
- API starts after migrations complete

**Scenario 2: Standalone API** (For isolated development)
```bash
# Start everything including own postgres
cd sexto-andar-api
docker-compose --profile full-stack up -d
```
- Creates local postgres, network and volume
- Useful for development without depending on auth service
- Auth service can use these resources when it starts later

### Available services:
- **migrate**: Runs migrations automatically (runs once then stops)
  - Creates/updates tables: `properties`, `addresses`, `visits`, `proposals`, `favorites`, `property_images`
  - **Does NOT touch** the `accounts` table (managed by auth service)
- **api**: FastAPI application (port 8000) - depends on migration
- **postgres**: PostgreSQL 15 (port 5432) - shared with auth service
- **pgadmin**: PostgreSQL web interface (port 8080)

### Service Dependencies:

```
postgres (healthy) 
    ↓
migrate (completes successfully)
    ↓
api (starts and runs)
```

### Useful commands:

```bash
# Stop all services
docker-compose down

# View logs of a service
docker-compose logs api
docker-compose logs migrate

# Rebuild images after code changes
docker-compose build

# Restart with fresh migrations
docker-compose down
docker-compose up -d
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


**Note**: This repository focuses on real estate domain (Properties, Visits, Proposals, Images). 
All authentication and account management is delegated to the `sexto-andar-auth` service.

## 📸 Image Management

### Overview
Properties require **1-15 images** for creation. Images are stored as binary data (BYTEA) in PostgreSQL and served via REST API endpoints.

### How it works

**1. Creating a property with images:**
```bash
POST /api/properties/houses
{
  "address": {...},
  "propertySize": 250.5,
  "description": "Beautiful house...",
  "propertyValue": 450000,
  "salesType": "sale",
  "landPrice": 200000,
  "isSingleHouse": true,
  "images": [
    {
      "image_data": "base64_encoded_jpeg_data_here...",
      "content_type": "image/jpeg",
      "display_order": 1,
      "is_primary": true
    }
  ]
}
```

**2. Frontend retrieves property metadata:**
```bash
GET /api/properties/{property_id}
```

Response includes image metadata:
```json
{
  "id": "344a1d4a-1889-46e5-8a53-e62135983dc7",
  "description": "Beautiful house...",
  "images": [
    {
      "id": "08e41fa5-4bc6-4789-8a06-9ab0d440eb93",
      "property_id": "344a1d4a-1889-46e5-8a53-e62135983dc7",
      "content_type": "image/jpeg",
      "file_size": 52431,
      "display_order": 1,
      "is_primary": true,
      "created_at": "2025-11-19T02:38:53.729318+00:00"
    }
  ]
}
```

**3. Frontend displays images using URLs:**
```jsx
// React/Next.js example
function PropertyGallery({ property }) {
  const primaryImage = property.images.find(img => img.is_primary);
  const sortedImages = property.images.sort((a, b) => a.display_order - b.display_order);
  
  return (
    <div>
      {/* Main image */}
      <img 
        src={`${API_URL}/images/${primaryImage.id}`}
        alt={property.description}
        className="w-full h-96 object-cover"
      />
      
      {/* Thumbnail gallery */}
      <div className="grid grid-cols-4 gap-2">
        {sortedImages.map(img => (
          <img 
            key={img.id}
            src={`${API_URL}/images/${img.id}`}
            className="w-full h-24 object-cover cursor-pointer"
          />
        ))}
      </div>
    </div>
  );
}
```

**4. Browser automatically downloads images:**
```
Browser sees: <img src="/api/images/08e41fa5..." />
Browser makes: GET /api/images/08e41fa5-4bc6-4789-8a06-9ab0d440eb93
API responds: Binary JPEG data with Content-Type: image/jpeg
Browser displays: Rendered image
```

### Image Specifications

- **Formats**: JPEG, PNG, WebP
- **Max size**: 5MB per image
- **Quantity**: 1-15 images per property (required)
- **Upload**: Base64 encoded in JSON
- **Storage**: BYTEA (binary) in PostgreSQL
- **Download**: Binary data via REST API
- **Primary image**: One image marked as main/primary per property

### Security

✅ **Frontend NEVER accesses database directly**  
✅ **All image access goes through API authentication**  
✅ **Rate limiting and validation at API layer**  
✅ **Proper Content-Type headers for security**

**Note**: This repository focuses on real estate domain (Properties, Visits, Proposals, Images). 
All authentication and account management is delegated to the `sexto-andar-auth` service.
