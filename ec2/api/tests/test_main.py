import pytest
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


class TestMainCore:
    @pytest.mark.fast
    def test_encode_geohash(self):
        from main import encode_geohash
        geohash = encode_geohash(-33.45, -70.67)
        assert isinstance(geohash, str)
        assert "-" in geohash

    @pytest.mark.e2e
    def test_get_dashboard_stats_with_data(self, client, mock_dynamodb):
        import jwt
        import datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'test-user',
            'email': 'test@test.com',
            'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert "by_estado" in data
        assert "by_tipo" in data

    @pytest.mark.fast
    def test_focos_activos_with_valid_data(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {
            'Items': [
                {'report_id': 'r1', 'reports_id': 'r1', 'latitud': '-33.45', 'longitud': '-70.67',
                 'estado': 'ACTIVO', 'tipo': 'FORESTAL', 'descripcion': 'Test fire',
                 'foto_url': 'https://example.com/foto.jpg', 'created_at': '2026-06-01T00:00:00'},
            ]
        }
        response = client.get("/focos-activos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["lat"] == -33.45
        assert data[0]["lng"] == -70.67
        assert data[0]["foto_url"] == "https://example.com/foto.jpg"

    @pytest.mark.fast
    def test_focos_activos_no_data(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {'Items': []}
        response = client.get("/focos-activos")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.fast
    def test_trigger_success(self, client):
        with patch('main.fetch_ciren_data') as mock_fetch:
            mock_fetch.return_value = None
            response = client.post(
                "/v1/external-reports/trigger",
                headers={"Authorization": "Bearer test-sync-token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "triggered"

    @pytest.mark.e2e
    def test_conaf_duplicate_returns_inserted(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Dup", "latitud": -33.45, "longitud": -70.67,
            "fh_inicio": "2026-01-01"
        }, headers={"Authorization": "Bearer test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "inserted"


class TestMainBackground:
    @pytest.mark.e2e
    async def test_fetch_ciren_data_success(self, db_connection):
        from main import fetch_ciren_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(return_value={
            "features": [{
                "attributes": {"nombre": "Test Fire", "region": "Valparaíso", "comuna": "Viña",
                              "provincia": "Valparaíso", "superficie": 10.5, "causa_gene": "Intencional",
                              "fh_inicio": "2026-01-01", "fh_extinci": "2026-01-05", "temporada": "2025-2026"},
                "geometry": {"x": -71.55, "y": -33.05}
            }]
        })
        with patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker):
            await fetch_ciren_data()

    @pytest.mark.e2e
    async def test_fetch_ciren_data_skips_no_geometry(self, db_connection):
        from main import fetch_ciren_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(return_value={
            "features": [{"attributes": {"nombre": "No Geo"}, "geometry": {}}]
        })
        with patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker):
            await fetch_ciren_data()

    @pytest.mark.e2e
    async def test_fetch_ciren_data_circuit_breaker_error(self, db_connection):
        from main import fetch_ciren_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(side_effect=RuntimeError("CIREN API down"))
        with patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker):
            await fetch_ciren_data()

    @pytest.mark.e2e
    async def test_fetch_firms_no_api_key(self, db_connection):
        from main import fetch_firms_hotspots
        with patch.dict(os.environ, {'FIRMS_API_KEY': ''}):
            await fetch_firms_hotspots()

    @pytest.mark.e2e
    async def test_fetch_firms_success(self, db_connection):
        from main import fetch_firms_hotspots
        csv_data = "latitude,longitude,brightness,frp,confidence,satellite,acq_date,acq_time,daynight\n-33.05,-71.55,350.5,100.2,high,NPP,2026-06-01,1234,D\n"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = csv_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(return_value=mock_response)
        with patch.dict(os.environ, {'FIRMS_API_KEY': 'test-key'}), \
             patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker):
            await fetch_firms_hotspots()

    @pytest.mark.e2e
    async def test_fetch_weather_no_api_key(self, db_connection):
        from main import fetch_weather_data
        with patch.dict(os.environ, {'OWM_API_KEY': ''}):
            await fetch_weather_data()

    @pytest.mark.e2e
    async def test_fetch_weather_success(self, db_connection):
        from main import fetch_weather_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(return_value={
            "main": {"temp": 25.5, "humidity": 60, "pressure": 1013},
            "wind": {"speed": 5.2, "deg": 180},
            "weather": [{"description": "clear sky"}]
        })
        with patch.dict(os.environ, {'OWM_API_KEY': 'test-key'}), \
             patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker):
            await fetch_weather_data()


class TestMainEdgeCases:
    @pytest.mark.fast
    def test_dashboard_stats_db_error(self):
        from main import app
        from fastapi.testclient import TestClient
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'u1', 'email': 't@t.cl', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        with patch('database_pg.query_pg_first', return_value=None):
            tc = TestClient(app, raise_server_exceptions=False)
            response = tc.get("/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["by_estado"] == {}
            assert data["by_tipo"] == {}

    @pytest.mark.fast
    def test_focos_activos_skips_bad_coords(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {
            'Items': [
                {'reports_id': 'r1', 'latitud': 'invalid', 'longitud': '-70.67', 'estado': 'ACTIVO',
                 'tipo': 'FORESTAL', 'descripcion': '', 'foto_url': '', 'created_at': ''},
                {'reports_id': 'r2', 'latitud': '0', 'longitud': '0', 'estado': 'ACTIVO',
                 'tipo': 'FORESTAL', 'descripcion': '', 'foto_url': '', 'created_at': ''},
                {'reports_id': 'r3', 'latitud': '-33.45', 'longitud': '-70.67', 'estado': 'VALIDADO',
                 'tipo': 'URBANO', 'descripcion': 'Real', 'foto_url': '', 'created_at': '2026-01-01'},
            ]
        }
        response = client.get("/focos-activos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "r3"

    @pytest.mark.fast
    def test_focos_activos_db_error(self, client):
        with patch('main.get_report_repository', side_effect=Exception("DynamoDB down")):
            response = client.get("/focos-activos")
            assert response.status_code == 500

    @pytest.mark.fast
    def test_receive_external_report_invalid_token(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CONAF", "nombre": "Test", "latitud": -33.45, "longitud": -70.67
        }, headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    @pytest.mark.fast
    def test_receive_external_report_no_auth_header(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CONAF", "nombre": "Test", "latitud": -33.45, "longitud": -70.67
        })
        assert response.status_code == 403

    @pytest.mark.fast
    def test_trigger_external_fetch_invalid_token(self, client):
        response = client.post("/v1/external-reports/trigger",
                               headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    @pytest.mark.fast
    def test_trigger_external_fetch_no_auth(self, client):
        response = client.post("/v1/external-reports/trigger")
        assert response.status_code == 403

    @pytest.mark.fast
    def test_upload_report_image_http_exception_passthrough(self, client, mock_lambda_service):
        from main import upload_report_image
        mock_file = MagicMock()
        mock_file.content_type = "text/plain"
        with pytest.raises(Exception):
            upload_report_image(file=mock_file)
