import pytest
import os
os.environ['JWT_SECRET'] = 'test-secret-key'
os.environ['DB_PATH'] = '/tmp/test_incendios.db'

class TestDependencies:
    @pytest.mark.fast
    def test_sync_users_insert(self, client):
        response = client.post("/sync", json={
            "table": "users",
            "operation": "INSERT",
            "data": {"user_id": "u1", "email": "u1@test.com", "nombre": "User 1", "rol": "VECINO", "created_at": "2026-01-01"}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        result = response.json()["result"]
        # PG not configured in test, falls back gracefully
        assert result in ("pg not configured", "user synced")

    @pytest.mark.fast
    def test_sync_reports_insert(self, client):
        response = client.post("/sync", json={
            "table": "reports",
            "operation": "INSERT",
            "data": {"report_id": "r-sync", "user_id": "u1", "tipo": "FORESTAL", "latitud": "-33.45", "longitud": "-70.67", "estado": "ACTIVO"}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        result = response.json()["result"]
        assert result in ("pg not configured", "report synced")

    @pytest.mark.fast
    def test_sync_reports_modify(self, client):
        response = client.post("/sync", json={
            "table": "reports",
            "operation": "MODIFY",
            "data": {"reports_id": "r-sync2", "user_id": "u1", "tipo": "URBANO", "estado": "PENDIENTE"}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        result = response.json()["result"]
        assert result in ("pg not configured", "report synced")

    @pytest.mark.fast
    def test_sync_unknown_table(self, client):
        response = client.post("/sync", json={
            "table": "unknown_table",
            "operation": "INSERT",
            "data": {}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        # Without PG configured, sync_to_postgres returns "pg not configured"
        assert "pg not configured" in response.json()["result"]

    @pytest.mark.fast
    def test_sync_invalid_token_403(self, client):
        response = client.post("/sync", json={
            "table": "users",
            "operation": "INSERT",
            "data": {}
        }, headers={"x-sync-token": "wrong-token"})
        assert response.status_code == 403

    @pytest.mark.fast
    def test_sync_no_token_422(self, client):
        response = client.post("/sync", json={
            "table": "users", "operation": "INSERT", "data": {}
        })
        assert response.status_code == 422
