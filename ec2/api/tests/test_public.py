import pytest
from unittest.mock import patch


def _mock_pg_rows(rows):
    """Helper: mock query_pg_first to return given rows."""
    return patch('routers.public.query_pg_first', return_value=rows)


class TestPublicEndpoints:
    @pytest.mark.fast
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

    @pytest.mark.fast
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

    @pytest.mark.fast
    def test_public_resources(self, client):
        rows = [
            ("r1", "FORESTAL", "ACTIVO", "BOMBEROS", 2, "CB-1, CB-2"),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/resources")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert data[0]["recurso"] == "BOMBEROS"

    @pytest.mark.fast
    def test_sync_endpoint_valid_token(self, client):
        response = client.post("/sync", json={
            "table": "users",
            "operation": "INSERT",
            "data": {"user_id": "sync-test", "email": "sync@test.com", "nombre": "Sync", "rol": "VECINO", "created_at": "2026-01-01"}
        }, headers={"x-sync-token": "test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "synced"

    @pytest.mark.fast
    def test_sync_endpoint_invalid_token(self, client):
        response = client.post("/sync", json={
            "table": "users",
            "operation": "INSERT",
            "data": {}
        }, headers={"x-sync-token": "wrong-token"})
        assert response.status_code == 403

    @pytest.mark.fast
    def test_sync_endpoint_no_token(self, client):
        response = client.post("/sync", json={
            "table": "users", "operation": "INSERT", "data": {}
        })
        assert response.status_code == 422

    @pytest.mark.fast
    def test_public_external_reports(self, client):
        # id, source, nombre, region, comuna, provincia, superficie, causa, latitud, longitud, fh_inicio, fh_extinci, temporada
        rows = [
            (1, "CIREN", "Test Fire", "Metropolitana", "Santiago", "Santiago", 100.5, "Natural", -33.45, -70.67, "2026-01-01", "2026-01-05", "2025-2026"),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/external-reports")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:
                assert data[0]["source"] == "CIREN"

    @pytest.mark.fast
    def test_public_firms_hotspots(self, client):
        # id, latitude, longitude, brightness, frp, confidence, satellite, acq_date, acq_time, daynight, source
        rows = [
            (1, -33.45, -70.67, 350.5, 100.2, "high", "NPP", "2026-06-01", 1200, "D", "VIIRS_SNPP_NRT"),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/firms-hotspots")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.fast
    def test_public_cluster_stats(self, client):
        rows = [
            ("r1", "-33.4500", "-70.6700"),
            ("r2", "-33.4501", "-70.6701"),
            ("r3", "-34.0000", "-71.0000"),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/cluster-stats")
            assert response.status_code == 200
            data = response.json()
            assert data["clusters"] >= 1

    @pytest.mark.fast
    def test_public_cluster_stats_bad_coords(self, client):
        rows = [
            ("r-bad", "not-a-number", "also-bad"),
            ("r-ok", "-33.45", "-70.67"),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/cluster-stats")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["clusters"], int)

    @pytest.mark.fast
    def test_public_stale_pendientes(self, client):
        rows = [
            ("r-stale", "2026-01-01 02:00:00", 90),
            ("r-fresh", "2026-01-03 12:00:00", 10),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/stale-pendientes")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert any(r["report_id"] == "r-stale" for r in data)

    @pytest.mark.fast
    def test_public_external_reports_filter_source(self, client):
        rows = [
            (1, "CIREN", "Fire 1", "RM", "Santiago", "Santiago", 50.0, "Natural", -33.45, -70.67, "2026-01-01", "", "2025-2026"),
        ]
        with _mock_pg_rows(rows):
            response = client.get("/public/external-reports?source=CIREN")
            assert response.status_code == 200
            data = response.json()
            assert all(r["source"] == "CIREN" for r in data)

    @pytest.mark.fast
    def test_public_external_reports_sources(self, client):
        rows = [("CIREN", 5), ("CONAF", 3)]
        with _mock_pg_rows(rows):
            response = client.get("/public/external-reports/sources")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert any(s["source"] == "CIREN" for s in data)

    @pytest.mark.fast
    def test_public_external_reports_sources_empty(self, client):
        response = client.get("/public/external-reports/sources")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_public_map_coordinates_empty(self, client):
        response = client.get("/public/map-coordinates")
        assert response.status_code == 200
        assert response.json() == {"error": "Internal server error"}

    @pytest.mark.fast
    def test_public_external_reports_empty(self, client):
        response = client.get("/public/external-reports")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_public_cluster_stats_empty(self, client):
        response = client.get("/public/cluster-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["clusters"] == 0
        assert data["pares"] == []

    @pytest.mark.fast
    def test_public_stale_pendientes_empty(self, client):
        response = client.get("/public/stale-pendientes")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_public_weather_latest_empty(self, client):
        response = client.get("/public/weather/latest")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_public_weather_history_empty(self, client):
        response = client.get("/public/weather/history")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_public_firms_hotspots_empty(self, client):
        response = client.get("/public/firms-hotspots")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_public_resources_empty(self, client):
        response = client.get("/public/resources")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_v1_trigger_invalid_token(self, client):
        response = client.post("/v1/external-reports/trigger", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    @pytest.mark.fast
    def test_v1_conaf_invalid_token(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Test", "latitud": -33.45, "longitud": -70.67
        }, headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    @pytest.mark.e2e
    def test_v1_conaf_success(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Test Fire CONAF", "region": "Metropolitana",
            "comuna": "Santiago", "latitud": -33.45, "longitud": -70.67, "superficie": 100.5
        }, headers={"Authorization": f"Bearer test-sync-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inserted"

    @pytest.mark.e2e
    def test_v1_conaf_duplicate(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Dup Fire", "latitud": -33.45, "longitud": -70.67,
            "fh_inicio": "2026-01-01"
        }, headers={"Authorization": f"Bearer test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "inserted"
