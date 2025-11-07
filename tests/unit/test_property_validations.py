"""
Unit tests for property validations and business logic
These tests don't require database or external dependencies
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError
from app.dtos.property_dto import (
    CreateHouseRequest,
    CreateApartmentRequest,
    UpdatePropertyRequest,
    AddressRequest
)


@pytest.mark.unit
class TestAddressValidation:
    """Unit tests for address validation"""
    
    @pytest.mark.parametrize("postal_code", [
        "12345-678",
        "98765-432",
        "00000-000",
    ])
    def test_valid_postal_codes(self, postal_code):
        """Test valid Brazilian postal codes"""
        address = AddressRequest(
            street="Rua Teste",
            number="123",
            city="São Paulo",
            postal_code=postal_code,
            country="Brazil"
        )
        assert address.postal_code == postal_code
    
    @pytest.mark.parametrize("postal_code", [
        "1234-567",      # Too short
        "123456789",     # No hyphen
        "12345-67",      # Second part too short
        "ABCDE-FGH",     # Letters instead of numbers
    ])
    def test_invalid_postal_codes(self, postal_code):
        """Test invalid postal codes should raise ValidationError"""
        with pytest.raises(ValidationError):
            AddressRequest(
                street="Rua Teste",
                number="123",
                city="São Paulo",
                postal_code=postal_code,
                country="Brazil"
            )


@pytest.mark.unit
class TestPropertyDescriptionValidation:
    """Unit tests for property description validation"""
    
    @pytest.mark.parametrize("description", [
        "A" * 10,  # Minimum valid length
        "Beautiful house with garden",
        "Modern apartment with amazing view and great location in the city",
        "X" * 500,  # Long description
    ])
    def test_valid_descriptions(self, description, test_house_data):
        """Test valid descriptions (10+ characters)"""
        test_house_data["description"] = description
        house = CreateHouseRequest(**test_house_data)
        assert house.description == description
    
    @pytest.mark.parametrize("description", [
        "Short",      # 5 chars
        "Test",       # 4 chars
        "X",          # 1 char
        "",           # Empty
    ])
    def test_invalid_descriptions(self, description, test_house_data):
        """Test invalid descriptions (< 10 characters)"""
        test_house_data["description"] = description
        with pytest.raises(ValidationError) as exc_info:
            CreateHouseRequest(**test_house_data)
        assert "at least 10 characters" in str(exc_info.value)


@pytest.mark.unit
class TestPropertySalesTypeValidation:
    """Unit tests for sales type validation"""
    
    @pytest.mark.parametrize("sales_type", ["sale", "rent"])
    def test_valid_sales_types(self, sales_type, test_house_data):
        """Test valid sales types"""
        test_house_data["salesType"] = sales_type
        house = CreateHouseRequest(**test_house_data)
        assert house.salesType == sales_type
    
    @pytest.mark.parametrize("sales_type", [
        "SALE",       # Uppercase (should fail with current validation)
        "RENT",       # Uppercase
        "lease",      # Invalid type
        "buy",        # Invalid type
        "exchange",   # Invalid type
    ])
    def test_invalid_sales_types(self, sales_type, test_house_data):
        """Test invalid sales types"""
        test_house_data["salesType"] = sales_type
        with pytest.raises(ValidationError) as exc_info:
            CreateHouseRequest(**test_house_data)
        assert "not a valid SalesTypeEnum" in str(exc_info.value)


@pytest.mark.unit
class TestPropertyValueValidation:
    """Unit tests for property value validation"""
    
    @pytest.mark.parametrize("value,expected", [
        ("100000.00", Decimal("100000.00")),
        ("500000.50", Decimal("500000.50")),
        ("1000000", Decimal("1000000")),
        ("0.01", Decimal("0.01")),
    ])
    def test_valid_property_values(self, value, expected, test_house_data):
        """Test valid property values"""
        test_house_data["propertyValue"] = value
        house = CreateHouseRequest(**test_house_data)
        assert house.propertyValue == expected
    
    @pytest.mark.parametrize("value", [
        "0",          # Zero value
        "-100000",    # Negative value
        "abc",        # Non-numeric
    ])
    def test_invalid_property_values(self, value, test_house_data):
        """Test invalid property values"""
        test_house_data["propertyValue"] = value
        with pytest.raises((ValidationError, ValueError)):
            CreateHouseRequest(**test_house_data)


@pytest.mark.unit
class TestHouseSpecificValidation:
    """Unit tests for house-specific validation"""
    
    @pytest.mark.parametrize("land_price,expected", [
        ("50000.00", Decimal("50000.00")),
        ("100000", Decimal("100000")),
        (None, None),  # Optional field
    ])
    def test_valid_land_prices(self, land_price, expected, test_house_data):
        """Test valid land prices"""
        test_house_data["landPrice"] = land_price
        house = CreateHouseRequest(**test_house_data)
        assert house.landPrice == expected
    
    @pytest.mark.parametrize("is_single_house", [True, False])
    def test_is_single_house_flag(self, is_single_house, test_house_data):
        """Test is_single_house flag"""
        test_house_data["isSingleHouse"] = is_single_house
        house = CreateHouseRequest(**test_house_data)
        assert house.isSingleHouse == is_single_house


@pytest.mark.unit
class TestApartmentSpecificValidation:
    """Unit tests for apartment-specific validation"""
    
    @pytest.mark.parametrize("floor,expected", [
        (1, 1),
        (10, 10),
        (0, 0),    # Ground floor
        (-1, -1),  # Basement
    ])
    def test_valid_floor_numbers(self, floor, expected, test_apartment_data):
        """Test valid floor numbers"""
        test_apartment_data["floor"] = floor
        apartment = CreateApartmentRequest(**test_apartment_data)
        assert apartment.floor == expected
    
    @pytest.mark.parametrize("condominium_fee,expected", [
        ("500.00", Decimal("500.00")),
        ("1200.50", Decimal("1200.50")),
        ("0", Decimal("0")),
    ])
    def test_valid_condominium_fees(self, condominium_fee, expected, test_apartment_data):
        """Test valid condominium fees"""
        test_apartment_data["condominiumFee"] = condominium_fee
        apartment = CreateApartmentRequest(**test_apartment_data)
        assert apartment.condominiumFee == expected
    
    @pytest.mark.parametrize("common_area", [True, False])
    def test_common_area_flag(self, common_area, test_apartment_data):
        """Test common area flag"""
        test_apartment_data["commonArea"] = common_area
        apartment = CreateApartmentRequest(**test_apartment_data)
        assert apartment.commonArea == common_area


@pytest.mark.unit
class TestUpdatePropertyValidation:
    """Unit tests for property update validation"""
    
    def test_empty_update_is_valid(self):
        """Test that empty update request is valid"""
        update = UpdatePropertyRequest()
        assert update.description is None
        assert update.propertyValue is None
    
    @pytest.mark.parametrize("field,value", [
        ("description", "Updated description with enough characters"),
        ("propertyValue", "600000.00"),
        ("salesType", "rent"),
        ("condominiumFee", "800.00"),
    ])
    def test_partial_updates(self, field, value):
        """Test partial updates with single fields"""
        update = UpdatePropertyRequest(**{field: value})
        assert getattr(update, field) is not None
    
    def test_update_with_invalid_description(self):
        """Test update with invalid description fails"""
        with pytest.raises(ValidationError):
            UpdatePropertyRequest(description="Short")
