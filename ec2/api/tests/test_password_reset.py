import pytest
from unittest.mock import patch

class TestPasswordReset:
    @pytest.mark.fast
    def test_forgot_password_with_existing_email_sends_otp(self, client):
        with patch('routers.password_reset.query_pg_first', return_value=('reset-user-1', 'reset@test.cl')):
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

    @pytest.mark.fast
    def test_forgot_password_nonexistent_email_returns_404(self, client):
        with patch('routers.password_reset.send_otp_email'):
            response = client.post("/auth/forgot-password", json={
                "email": "noexiste@test.cl"
            })

        assert response.status_code == 404
        assert "Email no registrado" in response.json()["detail"]

    @pytest.mark.e2e
    def test_reset_password_with_valid_otp_updates_password(self, client):
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

    @pytest.mark.fast
    def test_reset_password_with_invalid_otp_returns_400(self, client):
        with patch('routers.password_reset.send_otp_email'):
            with patch('routers.password_reset.query_pg_first', return_value=('reset-user-3', 'reset3@test.cl')):
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
