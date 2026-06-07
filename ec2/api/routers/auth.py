from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_user_repository, verify_token, sync_to_sqlite
from models import LoginRequest, RegisterRequest
import jwt
import os
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["auth"])
SECRET_KEY = os.environ.get('JWT_SECRET', 'incendios-valle-secret')


@router.post("/login")
def login(req: LoginRequest):
    try:
        repo = get_user_repository()
        return repo.authenticate(req.email, req.password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@router.post("/register")
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
        raise HTTPException(status_code=500, detail=f"Register error: {str(e)}")
