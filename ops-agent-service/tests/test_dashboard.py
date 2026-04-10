from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_homepage_is_project_specific():
    response = client.get("/")

    assert response.status_code == 200
    assert "设备网关运维诊断台" in response.text
    assert "/api/docs" in response.text


def test_swagger_docs_moved_to_api_docs():
    response = client.get("/api/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
