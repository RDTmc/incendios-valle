import pytest


class TestBFF:
    @pytest.mark.e2e
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

    @pytest.mark.e2e
    def test_bff_dashboard_with_data(self, client):
        response = client.get("/bff/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_reportes"] == 2
        assert data["stats"]["forestales"] == 1
        assert data["stats"]["urbanos"] == 1

    @pytest.mark.e2e
    def test_bff_dashboard_no_data(self, client):
        response = client.get("/bff/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_reportes"] == 0
        assert data["weather"] == {}

    @pytest.mark.fast
    def test_bff_dashboard_focos(self, client, mock_dynamodb):
        from unittest.mock import patch
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
        with patch('routers.bff.query_pg_first') as mock_pg:
            mock_pg.side_effect = [
                [("ACTIVO", 3)],                         # by_estado_rows
                [("FORESTAL", 3)],                        # by_tipo_rows
                None,                                     # weather_row (no data)
                (0,),                                     # hc (hotspots count)
                (5,),                                     # cc (ciren total)
                (3,),                                     # ac (active reports)
            ]
            response = client.get("/bff/dashboard")
            assert response.status_code == 200
            assert len(response.json()["focos"]) == 1

    @pytest.mark.fast
    def test_bff_dashboard_db_error(self, client):
        from unittest.mock import patch
        with patch('routers.bff.query_pg_first', return_value=None):
            response = client.get("/bff/dashboard")
            assert response.status_code == 503
