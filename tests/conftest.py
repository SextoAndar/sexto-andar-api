"""
Pytest configuration and fixtures for sexto-andar-api
"""
import os
import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import Mock, patch
from uuid import uuid4

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql://sexto_andar_user:sexto_andar_pass@localhost:5432/sexto_andar_test_db"
os.environ["AUTH_SERVICE_URL"] = "http://localhost:8001"
os.environ["API_BASE_PATH"] = "/api"
os.environ["SQL_DEBUG"] = "false"

from app.main import app
from app.database.connection import get_db
from app.models.base import Base
from app.models.property import Property
from app.models.address import Address

# Test database URL
TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session override"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user from auth service"""
    from app.auth.dependencies import AuthUser
    return AuthUser({
        "sub": str(uuid4()),
        "username": "testuser",
        "role": "USER"
    })


@pytest.fixture
def mock_auth_property_owner():
    """Mock authenticated property owner from auth service"""
    from app.auth.dependencies import AuthUser
    return AuthUser({
        "sub": str(uuid4()),
        "username": "testowner",
        "role": "PROPERTY_OWNER"
    })


@pytest.fixture
def mock_auth_admin():
    """Mock authenticated admin from auth service"""
    from app.auth.dependencies import AuthUser
    return AuthUser({
        "sub": str(uuid4()),
        "username": "testadmin",
        "role": "ADMIN"
    })


@pytest.fixture
def test_address_data():
    """Sample address data for testing"""
    return {
        "street": "Rua Teste",
        "number": "123",
        "city": "São Paulo",
        "postal_code": "01234-567",
        "country": "Brazil"
    }


@pytest.fixture
def test_house_data(test_address_data):
    """Sample house data for testing"""
    return {
        "address": test_address_data,
        "propertySize": "150.50",
        "description": "Beautiful test house with garden and large backyard",
        "propertyValue": "500000.00",
        "salesType": "sale",
        "isPetAllowed": True,
        "landPrice": "200000.00",
        "isSingleHouse": True
    }


@pytest.fixture
def test_apartment_data(test_address_data):
    """Sample apartment data for testing"""
    return {
        "address": test_address_data,
        "propertySize": "85.00",
        "description": "Modern test apartment with balcony and parking",
        "propertyValue": "350000.00",
        "salesType": "rent",
        "isPetAllowed": False,
        "condominiumFee": "500.00",
        "commonArea": True,
        "floor": 5
    }


@pytest.fixture
def authenticated_property_owner(client: TestClient, mock_auth_property_owner):
    """Mock authenticated property owner with dependency override"""
    from app.auth.dependencies import get_current_property_owner, get_current_user
    
    def override_get_current_property_owner():
        return mock_auth_property_owner
    
    def override_get_current_user():
        return mock_auth_property_owner
    
    app.dependency_overrides[get_current_property_owner] = override_get_current_property_owner
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield {
        "owner": mock_auth_property_owner,
        "client": client
    }
    
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_user(client: TestClient, mock_auth_user):
    """Mock authenticated user with dependency override"""
    from app.auth.dependencies import get_current_user
    
    def override_get_current_user():
        return mock_auth_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield {
        "user": mock_auth_user,
        "client": client
    }
    
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_admin(client: TestClient, mock_auth_admin):
    """Mock authenticated admin with dependency override"""
    from app.auth.dependencies import get_current_admin
    
    def override_get_current_admin():
        return mock_auth_admin
    
    app.dependency_overrides[get_current_admin] = override_get_current_admin
    
    yield {
        "admin": mock_auth_admin,
        "client": client
    }
    
    app.dependency_overrides.clear()


@pytest.fixture
def created_property(db_session: Session, mock_auth_property_owner, test_house_data):
    """Create a test property in the database"""
    from app.services.property_service import PropertyService
    from app.dtos.property_dto import CreateHouseRequest
    
    property_service = PropertyService(db_session)
    house_request = CreateHouseRequest(**test_house_data)
    property_obj = property_service.create_house(house_request, mock_auth_property_owner.id)
    
    return property_obj
