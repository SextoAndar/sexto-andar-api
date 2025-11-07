"""
Tests for property controller endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestPropertyCreation:
    """Test property creation endpoints"""
    
    def test_create_house_success(self, authenticated_property_owner, test_house_data):
        """Test successful house creation"""
        client = authenticated_property_owner["client"]
        owner = authenticated_property_owner["owner"]
        
        response = client.post("/api/properties/houses", json=test_house_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["propertyType"] == "HOUSE"
        assert data["salesType"] == "SALE"
        assert data["propertySize"] == test_house_data["propertySize"]
        assert data["description"] == test_house_data["description"]
        assert data["idPropertyOwner"] == owner.id
        assert data["is_active"] is True
        assert "address" in data
        assert data["address"]["street"] == test_house_data["address"]["street"]
    
    def test_create_apartment_success(self, authenticated_property_owner, test_apartment_data):
        """Test successful apartment creation"""
        client = authenticated_property_owner["client"]
        
        response = client.post("/api/properties/apartments", json=test_apartment_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["propertyType"] == "APARTMENT"
        assert data["floor"] == test_apartment_data["floor"]
        assert data["condominiumFee"] == test_apartment_data["condominiumFee"]
        assert data["commonArea"] == test_apartment_data["commonArea"]
    
    def test_create_house_without_authentication(self, client, test_house_data):
        """Test house creation without authentication fails"""
        response = client.post("/api/properties/houses", json=test_house_data)
        
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
    
    def test_create_house_invalid_sales_type(self, authenticated_property_owner, test_house_data):
        """Test house creation with invalid sales type fails"""
        client = authenticated_property_owner["client"]
        invalid_data = test_house_data.copy()
        invalid_data["salesType"] = "INVALID"
        
        response = client.post("/api/properties/houses", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_house_missing_fields(self, authenticated_property_owner):
        """Test house creation with missing required fields fails"""
        client = authenticated_property_owner["client"]
        incomplete_data = {
            "propertySize": "150.50",
            "salesType": "SALE"
            # Missing address, description, propertyValue, etc.
        }
        
        response = client.post("/api/properties/houses", json=incomplete_data)
        
        assert response.status_code == 422
    
    def test_create_apartment_missing_floor(self, authenticated_property_owner, test_apartment_data):
        """Test apartment creation without floor field fails"""
        client = authenticated_property_owner["client"]
        invalid_data = test_apartment_data.copy()
        del invalid_data["floor"]
        
        response = client.post("/api/properties/apartments", json=invalid_data)
        
        assert response.status_code == 422


class TestPropertyRetrieval:
    """Test property retrieval endpoints"""
    
    def test_get_property_by_id_success(self, client, created_property):
        """Test retrieving a property by ID"""
        property_id = str(created_property.id)
        
        response = client.get(f"/api/properties/{property_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == property_id
        assert data["propertyType"] == created_property.propertyType.value
        assert "address" in data
    
    def test_get_property_not_found(self, client):
        """Test retrieving non-existent property returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(f"/api/properties/{fake_id}")
        
        assert response.status_code == 404
    
    def test_list_all_properties(self, client, created_property):
        """Test listing all properties"""
        response = client.get("/api/properties/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "properties" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] >= 1
        assert len(data["properties"]) >= 1
    
    def test_list_properties_pagination(self, client, created_property):
        """Test property listing with pagination"""
        response = client.get("/api/properties/?page=1&size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["size"] == 5
        assert len(data["properties"]) <= 5
    
    def test_list_properties_filter_by_type(self, client, created_property):
        """Test filtering properties by type"""
        response = client.get("/api/properties/?property_type=HOUSE")
        
        assert response.status_code == 200
        data = response.json()
        
        for prop in data["properties"]:
            assert prop["propertyType"] == "HOUSE"
    
    def test_list_properties_filter_by_sales_type(self, client, created_property):
        """Test filtering properties by sales type"""
        response = client.get("/api/properties/?sales_type=SALE")
        
        assert response.status_code == 200
        data = response.json()
        
        for prop in data["properties"]:
            assert prop["salesType"] == "SALE"


class TestPropertyOwnerPortfolio:
    """Test property owner portfolio endpoints"""
    
    def test_get_my_properties(self, authenticated_property_owner, db_session, test_house_data):
        """Test owner retrieving their own properties"""
        client = authenticated_property_owner["client"]
        owner = authenticated_property_owner["owner"]
        
        # Create a property for this owner
        from app.services.property_service import PropertyService
        from app.dtos.property_dto import CreateHouseRequest
        
        property_service = PropertyService(db_session)
        house_request = CreateHouseRequest(**test_house_data)
        property_service.create_house(house_request, owner.id)
        
        response = client.get("/api/properties/owner/my-properties")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 1
        assert all(prop["idPropertyOwner"] == owner.id for prop in data["properties"])
    
    def test_get_my_properties_filter_by_type(self, authenticated_property_owner, db_session, test_house_data):
        """Test filtering owner's properties by type"""
        client = authenticated_property_owner["client"]
        owner = authenticated_property_owner["owner"]
        
        # Create a house
        from app.services.property_service import PropertyService
        from app.dtos.property_dto import CreateHouseRequest
        
        property_service = PropertyService(db_session)
        house_request = CreateHouseRequest(**test_house_data)
        property_service.create_house(house_request, owner.id)
        
        response = client.get("/api/properties/owner/my-properties?property_type=HOUSE")
        
        assert response.status_code == 200
        data = response.json()
        
        for prop in data["properties"]:
            assert prop["propertyType"] == "HOUSE"
            assert prop["idPropertyOwner"] == owner.id
    
    def test_get_portfolio_statistics(self, authenticated_property_owner, db_session, test_house_data):
        """Test getting portfolio statistics"""
        client = authenticated_property_owner["client"]
        owner = authenticated_property_owner["owner"]
        
        # Create a property
        from app.services.property_service import PropertyService
        from app.dtos.property_dto import CreateHouseRequest
        
        property_service = PropertyService(db_session)
        house_request = CreateHouseRequest(**test_house_data)
        property_service.create_house(house_request, owner.id)
        
        response = client.get("/api/properties/owner/portfolio-stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_properties" in data
        assert "active_properties" in data
        assert "inactive_properties" in data
        assert "total_houses" in data
        assert "total_apartments" in data
        assert "total_for_sale" in data
        assert "total_for_rent" in data
        assert "total_portfolio_value" in data
        assert data["total_properties"] >= 1
    
    def test_get_my_properties_without_auth(self, client):
        """Test accessing my properties without authentication fails"""
        response = client.get("/api/properties/owner/my-properties")
        
        assert response.status_code in [401, 403]


class TestPropertyUpdate:
    """Test property update endpoints"""
    
    def test_update_property_success(self, authenticated_property_owner, created_property):
        """Test successful property update"""
        client = authenticated_property_owner["client"]
        property_id = str(created_property.id)
        
        update_data = {
            "description": "Updated description",
            "propertyValue": "600000.00"
        }
        
        response = client.put(f"/api/properties/{property_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == update_data["description"]
        assert data["propertyValue"] == update_data["propertyValue"]
    
    def test_update_property_not_found(self, authenticated_property_owner):
        """Test updating non-existent property returns 404"""
        client = authenticated_property_owner["client"]
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        # Use valid description (10+ chars) to pass validation
        update_data = {"description": "Updated description with enough characters"}
        response = client.put(f"/api/properties/{fake_id}", json=update_data)
        
        assert response.status_code == 404


class TestPropertyDeletion:
    """Test property deletion (deactivation) endpoints"""
    
    def test_deactivate_property_success(self, authenticated_property_owner, created_property):
        """Test successful property deactivation"""
        client = authenticated_property_owner["client"]
        property_id = str(created_property.id)
        
        response = client.delete(f"/api/properties/{property_id}")
        
        # DELETE returns 204 No Content (no response body)
        assert response.status_code == 204
    
    def test_reactivate_property_success(self, authenticated_property_owner, db_session, test_house_data):
        """Test successful property reactivation"""
        client = authenticated_property_owner["client"]
        owner = authenticated_property_owner["owner"]
        
        # Create a property for this owner
        from app.services.property_service import PropertyService
        from app.dtos.property_dto import CreateHouseRequest
        
        property_service = PropertyService(db_session)
        house_request = CreateHouseRequest(**test_house_data)
        property_obj = property_service.create_house(house_request, owner.id)
        property_id = str(property_obj.id)
        
        # Ensure property is committed
        db_session.commit()
        
        # First deactivate
        delete_response = client.delete(f"/api/properties/{property_id}")
        assert delete_response.status_code == 204
        
        # Then reactivate (endpoint is /activate, not /reactivate)
        response = client.post(f"/api/properties/{property_id}/activate")
        
        assert response.status_code == 200
        data = response.json()
        
        # Response is the property object, not a message
        assert data["id"] == property_id
        assert data["is_active"] is True


