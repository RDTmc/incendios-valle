import pytest


class TestAlerts:
    @pytest.mark.fast
    def test_create_alert(self, client, db_connection):
        response = client.post("/alerts?alert_type=ALTA&message=Test%20alert&report_id=r1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["id"] > 0

    @pytest.mark.fast
    def test_create_alert_no_message(self, client):
        response = client.post("/alerts?alert_type=INFO")
        assert response.status_code == 400

    @pytest.mark.fast
    def test_list_alerts(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO alerts (alert_type, message, report_id) VALUES (?, ?, ?)",
                       ("ALTA", "Incendio forestal detectado", "r1"))
        cursor.execute("INSERT INTO alerts (alert_type, message, report_id) VALUES (?, ?, ?)",
                       ("INFO", "Clima favorable", "r2"))
        db_connection.commit()

        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.fast
    def test_list_alerts_filter_read(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO alerts (alert_type, message, report_id, read) VALUES (?, ?, ?, ?)",
                       ("ALTA", "Test alert", "r1", 1))
        cursor.execute("INSERT INTO alerts (alert_type, message, report_id, read) VALUES (?, ?, ?, ?)",
                       ("INFO", "Unread", "r2", 0))
        db_connection.commit()

        response = client.get("/alerts?read=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["read"] == False

    @pytest.mark.fast
    def test_mark_alert_read(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO alerts (alert_type, message) VALUES (?, ?)",
                       ("ALTA", "Test"))
        alert_id = cursor.lastrowid
        db_connection.commit()

        response = client.put(f"/alerts/{alert_id}/read")
        assert response.status_code == 200

        cursor.execute("SELECT read FROM alerts WHERE id = ?", (alert_id,))
        assert cursor.fetchone()[0] == 1

    @pytest.mark.fast
    def test_list_alerts_limit(self, client, db_connection):
        cursor = db_connection.cursor()
        for i in range(5):
            cursor.execute("INSERT INTO alerts (alert_type, message) VALUES (?, ?)",
                           ("INFO", f"Alert {i}"))
        db_connection.commit()

        response = client.get("/alerts?limit=3")
        data = response.json()
        assert len(data) == 3

    @pytest.mark.fast
    def test_list_alerts_db_error(self, client):
        from unittest.mock import patch
        with patch('routers.alerts.get_db_connection', side_effect=Exception("DB crash")):
            response = client.get("/alerts")
            assert response.status_code == 500

    @pytest.mark.fast
    def test_create_alert_db_error(self, client):
        from unittest.mock import patch
        with patch('routers.alerts.get_db_connection', side_effect=Exception("DB crash")):
            response = client.post("/alerts?alert_type=ALTA&message=Test")
            assert response.status_code == 500

    @pytest.mark.fast
    def test_mark_alert_read_db_error(self, client):
        from unittest.mock import patch
        with patch('routers.alerts.get_db_connection', side_effect=Exception("DB crash")):
            response = client.put("/alerts/1/read")
            assert response.status_code == 500
