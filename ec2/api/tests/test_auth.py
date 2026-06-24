import pytest
import json
from unittest.mock import MagicMock, patch

VALID_HASH = "$2b$04$KmVxaFOSh3IJfk5eqiIQoOe6rhiFpEiFrGLNhK5Zbk5FGWiDmTPgG"

class TestAuth:
    @pytest.mark.fast
    def test_login_success(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {
            'Items': [{
                'user_id': 'test-user-id',
                'email': 'test@example.com',
                'password_hash': VALID_HASH,
                'rol': 'VECINO',
                'nombre': 'Test User'
            }]
        }
        response = client.post("/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["rol"] == "VECINO"

    @pytest.mark.fast
    def test_login_invalid_credentials(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {'Items': []}
        response = client.post("/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert "Credenciales inválidas" in response.json()["detail"]

    @pytest.mark.fast
    def test_login_missing_fields(self, client):
        response = client.post("/login", json={"email": "test@example.com"})
        assert response.status_code == 422

        response = client.post("/login", json={"password": "testpass"})
        assert response.status_code == 422

    @pytest.mark.fast
    def test_register_success(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {'Items': []}
        mock_users.put_item.return_value = {}
        response = client.post("/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "nombre": "New User",
            "rol": "VECINO"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["nombre"] == "New User"

    @pytest.mark.fast
    def test_register_duplicate_email(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {
            'Items': [{'user_id': 'existing-id', 'email': 'existing@example.com'}]
        }
        response = client.post("/register", json={
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "nombre": "Existing User"
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.fast
    def test_token_generation(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {
            'Items': [{
                'user_id': 'test-user-id',
                'email': 'token@example.com',
                'password_hash': VALID_HASH,
                'rol': 'ADMIN',
                'nombre': 'Admin User'
            }]
        }
        response = client.post("/login", json={
            "email": "token@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        token = data["token"]
        assert len(token.split(".")) == 3

    @pytest.mark.fast
    def test_verify_token_valid(self, client):
        import jwt
        import datetime
        from datetime import timezone
        token = jwt.encode({
            'user_id': 'test-id',
            'email': 'test@example.com',
            'rol': 'VECINO',
            'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)
        }, 'test-secret-key', algorithm='HS256')
        response = client.get("/dashboard/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200

    @pytest.mark.fast
    def test_verify_token_invalid(self, client):
        response = client.get("/dashboard/stats", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert response.status_code == 401

    @pytest.mark.fast
    def test_verify_token_missing(self, client):
        response = client.get("/dashboard/stats")
        assert response.status_code == 401
        assert "Token requerido" in response.json()["detail"]

    @pytest.mark.fast
    def test_login_db_error(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.side_effect = Exception("DynamoDB error")
        response = client.post("/login", json={"email": "test@test.cl", "password": "test123"})
        assert response.status_code == 500

    @pytest.mark.fast
    def test_register_db_error(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.side_effect = Exception("DynamoDB error")
        response = client.post("/register", json={"email": "test@test.cl", "password": "Test1234!", "nombre": "Test"})
        assert response.status_code == 500

    # ── B1: Login + 2FA OTP en JWT ──────────────────────────────────────

    @pytest.mark.fast
    def test_login_with_2fa_returns_temp_token(self, client, mock_dynamodb, db_connection):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {
            'Items': [{
                'user_id': '2fa-user-id',
                'email': 'admin2fa@test.cl',
                'password_hash': VALID_HASH,
                'rol': 'ADMIN',
                'nombre': 'Admin 2FA'
            }]
        }
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
                       ('2fa-user-id', 'admin2fa@test.cl', 'Admin 2FA', 'ADMIN', '2026-01-01T00:00:00'))
        cursor.execute("INSERT OR REPLACE INTO admin_2fa (user_id, enabled, backup_codes, created_at) VALUES (?, ?, ?, ?)",
                       ('2fa-user-id', 1, '[]', '2026-01-01T00:00:00'))
        db_connection.commit()

        with patch('routers.auth.send_otp_email') as mock_email:
            response = client.post("/login", json={
                "email": "admin2fa@test.cl",
                "password": "testpass123"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["two_factor_required"] is True
        assert "temp_token" in data
        mock_email.assert_called_once()
        email_arg, otp_arg = mock_email.call_args[0]
        assert email_arg == "admin2fa@test.cl"
        assert len(otp_arg) == 6

    @pytest.mark.fast
    def test_verify_2fa_with_valid_otp_returns_jwt(self, client, mock_dynamodb, db_connection):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {
            'Items': [{
                'user_id': '2fa-user-id',
                'email': 'admin2fa@test.cl',
                'password_hash': VALID_HASH,
                'rol': 'ADMIN',
                'nombre': 'Admin 2FA'
            }]
        }
        mock_users.get_item.return_value = {
            'Item': {
                'user_id': '2fa-user-id',
                'email': 'admin2fa@test.cl',
                'rol': 'ADMIN',
                'nombre': 'Admin 2FA',
                'created_at': '2026-01-01T00:00:00'
            }
        }
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
                       ('2fa-user-id', 'admin2fa@test.cl', 'Admin 2FA', 'ADMIN', '2026-01-01T00:00:00'))
        cursor.execute("INSERT OR REPLACE INTO admin_2fa (user_id, enabled, backup_codes, created_at) VALUES (?, ?, ?, ?)",
                       ('2fa-user-id', 1, '[]', '2026-01-01T00:00:00'))
        db_connection.commit()

        with patch('routers.auth._generate_otp', return_value='123456'):
            with patch('routers.auth.send_otp_email'):
                login_resp = client.post("/login", json={
                    "email": "admin2fa@test.cl",
                    "password": "testpass123"
                })

        assert login_resp.status_code == 200
        temp_token = login_resp.json()["temp_token"]

        response = client.post("/auth/2fa/verify", json={
            "temp_token": temp_token,
            "code": "123456"
        })

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["rol"] == "ADMIN"
        assert data["user"]["email"] == "admin2fa@test.cl"

    @pytest.mark.fast
    def test_verify_2fa_with_invalid_otp_returns_401(self, client, mock_dynamodb, db_connection):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {
            'Items': [{
                'user_id': '2fa-user-id',
                'email': 'admin2fa@test.cl',
                'password_hash': VALID_HASH,
                'rol': 'ADMIN',
                'nombre': 'Admin 2FA'
            }]
        }
        cursor = db_connection.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
                       ('2fa-user-id', 'admin2fa@test.cl', 'Admin 2FA', 'ADMIN', '2026-01-01T00:00:00'))
        cursor.execute("INSERT OR REPLACE INTO admin_2fa (user_id, enabled, backup_codes, created_at) VALUES (?, ?, ?, ?)",
                       ('2fa-user-id', 1, '["AAAA-BBBB"]', '2026-01-01T00:00:00'))
        db_connection.commit()

        with patch('routers.auth.send_otp_email'):
            login_resp = client.post("/login", json={
                "email": "admin2fa@test.cl",
                "password": "testpass123"
            })

        assert login_resp.status_code == 200
        temp_token = login_resp.json()["temp_token"]

        response = client.post("/auth/2fa/verify", json={
            "temp_token": temp_token,
            "code": "000000"
        })

        assert response.status_code == 401
        assert "Código inválido" in response.json()["detail"]
