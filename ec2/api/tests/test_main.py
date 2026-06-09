import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from pathlib import Path


class TestMainCore:
    def test_encode_geohash(self):
        from main import encode_geohash
        geohash = encode_geohash(-33.45, -70.67)
        assert isinstance(geohash, str)
        assert "-" in geohash

    def test_get_dashboard_stats_with_data(self, client, mock_dynamodb, db_connection):
        import jwt
        import datetime
        from datetime import timezone
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO reports (report_id, tipo, estado, created_at) VALUES ('r1', 'FORESTAL', 'ACTIVO', datetime('now'))")
        cursor.execute("INSERT INTO reports (report_id, tipo, estado, created_at) VALUES ('r2', 'URBANO', 'PENDIENTE', datetime('now'))")
        db_connection.commit()
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

    def test_focos_activos_no_data(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {'Items': []}
        response = client.get("/focos-activos")
        assert response.status_code == 200
        assert response.json() == []

    def test_backup_sqlite_to_s3(self):
        from main import backup_sqlite_to_s3
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            backup_sqlite_to_s3()
            assert mock_run.call_count == 2

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

    def test_restore_sqlite_from_s3_when_empty(self, client, db_connection):
        from main import restore_sqlite_from_s3
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM external_reports")
        db_connection.commit()
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            restore_sqlite_from_s3()
            mock_run.assert_called_once()

    def test_restore_sqlite_from_s3_when_has_data(self, client, db_connection):
        from main import restore_sqlite_from_s3
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO external_reports (source, nombre, latitud, longitud) VALUES ('CIREN', 'Test', -33.45, -70.67)")
        db_connection.commit()
        with patch('subprocess.run') as mock_run:
            restore_sqlite_from_s3()
            mock_run.assert_not_called()

    def test_export_seed_empty(self, client, db_connection):
        from main import export_external_reports_seed
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM external_reports")
        db_connection.commit()
        with patch('builtins.open', mock_open()) as mock_file:
            export_external_reports_seed()
            mock_file.assert_not_called()

    def test_load_seed_no_file(self):
        from main import load_seed_if_empty
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            load_seed_if_empty()
            mock_exists.assert_called_once()

    def test_load_seed_file_with_data_already(self, client, db_connection):
        from main import load_seed_if_empty
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO external_reports (source, nombre, latitud, longitud) VALUES ('CIREN', 'Existing', -33.45, -70.67)")
        db_connection.commit()
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('builtins.open', mock_open(read_data='[]')):
                load_seed_if_empty()

    def test_conaf_duplicate_returns_inserted(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO external_reports (source, nombre, latitud, longitud, fh_inicio) VALUES ('CIREN', 'Dup', -33.45, -70.67, '2026-01-01')")
        db_connection.commit()
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CIREN", "nombre": "Dup", "latitud": -33.45, "longitud": -70.67,
            "fh_inicio": "2026-01-01"
        }, headers={"Authorization": "Bearer test-sync-token"})
        assert response.status_code == 200
        assert response.json()["status"] == "inserted"


class TestMainBackground:
    @pytest.mark.asyncio
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
        with patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker), \
             patch('main.export_external_reports_seed'), \
             patch('main.backup_sqlite_to_s3'):
            await fetch_ciren_data()
        cursor = db_connection.cursor()
        cursor.execute("SELECT nombre, source FROM external_reports")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "Test Fire"

    @pytest.mark.asyncio
    async def test_fetch_ciren_data_skips_no_geometry(self, db_connection):
        from main import fetch_ciren_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(return_value={
            "features": [{"attributes": {"nombre": "No Geo"}, "geometry": {}}]
        })
        with patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker), \
             patch('main.export_external_reports_seed'), \
             patch('main.backup_sqlite_to_s3'):
            await fetch_ciren_data()
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM external_reports")
        assert cursor.fetchone()[0] == 0

    @pytest.mark.asyncio
    async def test_fetch_ciren_data_circuit_breaker_error(self, db_connection):
        from main import fetch_ciren_data
        mock_breaker = MagicMock()
        mock_breaker.call = AsyncMock(side_effect=RuntimeError("CIREN API down"))
        with patch('main.CircuitBreakerRegistry.get', return_value=mock_breaker):
            await fetch_ciren_data()
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM external_reports")
        assert cursor.fetchone()[0] == 0

    @pytest.mark.asyncio
    async def test_fetch_firms_no_api_key(self, db_connection):
        from main import fetch_firms_hotspots
        with patch.dict(os.environ, {'FIRMS_API_KEY': ''}):
            await fetch_firms_hotspots()
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM firms_hotspots")
        assert cursor.fetchone()[0] == 0

    @pytest.mark.asyncio
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
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM firms_hotspots")
        assert cursor.fetchone()[0] > 0

    @pytest.mark.asyncio
    async def test_fetch_weather_no_api_key(self, db_connection):
        from main import fetch_weather_data
        with patch.dict(os.environ, {'OWM_API_KEY': ''}):
            await fetch_weather_data()
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_readings")
        assert cursor.fetchone()[0] == 0

    @pytest.mark.asyncio
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
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_readings")
        assert cursor.fetchone()[0] == len([
            {"region": "Valparaíso", "lat": -33.05, "lon": -71.62},
            {"region": "Metropolitana", "lat": -33.45, "lon": -70.67},
            {"region": "O'Higgins", "lat": -34.17, "lon": -70.74},
        ])


class TestMainEdgeCases:
    def test_dashboard_stats_db_error(self):
        from main import app
        from fastapi.testclient import TestClient
        import jwt, datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'u1', 'email': 't@t.cl', 'rol': 'ADMIN',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        with patch('main.get_db_connection', side_effect=Exception("DB crash")):
            tc = TestClient(app, raise_server_exceptions=False)
            response = tc.get("/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 500

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

    def test_focos_activos_db_error(self, client):
        with patch('main.get_report_repository', side_effect=Exception("DynamoDB down")):
            response = client.get("/focos-activos")
            assert response.status_code == 500

    def test_backup_error_silent(self):
        from main import backup_sqlite_to_s3
        with patch('subprocess.run', side_effect=Exception("aws not found")):
            backup_sqlite_to_s3()

    def test_receive_external_report_invalid_token(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CONAF", "nombre": "Test", "latitud": -33.45, "longitud": -70.67
        }, headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    def test_receive_external_report_no_auth_header(self, client):
        response = client.post("/v1/external-reports/conaf", json={
            "source": "CONAF", "nombre": "Test", "latitud": -33.45, "longitud": -70.67
        })
        assert response.status_code == 403

    def test_trigger_external_fetch_invalid_token(self, client):
        response = client.post("/v1/external-reports/trigger",
                               headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 403

    def test_trigger_external_fetch_no_auth(self, client):
        response = client.post("/v1/external-reports/trigger")
        assert response.status_code == 403

    def test_upload_report_image_http_exception_passthrough(self, client, mock_lambda_service):
        from main import upload_report_image
        mock_file = MagicMock()
        mock_file.content_type = "text/plain"
        with pytest.raises(Exception):
            upload_report_image(file=mock_file)

    def test_seed_resources_skips_when_data_exists(self, db_connection):
        from main import seed_resources
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO incident_resources (report_id, tipo_recurso, cantidad, unidad) VALUES ('r1', 'BOMBEROS', 1, 'CB-1')")
        db_connection.commit()
        seed_resources()
        cursor.execute("SELECT COUNT(*) FROM incident_resources")
        assert cursor.fetchone()[0] == 1

    def test_export_seed_with_data(self, client, db_connection):
        from main import export_external_reports_seed
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO external_reports (source, nombre, region, comuna, provincia, superficie, causa, latitud, longitud, fh_inicio, fh_extinci, temporada) VALUES ('CIREN', 'Fire1', 'RM', 'Santiago', 'Santiago', 100.5, 'Natural', -33.45, -70.67, '2026-01-01', '2026-01-05', '2025-2026')")
        db_connection.commit()
        with patch('builtins.open', mock_open()) as mock_file:
            export_external_reports_seed()
            mock_file.assert_called_once()
            handle = mock_file()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            assert 'Fire1' in written

    def test_export_seed_error_silent(self, client, db_connection):
        from main import export_external_reports_seed
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO external_reports (source, nombre, latitud, longitud) VALUES ('CIREN', 'Fire', -33.45, -70.67)")
        db_connection.commit()
        with patch('builtins.open', side_effect=PermissionError("Read-only")):
            export_external_reports_seed()

    def test_load_seed_with_data(self, client, db_connection):
        from main import load_seed_if_empty
        seed_data = json.dumps([{
            "nombre": "Seed Fire", "region": "Valparaíso", "comuna": "Viña",
            "provincia": "Valparaíso", "superficie": 50.0, "causa": "Accidental",
            "latitud": -33.05, "longitud": -71.55,
            "fh_inicio": "2026-02-01", "fh_extinci": "2026-02-10", "temporada": "2025-2026"
        }])
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=seed_data)):
            load_seed_if_empty()
        cursor = db_connection.cursor()
        cursor.execute("SELECT nombre FROM external_reports")
        assert cursor.fetchone()[0] == "Seed Fire"

    def test_load_seed_file_corrupt(self, client, db_connection):
        from main import load_seed_if_empty
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='{invalid json}')):
            load_seed_if_empty()
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM external_reports")
        assert cursor.fetchone()[0] == 0


