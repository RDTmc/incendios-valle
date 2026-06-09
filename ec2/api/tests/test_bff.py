import pytest
import os


class TestBFF:
    def test_bff_dashboard(self, client):
        response = client.get("/bff/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "weather" in data
        assert "hotspots" in data
        assert "focos" in data
        assert data["stats"]["total_reportes"] >= 0
        assert data["hotspots"]["ciren_records"] >= 0

    def test_bff_dashboard_with_data(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO reports (report_id, user_id, tipo, estado, latitud, longitud, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("r1", "u1", "FORESTAL", "ACTIVO", "-33.0", "-70.0", "2026-01-01", "2026-01-01"))
        cursor.execute("INSERT INTO reports (report_id, user_id, tipo, estado, latitud, longitud, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("r2", "u2", "URBANO", "PENDIENTE", "-33.5", "-70.5", "2026-01-01", "2026-01-01"))
        cursor.execute("INSERT INTO weather_readings (lat, lon, region, temperature, humidity, wind_speed, weather_desc, pressure) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (-33.45, -70.67, "Metropolitana", 25.0, 60, 5.0, "clear sky", 1013))
        cursor.execute("INSERT INTO firms_hotspots (latitude, longitude, brightness, frp, confidence, satellite, acq_date, acq_time, daynight, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (-33.5, -70.5, 300.0, 50.0, "high", "NPP", "2026-01-01", 1200, "D", "VIIRS_SNPP_NRT"))
        db_connection.commit()

        response = client.get("/bff/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_reportes"] == 2
        assert data["stats"]["forestales"] == 1
        assert data["stats"]["urbanos"] == 1
        assert data["weather"]["temperature"] == 25.0
        assert data["hotspots"]["ciren_records"] >= 0

    def test_bff_dashboard_no_data(self, client):
        response = client.get("/bff/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_reportes"] == 0
        assert data["weather"] == {}

    def test_bff_dashboard_focos(self, client, mock_dynamodb):
        _, mock_reports = mock_dynamodb
        mock_reports.scan.return_value = {
            'Items': [
                {'reports_id': 'r1', 'latitud': '-33.45', 'longitud': '-70.67',
                 'estado': 'ACTIVO', 'tipo': 'FORESTAL', 'descripcion': '', 'foto_url': '', 'created_at': ''},
                {'reports_id': 'r2', 'latitud': 'invalid', 'longitud': '-70.0',
                 'estado': 'ACTIVO', 'tipo': 'FORESTAL', 'descripcion': '', 'foto_url': '', 'created_at': ''},
                {'reports_id': 'r3', 'latitud': '0', 'longitud': '0',
                 'estado': 'ACTIVO', 'tipo': 'FORESTAL', 'descripcion': '', 'foto_url': '', 'created_at': ''},
            ]
        }
        response = client.get("/bff/dashboard")
        assert response.status_code == 200
        assert len(response.json()["focos"]) == 1

    def test_bff_dashboard_db_error(self, client):
        from unittest.mock import patch
        with patch('main.get_db_connection', side_effect=Exception("DB crash")):
            response = client.get("/bff/dashboard")
            assert response.status_code == 500
