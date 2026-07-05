import pytest
from unittest.mock import MagicMock

class TestReports:
    @pytest.mark.fast
    def test_create_report_authenticated(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.put_item.return_value = {}
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'test-user',
            'email': 'test@example.com',
            'rol': 'VECINO',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.post("/reports", json={
            "user_id": "test-user",
            "tipo": "FORESTAL",
            "latitud": -33.45,
            "longitud": -70.67,
            "descripcion": "Test report"
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "PENDIENTE"
        assert "report_id" in data

    @pytest.mark.fast
    def test_create_report_anonymous(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.put_item.return_value = {}
        response = client.post("/reportar", json={
            "tipo": "URBANO",
            "latitud": -33.45,
            "longitud": -70.67,
            "descripcion": "Anonymous report",
            "device_id": "test-device-001"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "PENDIENTE"

    @pytest.mark.fast
    def test_create_report_anonymous_no_device_id(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        response = client.post("/reportar", json={
            "tipo": "URBANO",
            "latitud": -33.45,
            "longitud": -70.67,
            "descripcion": "No device"
        })
        assert response.status_code == 400
        assert "device_id" in response.json()["detail"]

    @pytest.mark.fast
    def test_list_reports_authenticated(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {
            'Items': [
                {'reports_id': 'r1', 'user_id': 'u1', 'tipo': 'FORESTAL', 'estado': 'ACTIVO',
                 'latitud': '-33.45', 'longitud': '-70.67', 'created_at': '2026-01-01T00:00:00',
                 'descripcion': 'Fire 1'}
            ]
        }
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user',
            'email': 'admin@example.com',
            'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/reports", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["report_id"] == "r1"

    @pytest.mark.fast
    def test_get_report_by_id(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.get_item.return_value = {
            'Item': {'reports_id': 'r1', 'user_id': 'u1', 'tipo': 'FORESTAL',
                     'estado': 'PENDIENTE', 'latitud': '-33.45', 'longitud': '-70.67'}
        }
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/reports/r1", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert response.json()["report_id"] == "r1"

    @pytest.mark.fast
    def test_get_report_not_found(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.get_item.return_value = {}
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/reports/nonexistent-id", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 404

    @pytest.mark.fast
    def test_update_report_status(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.update_item.return_value = {}
        mock_reports.get_item.return_value = {
            'Item': {'reports_id': 'r1', 'estado': 'ACTIVO'}
        }
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.put("/reports/r1?estado=CONTROLADO", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert response.json()["estado"] == "ACTIVO"

    @pytest.mark.e2e
    def test_public_dashboard_stats(self, client):
        response = client.get("/public/dashboard-stats")
        assert response.status_code == 200
        data = response.json()
        assert "focos_activos" in data

    @pytest.mark.e2e
    def test_public_map_coordinates(self, client):
        response = client.get("/public/map-coordinates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.fast
    def test_dashboard_stats_authenticated(self, client):
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/dashboard/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_estado" in data
        assert "by_tipo" in data

    @pytest.mark.fast
    def test_dashboard_stats_unauthorized(self, client):
        response = client.get("/dashboard/stats")
        assert response.status_code == 401

    @pytest.mark.e2e
    def test_sync_reports_table(self, client):
        response = client.post("/sync", json={
            "table": "reports",
            "operation": "INSERT",
            "data": {"report_id": "sync-r1", "user_id": "u1", "tipo": "FORESTAL",
                     "latitud": "-33.45", "longitud": "-70.67", "estado": "ACTIVO",
                     "descripcion": "Sync test", "created_at": "2026-01-01", "updated_at": "2026-01-01"}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "synced"

    @pytest.mark.fast
    def test_sync_unknown_table(self, client):
        response = client.post("/sync", json={
            "table": "unknown",
            "operation": "INSERT",
            "data": {}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        assert "pg not configured" in response.json()["result"]

    @pytest.mark.fast
    def test_list_reports_by_user(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.query.return_value = {
            'Items': [
                {'reports_id': 'u1-r1', 'user_id': 'user1', 'tipo': 'FORESTAL', 'estado': 'ACTIVO',
                 'latitud': '-33.45', 'longitud': '-70.67', 'created_at': '2026-01-01', 'descripcion': 'My report'}
            ]
        }
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/reports?user_id=user1", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["report_id"] == "u1-r1"

    @pytest.mark.fast
    def test_create_report_db_error(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.put_item.side_effect = Exception("DynamoDB error")
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'test-user', 'email': 'test@test.com', 'rol': 'VECINO',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.post("/reports", json={
            "user_id": "test-user", "tipo": "FORESTAL",
            "latitud": -33.45, "longitud": -70.67, "descripcion": "Error test"
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 500

    @pytest.mark.fast
    def test_list_reports_db_error(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.side_effect = Exception("DynamoDB error")
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/reports", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 500

    @pytest.mark.fast
    def test_get_report_db_error(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.get_item.side_effect = Exception("DynamoDB error")
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/reports/r1", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 500

    # ── B6: Admin cambiar estado de reporte ──

    @pytest.mark.e2e
    def test_admin_update_report_status_success(self, client, mock_dynamodb):
        mock_users, mock_reports = mock_dynamodb

        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')

        response = client.put("/admin/reports/admin-report-1/status", json={
            "estado": "ACTIVO"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["estado"] == "ACTIVO"

    @pytest.mark.fast
    def test_admin_update_report_status_unauthorized(self, client):
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'vecino-user', 'email': 'vecino@test.com', 'rol': 'VECINO',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')

        response = client.put("/admin/reports/nonexistent/status", json={
            "estado": "ACTIVO"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403
        assert "ADMIN" in response.json()["detail"]

    @pytest.mark.e2e
    def test_admin_update_report_status_not_found(self, client):
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')

        response = client.put("/admin/reports/nonexistent-id/status", json={
            "estado": "ACTIVO"
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 404
        assert "Reporte no encontrado" in response.json()["detail"]

    @pytest.mark.fast
    def test_update_report_db_error(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.update_item.side_effect = Exception("DynamoDB error")
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.put("/reports/r1?estado=CONTROLADO", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 500
