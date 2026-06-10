from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_user_repository, verify_token, sync_to_sqlite, SECRET_KEY
from models import LoginRequest, RegisterRequest
from notification_service import send_welcome_notification
import jwt
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["auth"])


@router.post("/login", responses={
    500: {"description": "Login error"},
})
def login(req: LoginRequest):
    try:
        repo = get_user_repository()
        return repo.authenticate(req.email, req.password)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[auth] Login error: {e}")
        raise HTTPException(status_code=500, detail="Login error")


@router.post("/register", responses={
    500: {"description": "Register error"},
})
def register(req: RegisterRequest):
    try:
        repo = get_user_repository()
        user = repo.create(req.email, req.password, req.nombre, req.rol)

        sync_to_sqlite('users', 'INSERT', {
            'user_id': user['user_id'],
            'email': user['email'],
            'nombre': user['nombre'],
            'rol': user['rol'],
            'created_at': user['created_at'],
        })

        send_welcome_notification(
            email=user['email'],
            nombre=user['nombre'],
            rol=user['rol'],
        )

        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'rol': user['rol'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')

        return {
            "token": token,
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "rol": user['rol'],
                "nombre": user['nombre']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[auth] Register error: {e}")
        raise HTTPException(status_code=500, detail="Register error")
