import uuid
import bcrypt
import jwt
import os
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

SECRET_KEY = os.environ.get('JWT_SECRET', 'incendios-valle-secret')


class UserRepository:
    def __init__(self, table):
        self.table = table

    def find_by_email(self, email: str) -> dict | None:
        response = self.table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        items = response.get('Items', [])
        return items[0] if items else None

    def find_by_id(self, user_id: str) -> dict | None:
        response = self.table.get_item(Key={'user_id': user_id})
        return response.get('Item')

    def create(self, email: str, password: str, nombre: str = '', rol: str = 'VECINO') -> dict:
        existing = self.find_by_email(email)
        if existing:
            raise HTTPException(status_code=409, detail="User already exists")

        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'nombre': nombre,
            'rol': rol,
            'created_at': timestamp,
        }
        self.table.put_item(Item=item)
        return item

    def authenticate(self, email: str, password: str) -> dict:
        user = self.find_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        stored_hash = user.get('password_hash', '')
        if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'rol': user.get('rol', 'VECINO'),
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        }, SECRET_KEY, algorithm='HS256')

        return {
            "token": token,
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "rol": user.get('rol', 'VECINO'),
                "nombre": user.get('nombre', ''),
            },
        }
