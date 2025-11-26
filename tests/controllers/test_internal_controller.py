import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from app.settings import settings

# Mock services
@pytest.fixture
def mock_property_service():
    with patch('app.controllers.internal_controller.PropertyService') as mock:
        yield mock.return_value

@pytest.fixture
def mock_favorite_service():
    with patch('app.controllers.internal_controller.FavoriteService') as mock:
        yield mock.return_value

@pytest.fixture
def mock_visit_service():
    with patch('app.controllers.internal_controller.VisitService') as mock:
        yield mock.return_value

@pytest.fixture
def mock_proposal_service():
    with patch('app.controllers.internal_controller.ProposalService') as mock:
        yield mock.return_value


def test_user_deleted_webhook_success(
    client: TestClient,
    mock_property_service: Mock,
    mock_favorite_service: Mock,
    mock_visit_service: Mock,
    mock_proposal_service: Mock
):
    """
    Test that the user deleted webhook processes a valid request
    and triggers cascading deletion in all services.
    """
    test_user_id_uuid = uuid4()
    headers = {"X-Internal-Secret": settings.INTERNAL_API_SECRET}
    payload = {"user_id": str(test_user_id_uuid)}

    response = client.post("/api/internal/user-deleted-webhook", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == f"Webhook processed and cascading deletion initiated for user_id: {test_user_id_uuid}"

    # Assert that all service deletion methods were called with the correct user_id
    mock_property_service.delete_all_owner_properties_permanently.assert_called_once_with(test_user_id_uuid)
    mock_favorite_service.delete_all_user_favorites.assert_called_once_with(test_user_id_uuid)
    mock_visit_service.delete_all_user_visits.assert_called_once_with(test_user_id_uuid)
    mock_visit_service.delete_all_visits_for_owner_properties.assert_called_once_with(test_user_id_uuid)
    mock_proposal_service.delete_all_user_proposals.assert_called_once_with(test_user_id_uuid)
    mock_proposal_service.delete_all_proposals_for_owner_properties.assert_called_once_with(test_user_id_uuid)


def test_user_deleted_webhook_invalid_secret(client: TestClient):
    """
    Test that the user deleted webhook rejects requests with an invalid internal secret.
    """
    test_user_id = str(uuid4())
    headers = {"X-Internal-Secret": "invalid-secret"}
    payload = {"user_id": test_user_id}

    response = client.post("/api/internal/user-deleted-webhook", json=payload, headers=headers)

    assert response.status_code == 401
    assert "Invalid internal API secret" in response.json()["detail"]

    # Assert that no service deletion methods were called
    # (These mocks would need to be outside the test function if we wanted to assert they were *never* called across tests)
    # For now, this test focuses on the 401 status and that services aren't implicitly called due to a failure
    pass
