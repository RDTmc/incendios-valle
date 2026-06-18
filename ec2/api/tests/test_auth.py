import pytest
import json
from unittest.mock import MagicMock

VALID_HASH = "$2b$04$KmVxaFOSh3IJfk5eqiIQoOe6rhiFpEiFrGLNhK5Zbk5FGWiDmTPgG"

class TestAuth:
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

    def test_login_invalid_credentials(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.return_value = {'Items': []}
        response = client.post("/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert "Credenciales inválidas" in response.json()["detail"]

    def test_login_missing_fields(self, client):
        response = client.post("/login", json={"email": "test@example.com"})
        assert response.status_code == 422

        response = client.post("/login", json={"password": "testpass"})
        assert response.status_code == 422

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

    def test_verify_token_invalid(self, client):
        response = client.get("/dashboard/stats", headers={
            "Authorization": "Bearer invalid.token.here"
        })
        assert response.status_code == 401

    def test_verify_token_missing(self, client):
        response = client.get("/dashboard/stats")
        assert response.status_code == 401
        assert "Token requerido" in response.json()["detail"]

    def test_login_db_error(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.side_effect = Exception("DynamoDB error")
        response = client.post("/login", json={"email": "test@test.cl", "password": "test123"})
        assert response.status_code == 500

    def test_register_db_error(self, client, mock_dynamodb):
        mock_users, _ = mock_dynamodb
        mock_users.query.side_effect = Exception("DynamoDB error")
        response = client.post("/register", json={"email": "test@test.cl", "password": "Test1234!", "nombre": "Test"})
        assert response.status_code == 500
