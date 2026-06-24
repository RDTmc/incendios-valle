import json
import os
import sys
import importlib.util

spec = importlib.util.spec_from_file_location(
    "usuarios_app",
    os.path.join(os.path.dirname(__file__), "app.py")
)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)

from unittest.mock import patch, MagicMock
import bcrypt

class TestUsuarios:
    def test_login_success(self):
        with patch.object(app, 'users_table') as mock_table:
            password = "testpass123"
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            mock_table.query.return_value = {
                'Items': [{
                    'user_id': 'u1',
                    'email': 'test@test.cl',
                    'password_hash': pw_hash,
                    'rol': 'VECINO',
                    'nombre': 'Test'
                }]
            }
            event = {
                "httpMethod": "POST",
                "path": "/login",
                "body": json.dumps({"email": "test@test.cl", "password": password})
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert "token" in body
            assert body["user"]["email"] == "test@test.cl"

    def test_login_invalid_credentials(self):
        with patch.object(app, 'users_table') as mock_table:
            # Usuario existe pero password incorrecto → 401
            pw_hash = bcrypt.hashpw("realpass".encode(), bcrypt.gensalt()).decode()
            mock_table.query.return_value = {
                'Items': [{
                    'user_id': 'u1',
                    'email': 'test@test.cl',
                    'password_hash': pw_hash,
                    'rol': 'VECINO',
                    'nombre': 'Test'
                }]
            }
            event = {
                "httpMethod": "POST",
                "path": "/login",
                "body": json.dumps({"email": "test@test.cl", "password": "wrong"})
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 401
