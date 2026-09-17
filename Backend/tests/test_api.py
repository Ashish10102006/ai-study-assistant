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
