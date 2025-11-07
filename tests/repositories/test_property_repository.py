"""
Tests for property repository layer
"""
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4
from decimal import Decimal

from app.repositories.property_repository import PropertyRepository
from app.models.property import Property, PropertyTypeEnum, SalesTypeEnum
from app.models.address import Address


class TestPropertyRepositoryCreate:
    """Test property repository create operations"""
    
    def test_create_property_success(self, db_session: Session):
        """Test creating a property via repository"""
        repo = PropertyRepository(db_session)
        
        # Create address
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Test Country"
        )
        
        # Create property
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.50"),
            description="Test property",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True,
            address=address
        )
        
        created = repo.create(property_obj)
        
        assert created.id is not None
        assert created.is_active is True
        assert created.address.street == "Test Street"


class TestPropertyRepositoryRead:
    """Test property repository read operations"""
    
    def test_get_by_id_success(self, db_session: Session):
        """Test retrieving property by ID"""
        repo = PropertyRepository(db_session)
        
        # Create a property
        address = Address(
            street="Test Street", number="123", city="Test City",
            postal_code="12345-678", country="Test Country"
        )
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.50"),
            description="Test property",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True,
            address=address
        )
        created = repo.create(property_obj)
        
        # Retrieve it
        retrieved = repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.description == created.description
    
    def test_get_by_id_not_found(self, db_session: Session):
        """Test retrieving non-existent property returns None"""
        repo = PropertyRepository(db_session)
        fake_id = uuid4()
        
        result = repo.get_by_id(fake_id)
        
        assert result is None
    
    def test_get_all(self, db_session: Session):
        """Test getting all properties"""
        repo = PropertyRepository(db_session)
        
        # Create multiple properties
        for i in range(3):
            address = Address(
                street=f"Street {i}", number=str(i), city="Test City",
                postal_code="12345-678", country="Test Country"
            )
            property_obj = Property(
                idPropertyOwner=str(uuid4()),
                propertySize=Decimal("100.00"),
                description=f"Property {i} with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Get all using get_all_paginated
        properties, total = repo.get_all_paginated(page=1, size=10)
        
        assert total == 3
        assert len(properties) == 3
    
    def test_get_all_with_pagination(self, db_session: Session):
        """Test pagination in get_all_paginated"""
        repo = PropertyRepository(db_session)
        
        # Create 5 properties
        for i in range(5):
            address = Address(
                street=f"Street {i}", number=str(i), city="Test City",
                postal_code="12345-678", country="Test Country"
            )
            property_obj = Property(
                idPropertyOwner=str(uuid4()),
                propertySize=Decimal("100.00"),
                description=f"Property {i} with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Get page 2 with size 2
        properties, total = repo.get_all_paginated(page=2, size=2)
        
        assert total == 5
        assert len(properties) == 2
    
    def test_get_by_owner(self, db_session: Session):
        """Test getting properties by owner"""
        repo = PropertyRepository(db_session)
        owner_id = str(uuid4())
        other_owner_id = str(uuid4())
        
        # Create properties for two owners
        for owner in [owner_id, owner_id, other_owner_id]:
            address = Address(
                street="Test Street", number="123", city="Test City",
                postal_code="12345-678", country="Test Country"
            )
            property_obj = Property(
                idPropertyOwner=owner,
                propertySize=Decimal("100.00"),
                description="Test property with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Get properties for first owner
        properties, total = repo.get_by_owner(owner_id, page=1, size=10)
        
        assert total == 2
        assert all(p.idPropertyOwner == owner_id for p in properties)


class TestPropertyRepositoryUpdate:
    """Test property repository update operations"""
    
    def test_update_property_success(self, db_session: Session):
        """Test updating a property"""
        repo = PropertyRepository(db_session)
        
        # Create a property
        address = Address(
            street="Test Street", number="123", city="Test City",
            postal_code="12345-678", country="Test Country"
        )
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.00"),
            description="Original description",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True,
            address=address
        )
        created = repo.create(property_obj)
        
        # Update it
        created.description = "Updated description"
        created.propertyValue = Decimal("400000.00")
        updated = repo.update(created)
        
        assert updated.description == "Updated description"
        assert updated.propertyValue == Decimal("400000.00")


class TestPropertyRepositoryDelete:
    """Test property repository delete operations"""
    
    def test_delete_property_success(self, db_session: Session):
        """Test deleting a property"""
        repo = PropertyRepository(db_session)
        
        # Create a property
        address = Address(
            street="Test Street", number="123", city="Test City",
            postal_code="12345-678", country="Test Country"
        )
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.00"),
            description="Test property with enough description",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True,
            address=address
        )
        created = repo.create(property_obj)
        property_id = str(created.id)
        
        # Delete it
        result = repo.delete(property_id)
        
        assert result is True
        
        # Verify it's gone
        retrieved = repo.get_by_id(property_id)
        assert retrieved is None


class TestPropertyRepositoryFilters:
    """Test property repository filtering operations"""
    
    def test_filter_by_property_type(self, db_session: Session):
        """Test filtering by property type"""
        repo = PropertyRepository(db_session)
        owner_id = str(uuid4())
        
        # Create houses and apartments
        for prop_type in [PropertyTypeEnum.HOUSE, PropertyTypeEnum.HOUSE, PropertyTypeEnum.APARTMENT]:
            address = Address(
                street="Test Street", number="123", city="Test City",
                postal_code="12345-678", country="Test Country"
            )
            property_obj = Property(
                idPropertyOwner=owner_id,
                propertySize=Decimal("100.00"),
                description="Test property with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=prop_type,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Filter by HOUSE
        properties, total = repo.get_all_paginated(
            page=1, size=10, property_type=PropertyTypeEnum.HOUSE
        )
        
        assert total == 2
        assert all(p.propertyType == PropertyTypeEnum.HOUSE for p in properties)
    
    def test_filter_by_sales_type(self, db_session: Session):
        """Test filtering by sales type"""
        repo = PropertyRepository(db_session)
        owner_id = str(uuid4())
        
        # Create properties for sale and rent
        for sales_type in [SalesTypeEnum.SALE, SalesTypeEnum.RENT, SalesTypeEnum.SALE]:
            address = Address(
                street="Test Street", number="123", city="Test City",
                postal_code="12345-678", country="Test Country"
            )
            property_obj = Property(
                idPropertyOwner=owner_id,
                propertySize=Decimal("100.00"),
                description="Test property with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=sales_type,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Filter by SALE
        properties, total = repo.get_all_paginated(
            page=1, size=10, sales_type=SalesTypeEnum.SALE
        )
        
        assert total == 2
        assert all(p.salesType == SalesTypeEnum.SALE for p in properties)
    
    def test_filter_active_only(self, db_session: Session):
        """Test filtering active properties only"""
        repo = PropertyRepository(db_session)
        owner_id = str(uuid4())
        
        # Create active and inactive properties
        for is_active in [True, True, False]:
            address = Address(
                street="Test Street", number="123", city="Test City",
                postal_code="12345-678", country="Test Country"
            )
            property_obj = Property(
                idPropertyOwner=owner_id,
                propertySize=Decimal("100.00"),
                description="Test property with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                is_active=is_active,
                address=address
            )
            repo.create(property_obj)
        
        # Get active only
        properties, total = repo.get_all_paginated(page=1, size=10, active_only=True)
        
        assert total == 2
        assert all(p.is_active for p in properties)
