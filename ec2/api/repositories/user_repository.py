import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from dependencies import SECRET_KEY


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

    def find_all(self) -> list[dict]:
        response = self.table.scan()
        return response.get('Items', [])

    def update(self, user_id: str, email: str | None = None, nombre: str | None = None, rol: str | None = None) -> dict:
        user = self.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        update_expr = []
        expr_attrs = {':user_id': user_id}
        if email is not None:
            update_expr.append('email = :email')
            expr_attrs[':email'] = email
        if nombre is not None:
            update_expr.append('nombre = :nombre')
            expr_attrs[':nombre'] = nombre
        if rol is not None:
            update_expr.append('rol = :rol')
            expr_attrs[':rol'] = rol
        if not update_expr:
            return user
        expr = 'SET ' + ', '.join(update_expr)
        self.table.update_item(Key={'user_id': user_id}, UpdateExpression=expr, ExpressionAttributeValues=expr_attrs)
        return self.find_by_id(user_id)

    def delete(self, user_id: str) -> None:
        user = self.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        self.table.delete_item(Key={'user_id': user_id})

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
