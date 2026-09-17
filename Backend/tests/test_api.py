import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "AI STUDY ASSISTANT"
    assert data["status"] == "online"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "AI STUDY ASSISTANT"
    assert "services" in data


def test_conversations_flow():
    # Create conversation
    create_res = client.post("/api/conversations", json={
        "title": "Data Structures Trees",
        "subject": "Computer Science",
        "topic": "Binary Search Trees"
    })
    assert create_res.status_code == 200
    conv_data = create_res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Data Structures Trees"

    # Fetch conversation
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == conv_id

    # List conversations
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    assert any(c["id"] == conv_id for c in list_res.json())

    # Delete conversation
    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200


def test_profile_creation_and_retrieval():
    """Verify profile retrieval works cleanly with guest/auth headers."""
    res = client.get("/api/profile", headers={"X-Guest-Id": "guest_test_profile_user"})
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data
    assert "email" in data
    assert "interests" in data


def test_storage_profile_with_google_metadata():
    """Verify storage service stores Google metadata (name, avatar) correctly."""
    from app.services.storage_service import get_storage_service
    storage = get_storage_service()

    google_uid = "google_user_test_uuid_9999"
    email = "scholar.google@university.edu"
    full_name = "Dr. Jane Scholar"
    avatar = "https://lh3.googleusercontent.com/a/test_avatar"

    prof = storage.get_or_create_profile(
        user_id=google_uid,
        email=email,
        full_name=full_name,
        profile_image=avatar
    )

    assert prof["user_id"] == google_uid
    assert prof["full_name"] == full_name
    assert prof["profile_image"] == avatar
    assert prof["email"] == email
