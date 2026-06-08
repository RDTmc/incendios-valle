import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
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


