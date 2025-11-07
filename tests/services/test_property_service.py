"""
Tests for property service layer
"""
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.property_service import PropertyService
from app.dtos.property_dto import CreateHouseRequest, CreateApartmentRequest, UpdatePropertyRequest
from app.models.property import PropertyTypeEnum, SalesTypeEnum


class TestPropertyServiceCreation:
    """Test property service creation methods"""
    
    def test_create_house_success(self, db_session: Session, test_house_data):
        """Test successful house creation via service"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        house_request = CreateHouseRequest(**test_house_data)
        property_obj = property_service.create_house(house_request, owner_id)
        
        assert property_obj.id is not None
        assert property_obj.propertyType == PropertyTypeEnum.HOUSE
        assert str(property_obj.idPropertyOwner) == owner_id
        assert property_obj.is_active is True
        assert property_obj.address is not None
        assert property_obj.address.street == test_house_data["address"]["street"]
    
    def test_create_apartment_success(self, db_session: Session, test_apartment_data):
        """Test successful apartment creation via service"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        apartment_request = CreateApartmentRequest(**test_apartment_data)
        property_obj = property_service.create_apartment(apartment_request, owner_id)
        
        assert property_obj.id is not None
        assert property_obj.propertyType == PropertyTypeEnum.APARTMENT
        assert property_obj.floor == test_apartment_data["floor"]
        assert property_obj.condominiumFee is not None


class TestPropertyServiceRetrieval:
    """Test property service retrieval methods"""
    
    def test_get_property_by_id_success(self, db_session: Session, test_house_data):
        """Test retrieving property by ID"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create a property
        house_request = CreateHouseRequest(**test_house_data)
        created_property = property_service.create_house(house_request, owner_id)
        
        # Retrieve it
        retrieved_property = property_service.get_property_by_id(str(created_property.id))
        
        assert retrieved_property.id == created_property.id
        assert retrieved_property.description == created_property.description
    
    def test_get_property_by_id_not_found(self, db_session: Session):
        """Test retrieving non-existent property raises exception"""
        property_service = PropertyService(db_session)
        fake_id = str(uuid4())
        
        with pytest.raises(Exception):  # Should raise HTTPException or similar
            property_service.get_property_by_id(fake_id)
    
    def test_get_all_properties(self, db_session: Session, test_house_data):
        """Test getting all properties with pagination"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create multiple properties
        house_request = CreateHouseRequest(**test_house_data)
        property_service.create_house(house_request, owner_id)
        property_service.create_house(house_request, owner_id)
        
        # Get all properties
        properties, total = property_service.get_all_properties(page=1, size=10)
        
        assert total == 2
        assert len(properties) == 2
    
    def test_get_all_properties_with_filters(self, db_session: Session, test_house_data, test_apartment_data):
        """Test getting properties with filters"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create house and apartment
        house_request = CreateHouseRequest(**test_house_data)
        apartment_request = CreateApartmentRequest(**test_apartment_data)
        property_service.create_house(house_request, owner_id)
        property_service.create_apartment(apartment_request, owner_id)
        
        # Filter by type
        houses, total_houses = property_service.get_all_properties(
            page=1, size=10, property_type="HOUSE"
        )
        
        assert total_houses == 1
        assert all(p.propertyType == PropertyTypeEnum.HOUSE for p in houses)
    
    def test_get_properties_by_owner(self, db_session: Session, test_house_data):
        """Test getting properties by owner ID"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        other_owner_id = str(uuid4())
        
        # Create properties for two owners
        house_request = CreateHouseRequest(**test_house_data)
        property_service.create_house(house_request, owner_id)
        property_service.create_house(house_request, owner_id)
        property_service.create_house(house_request, other_owner_id)
        
        # Get properties for first owner
        properties, total = property_service.get_properties_by_owner(
            owner_id=owner_id, page=1, size=10
        )
        
        assert total == 2
        assert all(str(p.idPropertyOwner) == owner_id for p in properties)


class TestPropertyServiceUpdate:
    """Test property service update methods"""
    
    def test_update_property_success(self, db_session: Session, test_house_data):
        """Test successful property update"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create a property
        house_request = CreateHouseRequest(**test_house_data)
        property_obj = property_service.create_house(house_request, owner_id)
        
        # Update it
        update_data = UpdatePropertyRequest(
            description="Updated description",
            propertyValue="700000.00"
        )
        updated_property = property_service.update_property(
            str(property_obj.id), update_data, owner_id
        )
        
        assert updated_property.description == "Updated description"
        assert str(updated_property.propertyValue) == "700000.00"
    
    def test_update_property_not_owner(self, db_session: Session, test_house_data):
        """Test updating property by non-owner raises exception"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        other_user_id = str(uuid4())
        
        # Create a property
        house_request = CreateHouseRequest(**test_house_data)
        property_obj = property_service.create_house(house_request, owner_id)
        
        # Try to update with different owner (description must be 10+ chars)
        update_data = UpdatePropertyRequest(description="Hacked property by unauthorized user")
        
        with pytest.raises(Exception):  # Should raise permission error
            property_service.update_property(
                str(property_obj.id), update_data, other_user_id
            )


class TestPropertyServiceDeletion:
    """Test property service deletion/deactivation methods"""
    
    def test_deactivate_property_success(self, db_session: Session, test_house_data):
        """Test successful property deactivation"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create a property
        house_request = CreateHouseRequest(**test_house_data)
        property_obj = property_service.create_house(house_request, owner_id)
        
        # Deactivate it (soft delete)
        property_service.delete_property(
            str(property_obj.id), owner_id, is_admin=False
        )
        
        # Fetch again and verify it's deactivated
        updated = property_service.get_property_by_id(str(property_obj.id))
        assert updated.is_active is False
    
    def test_reactivate_property_success(self, db_session: Session, test_house_data):
        """Test successful property reactivation"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create and deactivate a property
        house_request = CreateHouseRequest(**test_house_data)
        property_obj = property_service.create_house(house_request, owner_id)
        property_service.delete_property(str(property_obj.id), owner_id, is_admin=False)
        
        # Reactivate it
        reactivated = property_service.activate_property(
            str(property_obj.id), owner_id
        )
        
        assert reactivated.is_active is True


class TestPropertyServiceStatistics:
    """Test property service statistics methods"""
    
    def test_get_portfolio_statistics(self, db_session: Session, test_house_data, test_apartment_data):
        """Test getting portfolio statistics"""
        property_service = PropertyService(db_session)
        owner_id = str(uuid4())
        
        # Create properties
        house_request = CreateHouseRequest(**test_house_data)
        apartment_request = CreateApartmentRequest(**test_apartment_data)
        
        property_service.create_house(house_request, owner_id)
        property_service.create_apartment(apartment_request, owner_id)
        
        # Deactivate one (using delete_property which does soft delete)
        house = property_service.create_house(house_request, owner_id)
        property_service.delete_property(str(house.id), owner_id, is_admin=False)
        
        # Get statistics (method is get_portfolio_stats, not get_portfolio_statistics)
        stats = property_service.get_portfolio_stats(owner_id)
        
        # Get statistics returns a dict with snake_case keys
        assert stats["total_properties"] == 3
        assert stats["active_properties"] == 2
        assert stats["inactive_properties"] == 1
        assert stats["total_houses"] == 2
        assert stats["total_apartments"] == 1
        assert stats["total_for_sale"] >= 1
        assert stats["total_for_rent"] >= 1
        assert float(stats["total_portfolio_value"]) > 0


