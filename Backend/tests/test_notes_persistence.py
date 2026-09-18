import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.storage_service import get_storage_service

client = TestClient(app)

USER_A_HEADERS = {"Authorization": "Bearer student-token-user-a"}
USER_B_HEADERS = {"Authorization": "Bearer student-token-user-b"}


def test_saved_notes_crud_and_tenant_isolation():
    """Verify saved notes creation, listing, retrieval, update, deletion, and strict multi-tenant isolation."""
    # 1. User A creates a note
    create_payload = {
        "topic": "AVL Trees and Rebalancing",
        "subject": "Data Structures",
        "content": "# AVL Trees\nAn AVL tree is a self-balancing binary search tree where the difference between heights of left and right subtrees cannot exceed 1."
    }
    res_a = client.post("/api/study/saved-notes", json=create_payload, headers=USER_A_HEADERS)
    assert res_a.status_code == 200, res_a.text
    note_a = res_a.json()
    assert note_a["topic"] == "AVL Trees and Rebalancing"
    assert "id" in note_a
    note_a_id = note_a["id"]

    # 2. User A retrieves the note
    get_res = client.get(f"/api/study/saved-notes/{note_a_id}", headers=USER_A_HEADERS)
    assert get_res.status_code == 200
    assert get_res.json()["content"] == create_payload["content"]

    # 3. User A lists notes
    list_res_a = client.get("/api/study/saved-notes", headers=USER_A_HEADERS)
    assert list_res_a.status_code == 200
    notes_a = list_res_a.json()
    assert any(n["id"] == note_a_id for n in notes_a)

    # 4. TENANT ISOLATION: User B CANNOT see or access User A's note
    get_res_b = client.get(f"/api/study/saved-notes/{note_a_id}", headers=USER_B_HEADERS)
    assert get_res_b.status_code == 404, "User B should not be able to access User A's saved note"

    list_res_b = client.get("/api/study/saved-notes", headers=USER_B_HEADERS)
    assert list_res_b.status_code == 200
    notes_b = list_res_b.json()
    assert not any(n["id"] == note_a_id for n in notes_b), "User B's notes list leaked User A's note"

    # 5. TENANT ISOLATION: User B CANNOT update or delete User A's note
    patch_res_b = client.patch(f"/api/study/saved-notes/{note_a_id}", json={"topic": "Hacked"}, headers=USER_B_HEADERS)
    assert patch_res_b.status_code == 404

    del_res_b = client.delete(f"/api/study/saved-notes/{note_a_id}", headers=USER_B_HEADERS)
    assert del_res_b.status_code == 404

    # 6. User A updates the note
    patch_res_a = client.patch(
        f"/api/study/saved-notes/{note_a_id}",
        json={"topic": "AVL Trees (Updated)", "content": "# Updated Content"},
        headers=USER_A_HEADERS
    )
    assert patch_res_a.status_code == 200
    assert patch_res_a.json()["topic"] == "AVL Trees (Updated)"

    # 7. User A deletes the note
    del_res_a = client.delete(f"/api/study/saved-notes/{note_a_id}", headers=USER_A_HEADERS)
    assert del_res_a.status_code == 200

    # 8. Note is gone for User A
    get_after_del = client.get(f"/api/study/saved-notes/{note_a_id}", headers=USER_A_HEADERS)
    assert get_after_del.status_code == 404


def test_saved_notes_validation_empty_inputs():
    """Verify that empty inputs are rejected cleanly."""
    bad_payload = {"topic": "   ", "content": ""}
    res = client.post("/api/study/saved-notes", json=bad_payload, headers=USER_A_HEADERS)
    assert res.status_code in [400, 422]
