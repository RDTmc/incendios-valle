import pytest
from unittest.mock import patch

class TestPasswordReset:
    def test_forgot_password_with_existing_email_sends_otp(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
                       ('reset-user-1', 'reset@test.cl', 'Reset User', 'VECINO', '2026-01-01T00:00:00'))
        db_connection.commit()

        with patch('routers.password_reset.send_otp_email') as mock_email:
            response = client.post("/auth/forgot-password", json={
                "email": "reset@test.cl"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Código de verificación enviado al correo"
        mock_email.assert_called_once()
        email_arg, otp_arg = mock_email.call_args[0]
        assert email_arg == "reset@test.cl"
        assert len(otp_arg) == 6

    def test_forgot_password_nonexistent_email_returns_404(self, client):
        with patch('routers.password_reset.send_otp_email'):
            response = client.post("/auth/forgot-password", json={
                "email": "noexiste@test.cl"
            })

        assert response.status_code == 404
        assert "Email no registrado" in response.json()["detail"]

    def test_reset_password_with_valid_otp_updates_password(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
                       ('reset-user-2', 'reset2@test.cl', 'Reset User 2', 'VECINO', '2026-01-01T00:00:00'))
        db_connection.commit()

        with patch('routers.password_reset.send_otp_email') as mock_email:
            forgot_resp = client.post("/auth/forgot-password", json={
                "email": "reset2@test.cl"
            })
        assert forgot_resp.status_code == 200

        otp = mock_email.call_args[0][1]

        response = client.post("/auth/reset-password", json={
            "email": "reset2@test.cl",
            "otp": otp,
            "password": "NuevaPass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Contraseña actualizada correctamente"

        cursor.execute("SELECT password_hash FROM users WHERE email = ?", ("reset2@test.cl",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] is not None
        assert len(row[0]) > 20

    def test_reset_password_with_invalid_otp_returns_400(self, client, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
                       ('reset-user-3', 'reset3@test.cl', 'Reset User 3', 'VECINO', '2026-01-01T00:00:00'))
        db_connection.commit()

        with patch('routers.password_reset.send_otp_email'):
            forgot_resp = client.post("/auth/forgot-password", json={
                "email": "reset3@test.cl"
            })
        assert forgot_resp.status_code == 200

        response = client.post("/auth/reset-password", json={
            "email": "reset3@test.cl",
            "otp": "999999",
            "password": "NuevaPass123!"
        })

        assert response.status_code == 400
        assert "Código de verificación incorrecto" in response.json()["detail"]
