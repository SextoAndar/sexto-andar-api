"""
Integration tests for complete property workflows
These tests verify end-to-end functionality with database
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from app.services.property_service import PropertyService
from app.dtos.property_dto import CreateHouseRequest, CreateApartmentRequest, UpdatePropertyRequest
from app.models.property import Property


@pytest.mark.integration
class TestPropertyLifecycle:
    """Integration tests for complete property lifecycle"""
    
    def test_create_house_full_workflow(self, db_session: Session, test_house_data):
        """Test complete house creation workflow"""
        service = PropertyService(db_session)
        owner_id = "test-owner-123"
        
        # Create house
        house_request = CreateHouseRequest(**test_house_data)
        created_house = service.create_house(house_request, owner_id)
        
        # Verify creation
        assert created_house.id is not None
        assert str(created_house.idPropertyOwner) == owner_id
        assert created_house.is_active is True
        assert created_house.is_house() is True
        
        # Verify address was created
        assert created_house.address is not None
        assert created_house.address.street == test_house_data["address"]["street"]
        
        # Verify can retrieve by ID
        retrieved = service.get_property_by_id(str(created_house.id))
        assert retrieved.id == created_house.id
        assert retrieved.description == test_house_data["description"]
    
    def test_create_update_delete_workflow(self, db_session: Session, test_house_data):
        """Test create -> update -> delete workflow"""
        service = PropertyService(db_session)
        owner_id = "test-owner-456"
        
        # 1. Create
        house_request = CreateHouseRequest(**test_house_data)
        created = service.create_house(house_request, owner_id)
        original_description = created.description
        
        # 2. Update
        update_data = UpdatePropertyRequest(
            description="Updated description after creation",
            propertyValue="600000.00"
        )
        updated = service.update_property(
            str(created.id), update_data, owner_id
        )
        assert updated.description != original_description
        assert updated.description == "Updated description after creation"
        assert updated.propertyValue == Decimal("600000.00")
        
        # 3. Deactivate (soft delete)
        service.delete_property(str(created.id), owner_id, is_admin=False)
        
        # 4. Verify deactivated
        deactivated = service.get_property_by_id(str(created.id))
        assert deactivated.is_active is False
        
        # 5. Reactivate
        reactivated = service.activate_property(str(created.id), owner_id)
        assert reactivated.is_active is True
    
    def test_multiple_properties_same_owner(self, db_session: Session, test_house_data, test_apartment_data):
        """Test creating multiple properties for same owner"""
        service = PropertyService(db_session)
        owner_id = "test-owner-multi"
        
        # Create house
        house_request = CreateHouseRequest(**test_house_data)
        house = service.create_house(house_request, owner_id)
        
        # Create apartment
        apartment_request = CreateApartmentRequest(**test_apartment_data)
        apartment = service.create_apartment(apartment_request, owner_id)
        
        # Verify both exist
        properties, total = service.get_properties_by_owner(owner_id, page=1, size=10)
        assert total == 2
        assert len(properties) == 2
        
        # Verify types
        types = [p.propertyType.value for p in properties]
        assert "HOUSE" in types
        assert "APARTMENT" in types


@pytest.mark.integration
class TestPropertyFiltering:
    """Integration tests for property filtering"""
    
    def test_filter_by_sales_type(self, db_session: Session, test_house_data):
        """Test filtering properties by sales type"""
        service = PropertyService(db_session)
        owner_id = "test-owner-filter"
        
        # Create properties with different sales types
        test_house_data["salesType"] = "sale"
        house_sale = CreateHouseRequest(**test_house_data)
        service.create_house(house_sale, owner_id)
        
        test_house_data["salesType"] = "rent"
        house_rent = CreateHouseRequest(**test_house_data)
        service.create_house(house_rent, owner_id)
        
        # Filter by sale
        properties, total = service.get_all_properties(
            page=1, size=10, sales_type="sale"
        )
        assert all(p.salesType.value == "SALE" for p in properties)
        
        # Filter by rent
        properties, total = service.get_all_properties(
            page=1, size=10, sales_type="rent"
        )
        assert all(p.salesType.value == "RENT" for p in properties)
    
    def test_filter_by_property_type(self, db_session: Session, test_house_data, test_apartment_data):
        """Test filtering properties by type"""
        service = PropertyService(db_session)
        owner_id = "test-owner-type-filter"
        
        # Create house
        house_request = CreateHouseRequest(**test_house_data)
        service.create_house(house_request, owner_id)
        
        # Create apartment
        apartment_request = CreateApartmentRequest(**test_apartment_data)
        service.create_apartment(apartment_request, owner_id)
        
        # Filter by house
        properties, total = service.get_all_properties(
            page=1, size=10, property_type="house"
        )
        assert all(p.propertyType.value == "HOUSE" for p in properties)
        
        # Filter by apartment
        properties, total = service.get_all_properties(
            page=1, size=10, property_type="apartment"
        )
        assert all(p.propertyType.value == "APARTMENT" for p in properties)
    
    def test_filter_active_only(self, db_session: Session, test_house_data):
        """Test filtering active vs inactive properties"""
        service = PropertyService(db_session)
        owner_id = "test-owner-active-filter"
        
        # Create properties
        house_request = CreateHouseRequest(**test_house_data)
        house1 = service.create_house(house_request, owner_id)
        house2 = service.create_house(house_request, owner_id)
        
        # Deactivate one
        service.delete_property(str(house1.id), owner_id, is_admin=False)
        
        # Filter active only
        properties, total = service.get_all_properties(
            page=1, size=10, active_only=True
        )
        assert all(p.is_active for p in properties)
        
        # Include inactive
        properties, total = service.get_all_properties(
            page=1, size=10, active_only=False
        )
        active_count = sum(1 for p in properties if p.is_active)
        inactive_count = sum(1 for p in properties if not p.is_active)
        assert inactive_count >= 1


@pytest.mark.integration
class TestPropertyStatistics:
    """Integration tests for property statistics"""
    
    def test_portfolio_statistics_calculation(self, db_session: Session, test_house_data, test_apartment_data):
        """Test portfolio statistics are calculated correctly"""
        service = PropertyService(db_session)
        owner_id = "test-owner-stats"
        
        # Create 2 houses for sale
        test_house_data["salesType"] = "sale"
        test_house_data["propertyValue"] = "500000.00"
        house_request = CreateHouseRequest(**test_house_data)
        service.create_house(house_request, owner_id)
        service.create_house(house_request, owner_id)
        
        # Create 1 apartment for rent
        test_apartment_data["salesType"] = "rent"
        test_apartment_data["propertyValue"] = "300000.00"
        apartment_request = CreateApartmentRequest(**test_apartment_data)
        service.create_apartment(apartment_request, owner_id)
        
        # Get statistics
        stats = service.get_portfolio_stats(owner_id)
        
        # Verify counts
        assert stats["total_properties"] == 3
        assert stats["active_properties"] == 3
        assert stats["inactive_properties"] == 0
        assert stats["total_houses"] == 2
        assert stats["total_apartments"] == 1
        assert stats["total_for_sale"] == 2
        assert stats["total_for_rent"] == 1
        
        # Verify financial calculations
        assert Decimal(stats["total_portfolio_value"]) == Decimal("1300000.00")
    
    def test_statistics_with_inactive_properties(self, db_session: Session, test_house_data):
        """Test statistics correctly handle inactive properties"""
        service = PropertyService(db_session)
        owner_id = "test-owner-stats-inactive"
        
        # Create 3 houses
        house_request = CreateHouseRequest(**test_house_data)
        house1 = service.create_house(house_request, owner_id)
        service.create_house(house_request, owner_id)
        service.create_house(house_request, owner_id)
        
        # Deactivate one
        service.delete_property(str(house1.id), owner_id, is_admin=False)
        
        # Get statistics
        stats = service.get_portfolio_stats(owner_id)
        
        # Verify counts include inactive
        assert stats["total_properties"] == 3
        assert stats["active_properties"] == 2
        assert stats["inactive_properties"] == 1


@pytest.mark.integration
@pytest.mark.slow
class TestPropertyPagination:
    """Integration tests for pagination"""
    
    def test_pagination_first_page(self, db_session: Session, test_house_data):
        """Test retrieving first page of results"""
        service = PropertyService(db_session)
        owner_id = "test-owner-pagination"
        
        # Create 15 properties
        house_request = CreateHouseRequest(**test_house_data)
        for _ in range(15):
            service.create_house(house_request, owner_id)
        
        # Get first page (10 items)
        properties, total = service.get_properties_by_owner(
            owner_id, page=1, size=10
        )
        
        assert len(properties) == 10
        assert total == 15
    
    def test_pagination_second_page(self, db_session: Session, test_house_data):
        """Test retrieving second page of results"""
        service = PropertyService(db_session)
        owner_id = "test-owner-pagination-2"
        
        # Create 15 properties
        house_request = CreateHouseRequest(**test_house_data)
        for _ in range(15):
            service.create_house(house_request, owner_id)
        
        # Get second page
        properties, total = service.get_properties_by_owner(
            owner_id, page=2, size=10
        )
        
        assert len(properties) == 5  # Remaining items
        assert total == 15
    
    @pytest.mark.parametrize("page_size", [5, 10, 20, 50])
    def test_different_page_sizes(self, db_session: Session, test_house_data, page_size):
        """Test pagination with different page sizes"""
        service = PropertyService(db_session)
        owner_id = f"test-owner-size-{page_size}"
        
        # Create 25 properties
        house_request = CreateHouseRequest(**test_house_data)
        for _ in range(25):
            service.create_house(house_request, owner_id)
        
        # Get first page with specific size
        properties, total = service.get_properties_by_owner(
            owner_id, page=1, size=page_size
        )
        
        assert len(properties) == min(page_size, 25)
        assert total == 25


@pytest.mark.integration
class TestPropertyOwnership:
    """Integration tests for property ownership validation"""
    
    def test_owner_can_update_own_property(self, db_session: Session, test_house_data):
        """Test owner can update their own property"""
        service = PropertyService(db_session)
        owner_id = "test-owner-ownership"
        
        house_request = CreateHouseRequest(**test_house_data)
        created = service.create_house(house_request, owner_id)
        
        # Update as owner - should succeed
        update_data = UpdatePropertyRequest(
            description="Updated by owner with valid description"
        )
        updated = service.update_property(
            str(created.id), update_data, owner_id
        )
        assert updated.description == "Updated by owner with valid description"
    
    def test_non_owner_cannot_update_property(self, db_session: Session, test_house_data):
        """Test non-owner cannot update property"""
        service = PropertyService(db_session)
        owner_id = "test-owner-original"
        other_user_id = "test-owner-other"
        
        house_request = CreateHouseRequest(**test_house_data)
        created = service.create_house(house_request, owner_id)
        
        # Try to update as different user - should fail
        update_data = UpdatePropertyRequest(
            description="Attempted update by non-owner with valid description"
        )
        
        with pytest.raises(Exception) as exc_info:
            service.update_property(
                str(created.id), update_data, other_user_id
            )
        assert "permission" in str(exc_info.value).lower()
    
    def test_admin_can_delete_any_property(self, db_session: Session, test_house_data):
        """Test admin can delete any property"""
        service = PropertyService(db_session)
        owner_id = "test-owner-admin-test"
        admin_id = "test-admin-123"
        
        house_request = CreateHouseRequest(**test_house_data)
        created = service.create_house(house_request, owner_id)
        
        # Delete as admin - should succeed
        service.delete_property(
            str(created.id), admin_id, is_admin=True
        )
        
        # Verify deactivated
        deactivated = service.get_property_by_id(str(created.id))
        assert deactivated.is_active is False
