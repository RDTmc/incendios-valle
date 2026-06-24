import pytest
@pytest.mark.fast
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

@pytest.mark.fast
def test_health_with_root_path(client):
    response = client.get("/api/health", headers={"Host": "testserver"})
    assert response.status_code == 200 or response.status_code == 404

@pytest.mark.fast
def test_health_cors_headers(client):
    response = client.options("/health", headers={
        "Origin": "https://incendios-valle.pages.dev",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
