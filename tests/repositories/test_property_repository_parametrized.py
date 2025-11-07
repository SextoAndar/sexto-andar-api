"""
Parametrized tests for property repository
Tests multiple scenarios with different input combinations
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.orm import Session
from app.repositories.property_repository import PropertyRepository
from app.models.property import Property, PropertyTypeEnum, SalesTypeEnum
from app.models.address import Address


@pytest.mark.repositories
class TestPropertyRepositoryParametrized:
    """Parametrized tests for property repository operations"""
    
    @pytest.mark.parametrize("property_type,sales_type,value", [
        (PropertyTypeEnum.HOUSE, SalesTypeEnum.SALE, "500000.00"),
        (PropertyTypeEnum.HOUSE, SalesTypeEnum.RENT, "300000.00"),
        (PropertyTypeEnum.APARTMENT, SalesTypeEnum.SALE, "400000.00"),
        (PropertyTypeEnum.APARTMENT, SalesTypeEnum.RENT, "250000.00"),
    ])
    def test_create_different_property_combinations(
        self, db_session: Session, property_type, sales_type, value
    ):
        """Test creating properties with different type and sales combinations"""
        repo = PropertyRepository(db_session)
        
        # Create address
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Brazil"
        )
        
        # Create property
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.00"),
            description="Test property with enough description for validation",
            propertyValue=Decimal(value),
            salesType=sales_type,
            propertyType=property_type,
            isPetAllowed=True,
            address=address
        )
        
        created = repo.create(property_obj)
        
        assert created.id is not None
        assert created.propertyType == property_type
        assert created.salesType == sales_type
        assert created.propertyValue == Decimal(value)
    
    @pytest.mark.parametrize("page,size,expected_min", [
        (1, 5, 5),
        (1, 10, 10),
        (2, 5, 0),  # Second page might be empty or have items
        (1, 20, 10),  # More than available
    ])
    def test_pagination_scenarios(
        self, db_session: Session, page, size, expected_min
    ):
        """Test different pagination scenarios"""
        repo = PropertyRepository(db_session)
        owner_id = str(uuid4())
        
        # Create 10 properties
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Brazil"
        )
        
        for i in range(10):
            property_obj = Property(
                idPropertyOwner=owner_id,
                propertySize=Decimal("100.00"),
                description=f"Test property number {i} with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Query with pagination
        properties, total = repo.get_by_owner(owner_id, page=page, size=size)
        
        assert total == 10
        if page == 1:
            assert len(properties) >= expected_min or len(properties) == total
    
    @pytest.mark.parametrize("property_size,expected_decimal", [
        ("50.00", Decimal("50.00")),
        ("100.50", Decimal("100.50")),
        ("250", Decimal("250")),
        ("1000.99", Decimal("1000.99")),
    ])
    def test_property_size_decimal_handling(
        self, db_session: Session, property_size, expected_decimal
    ):
        """Test proper handling of property size as Decimal"""
        repo = PropertyRepository(db_session)
        
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Brazil"
        )
        
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal(property_size),
            description="Test property with enough description for validation",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True,
            address=address
        )
        
        created = repo.create(property_obj)
        assert created.propertySize == expected_decimal
    
    @pytest.mark.parametrize("is_pet_allowed", [True, False])
    def test_pet_allowed_flag(self, db_session: Session, is_pet_allowed):
        """Test pet allowed flag works for both values"""
        repo = PropertyRepository(db_session)
        
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Brazil"
        )
        
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.00"),
            description="Test property with enough description for validation",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=is_pet_allowed,
            address=address
        )
        
        created = repo.create(property_obj)
        assert created.isPetAllowed == is_pet_allowed


@pytest.mark.repositories
class TestPropertyFilteringParametrized:
    """Parametrized tests for property filtering"""
    
    @pytest.mark.parametrize("filter_type,filter_value,expected_match", [
        ("property_type", PropertyTypeEnum.HOUSE, lambda p: p.propertyType == PropertyTypeEnum.HOUSE),
        ("property_type", PropertyTypeEnum.APARTMENT, lambda p: p.propertyType == PropertyTypeEnum.APARTMENT),
        ("sales_type", SalesTypeEnum.SALE, lambda p: p.salesType == SalesTypeEnum.SALE),
        ("sales_type", SalesTypeEnum.RENT, lambda p: p.salesType == SalesTypeEnum.RENT),
    ])
    def test_filtering_by_different_criteria(
        self, db_session: Session, filter_type, filter_value, expected_match
    ):
        """Test filtering by different criteria"""
        repo = PropertyRepository(db_session)
        
        # Create properties with different characteristics
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Brazil"
        )
        
        # Create diverse properties
        combinations = [
            (PropertyTypeEnum.HOUSE, SalesTypeEnum.SALE),
            (PropertyTypeEnum.HOUSE, SalesTypeEnum.RENT),
            (PropertyTypeEnum.APARTMENT, SalesTypeEnum.SALE),
            (PropertyTypeEnum.APARTMENT, SalesTypeEnum.RENT),
        ]
        
        for prop_type, sales_type in combinations:
            property_obj = Property(
                idPropertyOwner=str(uuid4()),
                propertySize=Decimal("100.00"),
                description="Test property with enough description for validation",
                propertyValue=Decimal("300000.00"),
                salesType=sales_type,
                propertyType=prop_type,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Filter
        if filter_type == "property_type":
            properties, total = repo.get_all_paginated(
                page=1, size=10, property_type=filter_value
            )
        else:
            properties, total = repo.get_all_paginated(
                page=1, size=10, sales_type=filter_value
            )
        
        # Verify all match the filter
        assert all(expected_match(p) for p in properties)
    
    @pytest.mark.parametrize("active_only,create_inactive", [
        (True, False),   # Only active, don't create inactive
        (True, True),    # Only active, but inactive exist
        (False, True),   # Include all, inactive exist
    ])
    def test_active_filtering_scenarios(
        self, db_session: Session, active_only, create_inactive
    ):
        """Test different active filtering scenarios"""
        repo = PropertyRepository(db_session)
        owner_id = str(uuid4())
        
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code="12345-678",
            country="Brazil"
        )
        
        # Create active properties
        for i in range(3):
            property_obj = Property(
                idPropertyOwner=owner_id,
                propertySize=Decimal("100.00"),
                description=f"Active property {i} with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            repo.create(property_obj)
        
        # Create inactive if needed
        if create_inactive:
            inactive_property = Property(
                idPropertyOwner=owner_id,
                propertySize=Decimal("100.00"),
                description="Inactive property with enough description",
                propertyValue=Decimal("300000.00"),
                salesType=SalesTypeEnum.SALE,
                propertyType=PropertyTypeEnum.HOUSE,
                isPetAllowed=True,
                address=address
            )
            created_inactive = repo.create(inactive_property)
            repo.deactivate(created_inactive)
        
        # Query
        properties, total = repo.get_by_owner(
            owner_id, page=1, size=10, active_only=active_only
        )
        
        if active_only:
            assert all(p.is_active for p in properties)
        else:
            # Should include both active and inactive
            has_inactive = any(not p.is_active for p in properties)
            if create_inactive:
                assert has_inactive


@pytest.mark.repositories
@pytest.mark.unit
class TestAddressRepositoryParametrized:
    """Parametrized tests for address data"""
    
    @pytest.mark.parametrize("street,number,city", [
        ("Rua Principal", "100", "São Paulo"),
        ("Avenida Paulista", "1000", "São Paulo"),
        ("Rua das Flores", "25A", "Rio de Janeiro"),
        ("Alameda Santos", "S/N", "Brasília"),
    ])
    def test_different_address_combinations(
        self, db_session: Session, street, number, city
    ):
        """Test creating addresses with different combinations"""
        address = Address(
            street=street,
            number=number,
            city=city,
            postal_code="12345-678",
            country="Brazil"
        )
        
        db_session.add(address)
        db_session.commit()
        db_session.refresh(address)
        
        assert address.id is not None
        assert address.street == street
        assert address.number == number
        assert address.city == city
    
    @pytest.mark.parametrize("postal_code", [
        "12345-678",
        "00000-000",
        "99999-999",
    ])
    def test_different_postal_codes(
        self, db_session: Session, postal_code
    ):
        """Test different postal code formats"""
        address = Address(
            street="Test Street",
            number="123",
            city="Test City",
            postal_code=postal_code,
            country="Brazil"
        )
        
        db_session.add(address)
        db_session.commit()
        db_session.refresh(address)
        
        assert address.postal_code == postal_code
