# User Stories Implementation

## US14 - Register House Property ✅

**Como proprietário, quero cadastrar casas informando: endereço, tamanho, descrição, valor, tipo de venda (aluguel/venda), preço do terreno e se é casa única no terreno.**

### Endpoint
```
POST /api/properties/houses
```

### Authentication Required
- **Role**: PROPERTY_OWNER
- **Cookie**: access_token (JWT from sexto-andar-auth)

### Request Body
```json
{
  "address": {
    "street": "Rua das Flores",
    "number": "123",
    "city": "São Paulo",
    "postal_code": "01234567",
    "country": "Brazil"
  },
  "propertySize": 250.50,
  "description": "Beautiful house with garden and pool in quiet neighborhood",
  "propertyValue": 850000.00,
  "salesType": "sale",
  "landPrice": 300000.00,
  "isSingleHouse": true
}
```

### Response (201 Created)
```json
{
  "id": "uuid-here",
  "idPropertyOwner": "owner-uuid",
  "address": {
    "id": "address-uuid",
    "street": "Rua das Flores",
    "number": "123",
    "city": "São Paulo",
    "postal_code": "01234567",
    "country": "Brazil"
  },
  "propertySize": 250.50,
  "description": "Beautiful house with garden and pool in quiet neighborhood",
  "propertyValue": 850000.00,
  "publishDate": "2025-10-29T19:00:00Z",
  "condominiumFee": 0.00,
  "commonArea": false,
  "floor": null,
  "isPetAllowed": false,
  "landPrice": 300000.00,
  "isSingleHouse": true,
  "salesType": "sale",
  "propertyType": "house",
  "is_active": true,
  "created_at": "2025-10-29T19:00:00Z",
  "updated_at": "2025-10-29T19:00:00Z"
}
```

### Validations
- ✅ Address fields required (street, number, city, postal_code)
- ✅ Property size must be greater than 0
- ✅ Description minimum 10 characters, maximum 1000
- ✅ Property value must be greater than 0
- ✅ Sales type must be 'rent' or 'sale'
- ✅ Land price must be greater than 0
- ✅ Only PROPERTY_OWNER role can create houses

---

## US15 - Register Apartment Property ✅

**Como proprietário, quero cadastrar apartamentos informando: endereço, tamanho, descrição, valor, tipo de venda, preço do condomínio, área de convivência, andar e se permite pets.**

### Endpoint
```
POST /api/properties/apartments
```

### Authentication Required
- **Role**: PROPERTY_OWNER
- **Cookie**: access_token (JWT from sexto-andar-auth)

### Request Body
```json
{
  "address": {
    "street": "Avenida Paulista",
    "number": "1000",
    "city": "São Paulo",
    "postal_code": "01310100",
    "country": "Brazil"
  },
  "propertySize": 85.00,
  "description": "Modern apartment with stunning city view, 2 bedrooms and 2 bathrooms",
  "propertyValue": 650000.00,
  "salesType": "sale",
  "condominiumFee": 800.00,
  "commonArea": true,
  "floor": 15,
  "isPetAllowed": true
}
```

### Response (201 Created)
```json
{
  "id": "uuid-here",
  "idPropertyOwner": "owner-uuid",
  "address": {
    "id": "address-uuid",
    "street": "Avenida Paulista",
    "number": "1000",
    "city": "São Paulo",
    "postal_code": "01310100",
    "country": "Brazil"
  },
  "propertySize": 85.00,
  "description": "Modern apartment with stunning city view, 2 bedrooms and 2 bathrooms",
  "propertyValue": 650000.00,
  "publishDate": "2025-10-29T19:00:00Z",
  "condominiumFee": 800.00,
  "commonArea": true,
  "floor": 15,
  "isPetAllowed": true,
  "landPrice": null,
  "isSingleHouse": null,
  "salesType": "sale",
  "propertyType": "apartment",
  "is_active": true,
  "created_at": "2025-10-29T19:00:00Z",
  "updated_at": "2025-10-29T19:00:00Z"
}
```

### Validations
- ✅ Address fields required (street, number, city, postal_code)
- ✅ Property size must be greater than 0
- ✅ Description minimum 10 characters, maximum 1000
- ✅ Property value must be greater than 0
- ✅ Sales type must be 'rent' or 'sale'
- ✅ Condominium fee must be >= 0
- ✅ Floor must be between -10 and 200
- ✅ Only PROPERTY_OWNER role can create apartments

---

## Additional Endpoints

### List All Properties
```
GET /api/properties?page=1&size=10&property_type=house&sales_type=rent
```
- **Public** - No authentication required
- Filters: property_type, sales_type, active_only
- Pagination: page, size

### Get Property by ID
```
GET /api/properties/{property_id}
```
- **Public** - No authentication required

### Get My Properties (Owner)
```
GET /api/properties/owner/my-properties?page=1&size=10
```
- **Authentication**: PROPERTY_OWNER role required
- Returns all properties owned by authenticated user

### Update Property
```
PUT /api/properties/{property_id}
```
- **Authentication**: PROPERTY_OWNER role required
- Must be the property owner
- Partial update supported (only send fields to update)

### Delete Property
```
DELETE /api/properties/{property_id}
```
- **Authentication**: PROPERTY_OWNER role required
- Must be the property owner
- Soft delete (deactivates property)

### Activate Property
```
POST /api/properties/{property_id}/activate
```
- **Authentication**: PROPERTY_OWNER role required
- Must be the property owner
- Reactivates a deactivated property

---

## Architecture

### MVC Pattern Structure

```
app/
├── controllers/
│   └── property_controller.py  # FastAPI routes/endpoints
├── services/
│   └── property_service.py     # Business logic
├── repositories/
│   └── property_repository.py  # Database access layer
├── dtos/
│   └── property_dto.py         # Request/Response models
├── models/
│   ├── property.py             # Property entity
│   └── address.py              # Address entity
└── auth/
    ├── auth_client.py          # Auth service integration
    └── dependencies.py         # Authentication dependencies
```

### Authentication Flow

1. User logs in via `sexto-andar-auth` service
2. Receives JWT token in HTTP-only cookie
3. Sends requests to `sexto-andar-api` with cookie
4. `sexto-andar-api` validates token via `/api/auth/introspect` endpoint
5. Extracts user ID and role from token claims
6. Applies role-based access control

### Database Schema Changes

**New columns added to `properties` table:**

```sql
-- House-specific fields
landPrice NUMERIC(10, 2) NULL,
isSingleHouse BOOLEAN NULL,
```

These fields are:
- Required for houses (`propertyType='house'`)
- NULL for apartments (`propertyType='apartment'`)

---

## Testing

### Prerequisites
1. Start `sexto-andar-auth` service on port 8001
2. Start `sexto-andar-api` service on port 8000
3. Register a PROPERTY_OWNER account via auth service
4. Login to get JWT token

### Test US14 (House)
```bash
# 1. Login as property owner (get cookie)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"owner1","password":"password123"}' \
  -c cookies.txt

# 2. Create house
curl -X POST http://localhost:8000/api/properties/houses \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "address": {
      "street": "Rua das Flores",
      "number": "123",
      "city": "São Paulo",
      "postal_code": "01234567",
      "country": "Brazil"
    },
    "propertySize": 250.50,
    "description": "Beautiful house with garden and pool",
    "propertyValue": 850000.00,
    "salesType": "sale",
    "landPrice": 300000.00,
    "isSingleHouse": true
  }'
```

### Test US15 (Apartment)
```bash
# 1. Login as property owner (get cookie)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"owner1","password":"password123"}' \
  -c cookies.txt

# 2. Create apartment
curl -X POST http://localhost:8000/api/properties/apartments \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "address": {
      "street": "Avenida Paulista",
      "number": "1000",
      "city": "São Paulo",
      "postal_code": "01310100",
      "country": "Brazil"
    },
    "propertySize": 85.00,
    "description": "Modern apartment with city view",
    "propertyValue": 650000.00,
    "salesType": "sale",
    "condominiumFee": 800.00,
    "commonArea": true,
    "floor": 15,
    "isPetAllowed": true
  }'
```

---

## API Documentation

After starting the service, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

All endpoints, request/response schemas, and authentication requirements are documented there.
