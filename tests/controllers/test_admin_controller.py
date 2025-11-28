# tests/controllers/test_admin_controller.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.property import Property
from app.models.visit import Visit
from app.models.proposal import Proposal, ProposalStatusEnum
from app.models.favorite import Favorite
from app.models.property_image import PropertyImage
from app.services.property_service import PropertyService
from app.dtos.property_dto import CreateHouseRequest


def test_permanently_delete_property_as_admin(
    db_session: Session,
    authenticated_admin: dict,
    mock_auth_property_owner: dict,
    mock_auth_user: dict,
    test_house_data: dict,
):
    """
    Test that an admin can permanently delete a property and all its related data.
    """
    # ARRANGE
    client = authenticated_admin["client"]
    owner_user = mock_auth_property_owner
    regular_user = mock_auth_user

    # 1. Create a property with an owner
    prop_service = PropertyService(db_session)
    house_request = CreateHouseRequest(**test_house_data)
    created_prop = prop_service.create_house(house_request, owner_user.id)
    property_id = created_prop.id

    # 2. Create related data for the property
    # Visit
    visit = Visit(
        id=uuid4(),
        idProperty=property_id,
        idUser=regular_user.id,
        visitDate=datetime.utcnow() + timedelta(days=5),
        isVisitCompleted=False,
        cancelled=False,
    )
    db_session.add(visit)

    # Proposal
    proposal = Proposal(
        id=uuid4(),
        idProperty=property_id,
        idUser=regular_user.id,
        status=ProposalStatusEnum.PENDING,
        proposalValue=created_prop.propertyValue * Decimal("0.95"),
    )
    db_session.add(proposal)

    # Favorite
    favorite = Favorite(id=uuid4(), idProperty=property_id, idUser=regular_user.id)
    db_session.add(favorite)
    db_session.commit()

    # Verify everything exists before deletion
    assert (
        db_session.query(Property).filter(Property.id == property_id).first()
        is not None
    )
    assert (
        db_session.query(Visit).filter(Visit.idProperty == property_id).first()
        is not None
    )
    assert (
        db_session.query(Proposal).filter(Proposal.idProperty == property_id).first()
        is not None
    )
    assert (
        db_session.query(Favorite).filter(Favorite.idProperty == property_id).first()
        is not None
    )
    assert (
        db_session.query(PropertyImage)
        .filter(PropertyImage.property_id == property_id)
        .first()
        is not None
    )

    # ACT
    response = client.delete(f"/api/admin/properties/{property_id}/permanent")

    # ASSERT
    assert response.status_code == 204

    # Verify that the property and all related data are gone
    db_session.expire_all()  # Ensure fresh data is loaded from db
    assert (
        db_session.query(Property).filter(Property.id == property_id).first() is None
    ), "Property should be deleted"
    assert (
        db_session.query(Visit).filter(Visit.idProperty == property_id).first() is None
    ), "Visits should be deleted"
    assert (
        db_session.query(Proposal).filter(Proposal.idProperty == property_id).first()
        is None
    ), "Proposals should be deleted"
    assert (
        db_session.query(Favorite).filter(Favorite.idProperty == property_id).first()
        is None
    ), "Favorites should be deleted"
    assert (
        db_session.query(PropertyImage)
        .filter(PropertyImage.property_id == property_id)
        .count()
        == 0
    ), "Images should be deleted"


def test_permanently_delete_property_as_non_admin(
    client: TestClient,
    created_property: Property,
    authenticated_user: dict,
):
    """
    Test that a non-admin user cannot permanently delete a property.
    """
    # ARRANGE
    property_id = created_property.id

    # ACT
    response = client.delete(f"/api/admin/properties/{property_id}/permanent")

    # ASSERT
    assert response.status_code == 403  # Forbidden
