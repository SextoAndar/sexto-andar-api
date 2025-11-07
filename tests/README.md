# Tests - Sexto Andar API

Test suite for the Sexto Andar Properties API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── pytest.ini                     # Pytest configuration
├── controllers/                   # Controller/endpoint tests
│   ├── test_property_endpoints.py
│   └── test_health.py
├── services/                      # Service layer tests
│   └── test_property_service.py
├── repositories/                  # Repository layer tests
│   └── test_property_repository.py
├── models/                        # Model tests
│   └── test_property_models.py
└── unit/                          # Unit tests
    └── test_settings.py
```

## Prerequisites

1. **PostgreSQL Test Database**: Create a test database
   ```bash
   psql -U sexto_andar_user
   CREATE DATABASE sexto_andar_test_db;
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Controller tests
pytest tests/controllers/

# Service tests
pytest tests/services/

# Repository tests
pytest tests/repositories/

# Model tests
pytest tests/models/

# Unit tests
pytest tests/unit/
```

### Run Specific Test File
```bash
pytest tests/controllers/test_property_endpoints.py
```

### Run Specific Test Class or Method
```bash
# Specific class
pytest tests/controllers/test_property_endpoints.py::TestPropertyCreation

# Specific test
pytest tests/controllers/test_property_endpoints.py::TestPropertyCreation::test_create_house_success
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run with Verbose Output
```bash
pytest -v
```

### Run with Output (print statements)
```bash
pytest -s
```

## Test Categories (Markers)

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Controller tests
pytest -m controllers

# Service tests
pytest -m services

# Repository tests
pytest -m repositories

# Model tests
pytest -m models
```

## Test Fixtures

Common fixtures available in `conftest.py`:

- `db_session`: Fresh database session for each test
- `client`: FastAPI test client
- `mock_auth_user`: Mock authenticated user
- `mock_auth_property_owner`: Mock authenticated property owner
- `mock_auth_admin`: Mock authenticated admin
- `authenticated_property_owner`: Client with property owner authentication
- `authenticated_user`: Client with user authentication
- `authenticated_admin`: Client with admin authentication
- `test_house_data`: Sample house data
- `test_apartment_data`: Sample apartment data
- `test_address_data`: Sample address data
- `created_property`: Property already created in database

## Writing New Tests

### Example: Controller Test
```python
def test_my_endpoint(authenticated_property_owner, test_house_data):
    """Test description"""
    client = authenticated_property_owner["client"]
    owner = authenticated_property_owner["owner"]
    
    response = client.post("/api/properties/houses", json=test_house_data)
    
    assert response.status_code == 201
    assert response.json()["idPropertyOwner"] == owner.id
```

### Example: Service Test
```python
def test_my_service_method(db_session, test_house_data):
    """Test description"""
    from app.services.property_service import PropertyService
    
    service = PropertyService(db_session)
    result = service.some_method(test_house_data)
    
    assert result is not None
```

## Test Database

Tests use a separate test database (`sexto_andar_test_db`) to avoid affecting development data.

- Database is created fresh for each test
- All tables are dropped after each test
- No data persists between tests

## Authentication in Tests

Tests mock the authentication service responses:
- No real HTTP calls to `sexto-andar-auth`
- Mock users are created with `AuthUser` objects
- Dependency injection overrides handle authentication

## Continuous Integration

Tests can be run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Database Connection Error
Ensure PostgreSQL is running and test database exists:
```bash
psql -U sexto_andar_user -c "CREATE DATABASE sexto_andar_test_db;"
```

### Import Errors
Ensure you're in the project root and virtual environment is activated:
```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Tests Hanging
Check for:
- Database locks (restart PostgreSQL)
- Open database connections
- Background processes

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Use clear test method names
3. **AAA Pattern**: Arrange, Act, Assert
4. **Mock External Services**: Don't make real HTTP calls
5. **Clean Up**: Use fixtures to ensure cleanup
6. **Fast Tests**: Keep tests fast (< 1 second each)
7. **Coverage**: Aim for > 80% code coverage

## Coverage Goals

- Controllers: > 90%
- Services: > 85%
- Repositories: > 80%
- Models: > 75%
- Overall: > 80%
