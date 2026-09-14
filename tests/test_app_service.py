from fastapi.testclient import TestClient

from app_service import main


def sample_application(application_id=1, active=True):
    return {
        "id": application_id,
        "name": "Test App",
        "package_name": "com.example.test",
        "category": "test",
        "active": active,
    }


def test_create_application(monkeypatch):
    monkeypatch.setattr(
        main.repository,
        "create_application",
        lambda data: sample_application(),
    )
    client = TestClient(main.app)

    response = client.post(
        "/applications",
        json={
            "name": "Test App",
            "package_name": "com.example.test",
            "category": "test",
        },
    )

    assert response.status_code == 201
    assert response.json()["package_name"] == "com.example.test"


def test_invalid_package_name_is_rejected():
    client = TestClient(main.app)

    response = client.post(
        "/applications",
        json={
            "name": "Bad App",
            "package_name": "not a package!",
            "category": "test",
        },
    )

    assert response.status_code == 422


def test_delete_deactivates_application(monkeypatch):
    monkeypatch.setattr(
        main.repository,
        "deactivate_application",
        lambda application_id: sample_application(application_id, False),
    )
    client = TestClient(main.app)

    response = client.delete("/applications/7")

    assert response.status_code == 200
    assert response.json()["active"] is False


def test_missing_application_returns_404(monkeypatch):
    monkeypatch.setattr(
        main.repository,
        "get_application",
        lambda application_id: None,
    )
    client = TestClient(main.app)

    response = client.get("/applications/999")

    assert response.status_code == 404
