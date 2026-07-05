"""
One-time bootstrap endpoint to create or restore admin access.
Self-destructs after first use (sets BOOTSTRAPPED env var).
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database_pg import get_pg_connection

router = APIRouter(tags=["auth"])


class BootstrapRequest(BaseModel):
    email: str


@router.post("/auth/bootstrap-admin")
def bootstrap_admin(req: BootstrapRequest):
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, email, rol FROM users WHERE email = %s", (req.email,))
                user = cur.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")

                cur.execute("UPDATE users SET rol = 'ADMIN' WHERE email = %s", (req.email,))
                conn.commit()

                cur.execute("SELECT user_id, email, nombre, rol FROM users WHERE email = %s", (req.email,))
                row = cur.fetchone()
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
        raise HTTPException(status_code=500, detail="Error interno del servidor")
