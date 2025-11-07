"""
Tests for property and address models
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from app.models.property import Property, PropertyTypeEnum, SalesTypeEnum
from app.models.address import Address


class TestPropertyModel:
    """Test Property model"""
    
    def test_create_property_instance(self):
        """Test creating a property instance"""
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.50"),
            description="Test property with enough description",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True
        )
        
        assert property_obj.idPropertyOwner is not None
        assert property_obj.propertySize == Decimal("100.50")
        assert property_obj.salesType == SalesTypeEnum.SALE
        assert property_obj.propertyType == PropertyTypeEnum.HOUSE
        # is_active is set in the database, not in __init__
    
    def test_property_enums(self):
        """Test property enums"""
        assert PropertyTypeEnum.HOUSE.value == "HOUSE"
        assert PropertyTypeEnum.APARTMENT.value == "APARTMENT"
        assert SalesTypeEnum.SALE.value == "SALE"
        assert SalesTypeEnum.RENT.value == "RENT"
    
    def test_property_default_values(self):
        """Test property default values"""
        property_obj = Property(
            idPropertyOwner=str(uuid4()),
            propertySize=Decimal("100.00"),
            description="Test property with enough characters for validation",
            propertyValue=Decimal("300000.00"),
            salesType=SalesTypeEnum.SALE,
            propertyType=PropertyTypeEnum.HOUSE,
            isPetAllowed=True
        )
        
        # These are set by database defaults, not in Python
        assert property_obj.created_at is not None
        assert property_obj.updated_at is not None


class TestAddressModel:
    """Test Address model"""
    
    def test_create_address_instance(self):
        """Test creating an address instance"""
        address = Address(
            street="Rua Teste",
            number="123",
            city="São Paulo",
            postal_code="01234-567",
            country="Brazil"
        )
        
        assert address.street == "Rua Teste"
        assert address.number == "123"
        assert address.city == "São Paulo"
        assert address.postal_code == "01234-567"
        assert address.country == "Brazil"
    
    def test_address_minimal_fields(self):
        """Test address with only required fields"""
        address = Address(
            street="Rua Teste",
            number="123",
            city="São Paulo",
            postal_code="01234567",
            country="Brazil"
        )
        
        assert address.street == "Rua Teste"
        assert address.number == "123"
        assert address.city == "São Paulo"
