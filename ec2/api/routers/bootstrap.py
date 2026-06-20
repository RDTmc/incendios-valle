"""
One-time bootstrap endpoint to create or restore admin access.
Only works when DynamoDB is unavailable and the user exists in SQLite.
Self-destructs after first use (sets BOOTSTRAPPED env var).
"""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dependencies import get_db_connection

router = APIRouter(tags=["auth"])


class BootstrapRequest(BaseModel):
    email: str


@router.post("/auth/bootstrap-admin")
def bootstrap_admin(req: BootstrapRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, email, rol FROM users WHERE email = ?", (req.email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en SQLite")

        cursor.execute("UPDATE users SET rol = 'ADMIN' WHERE email = ?", (req.email,))
        conn.commit()

        cursor.execute("SELECT user_id, email, nombre, rol FROM users WHERE email = ?", (req.email,))
        row = cursor.fetchone()
        return {
            "status": "ok",
            "user": {
                "user_id": row[0],
                "email": row[1],
                "nombre": row[2] or "",
                "rol": "ADMIN",
            },
            "message": "Rol actualizado a ADMIN. Cierra sesión y vuelve a iniciar sesión."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
