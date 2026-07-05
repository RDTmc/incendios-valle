import pytest
from unittest.mock import patch


class TestAlerts:
    @pytest.mark.e2e
    def test_create_alert(self, client):
        response = client.post("/alerts?alert_type=ALTA&message=Test%20alert&report_id=r1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["id"] > 0

    @pytest.mark.fast
    def test_create_alert_no_message(self, client):
        response = client.post("/alerts?alert_type=INFO")
        assert response.status_code == 400

    @pytest.mark.e2e
    def test_list_alerts(self, client):
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.e2e
    def test_list_alerts_filter_read(self, client):
        response = client.get("/alerts?read=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.e2e
    def test_mark_alert_read(self, client):
        response = client.put("/alerts/1/read")
        assert response.status_code == 200

    @pytest.mark.e2e
    def test_list_alerts_limit(self, client):
        response = client.get("/alerts?limit=3")
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.fast
    def test_list_alerts_db_error(self, client):
        with patch('routers.alerts.query_pg_first', return_value=None):
            response = client.get("/alerts")
            assert response.status_code == 503

    @pytest.mark.fast
    def test_create_alert_db_error(self, client):
        with patch('routers.alerts.get_pg_connection') as mock_conn:
            mock_conn.return_value.__enter__.return_value = None
            response = client.post("/alerts?alert_type=ALTA&message=Test")
            assert response.status_code == 503

    @pytest.mark.fast
    def test_mark_alert_read_db_error(self, client):
        with patch('routers.alerts.get_pg_connection') as mock_conn:
            mock_conn.return_value.__enter__.return_value = None
            response = client.put("/alerts/1/read")
            assert response.status_code == 500
