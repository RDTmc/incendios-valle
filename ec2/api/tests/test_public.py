import pytest

class TestPublicEndpoints:
    def test_focos_activos(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {
            'Items': [
                {'report_id': 'r1', 'reports_id': 'r1', 'latitud': '-33.45', 'longitud': '-70.67',
                 'estado': 'ACTIVO', 'tipo': 'FORESTAL', 'descripcion': 'Fire',
                 'foto_url': '', 'created_at': '2026-01-01T00:00:00'},
            ]
        }
        response = client.get("/focos-activos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["lat"] == -33.45

    def test_focos_activos_geofence(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {
            'Items': [
                {'report_id': 'r1', 'reports_id': 'r1', 'latitud': '0', 'longitud': '0',
                 'estado': 'ACTIVO', 'tipo': 'FORESTAL', 'descripcion': '', 'foto_url': '', 'created_at': ''},
            ]
        }
        response = client.get("/focos-activos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_public_resources(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO reports (report_id, tipo, estado, created_at) VALUES ('r1', 'FORESTAL', 'ACTIVO', datetime('now'))")
        cursor.execute("INSERT INTO incident_resources (report_id, tipo_recurso, cantidad, unidad) VALUES ('r1', 'BOMBEROS', 2, 'CB-1, CB-2')")
        db_connection.commit()
        response = client.get("/public/resources")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["recurso"] == "BOMBEROS"

    def test_sync_endpoint_valid_token(self, client):
        response = client.post("/sync", json={
            "table": "users",
            "operation": "INSERT",
            "data": {"user_id": "sync-test", "email": "sync@test.com", "nombre": "Sync", "rol": "VECINO", "created_at": "2026-01-01"}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "synced"

    def test_sync_endpoint_invalid_token(self, client):
        response = client.post("/sync", json={
            "table": "users",
            "operation": "INSERT",
            "data": {}
        }, headers={"x-sync-token": "wrong-token"})
        assert response.status_code == 403

    def test_sync_endpoint_no_token(self, client):
        response = client.post("/sync", json={
            "table": "users", "operation": "INSERT", "data": {}
        })
        assert response.status_code == 422

    def test_public_external_reports(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO external_reports (source, nombre, region, latitud, longitud, fh_inicio) VALUES ('CIREN', 'Test Fire', 'Metropolitana', -33.45, -70.67, '2026-01-01')")
        db_connection.commit()
        response = client.get("/public/external-reports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_public_firms_hotspots(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO firms_hotspots (latitude, longitude, brightness, acq_date, acq_time, satellite) VALUES (-33.45, -70.67, 350.5, '2026-06-01', 1200, 'NPP')")
        db_connection.commit()
        response = client.get("/public/firms-hotspots")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_public_cluster_stats(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO reports (report_id, latitud, longitud, created_at) VALUES ('r1', '-33.4500', '-70.6700', datetime('now'))")
        cursor.execute("INSERT OR IGNORE INTO reports (report_id, latitud, longitud, created_at) VALUES ('r2', '-33.4501', '-70.6701', datetime('now'))")
        cursor.execute("INSERT OR IGNORE INTO reports (report_id, latitud, longitud, created_at) VALUES ('r3', '-34.0000', '-71.0000', datetime('now'))")
        db_connection.commit()
        response = client.get("/public/cluster-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["clusters"] >= 1

    def test_public_stale_pendientes(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO reports (report_id, estado, created_at) VALUES ('r-stale', 'PENDIENTE', datetime('now', '-2 hours'))")
        cursor.execute("INSERT OR IGNORE INTO reports (report_id, estado, created_at) VALUES ('r-fresh', 'PENDIENTE', datetime('now'))")
        db_connection.commit()
        response = client.get("/public/stale-pendientes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(r["report_id"] == "r-stale" for r in data)

    def test_public_external_reports_sources(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO external_reports (source, nombre, latitud, longitud) VALUES ('CIREN', 'Fire 1', -33.45, -70.67)")
        db_connection.commit()
        response = client.get("/public/external-reports/sources")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(s["source"] == "CIREN" for s in data)

    def test_public_weather_latest(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO weather_readings (lat, lon, region, temperature, humidity, wind_speed) VALUES (-33.05, -71.62, 'Valparaíso', 25.5, 60, 12.3)")
        db_connection.commit()
        response = client.get("/public/weather/latest")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "temperature" in data[0]

    def test_public_weather_history(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO weather_readings (lat, lon, region, temperature, humidity, wind_speed) VALUES (-33.05, -71.62, 'Valparaíso', 25.5, 60, 12.3)")
        db_connection.commit()
        response = client.get("/public/weather/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "temperature" in data[0]

    def test_public_weather_history_default_limit(self, client, db_connection):
        response = client.get("/public/weather/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_v1_trigger_invalid_token(self, client):
        response = client.post("/v1/external-reports/trigger", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    def test_v1_conaf_invalid_token(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Test", "latitud": -33.45, "longitud": -70.67
        }, headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    def test_v1_conaf_success(self, client, db_connection):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Test Fire CONAF", "region": "Metropolitana",
            "comuna": "Santiago", "latitud": -33.45, "longitud": -70.67, "superficie": 100.5
        }, headers={"Authorization": f"Bearer test-sync-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inserted"

    def test_v1_conaf_duplicate(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO external_reports (source, nombre, latitud, longitud, fh_inicio) VALUES ('CIREN', 'Dup Fire', -33.45, -70.67, '2026-01-01')")
        db_connection.commit()
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Dup Fire", "latitud": -33.45, "longitud": -70.67,
            "fh_inicio": "2026-01-01"
        }, headers={"Authorization": f"Bearer test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "inserted"
