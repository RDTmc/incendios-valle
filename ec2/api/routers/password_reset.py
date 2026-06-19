import secrets
import random
import bcrypt
import json
import sqlite3
from fastapi import APIRouter, HTTPException
from models import ForgotPasswordRequest, ResetPasswordRequest
from dependencies import get_db_connection, SECRET_KEY
from notification_service import send_otp_email
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["auth"])

_reset_otp_store: dict[str, dict] = {}
OTP_EXPIRE_MINUTES = 10


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def _clean_expired_otp():
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _reset_otp_store.items() if v.get("expires_at", now) < now]
    for k in expired:
        _reset_otp_store.pop(k, None)


@router.post("/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    _clean_expired_otp()
    otp = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, email FROM users WHERE email = ?", (req.email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Email no registrado")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error al verificar usuario")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    _reset_otp_store[req.email] = {
        "otp": otp,
        "expires_at": expires_at,
    }

    send_otp_email(req.email, otp)
    return {"message": "Código de verificación enviado al correo"}


@router.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest):
    _clean_expired_otp()

    entry = _reset_otp_store.get(req.email)
    if not entry:
        raise HTTPException(status_code=400, detail="Solicitud de recuperación no encontrada. Solicita un nuevo código.")
    if entry["otp"] != req.otp:
        raise HTTPException(status_code=400, detail="Código de verificación incorrecto")
    if entry["expires_at"] < datetime.now(timezone.utc):
        _reset_otp_store.pop(req.email, None)
        raise HTTPException(status_code=400, detail="Código expirado. Solicita uno nuevo.")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM users WHERE email = ?", (req.email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user_id = user[0]

        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_2fa (
            user_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 0,
            backup_codes TEXT DEFAULT '[]'
        )''')
        conn.commit()

        cursor.execute("SELECT enabled, backup_codes FROM admin_2fa WHERE user_id = ?", (user_id,))
        twofa_row = cursor.fetchone()
        twofa_enabled = bool(twofa_row[0]) if twofa_row else False
        backup_codes = json.loads(twofa_row[1]) if twofa_row and twofa_row[1] else []

        if twofa_enabled:
            if req.backup_code:
                if req.backup_code not in backup_codes:
                    raise HTTPException(status_code=400, detail="Código de respaldo inválido")
                backup_codes.remove(req.backup_code)
            else:
                cursor.execute("UPDATE admin_2fa SET enabled = 0 WHERE user_id = ?", (user_id,))
                conn.commit()

        new_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT", ())
            conn.commit()
        except Exception:
            pass

        cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user_id))

        if twofa_enabled and req.backup_code:
            remaining = [c for c in backup_codes]
            cursor.execute("UPDATE admin_2fa SET backup_codes = ? WHERE user_id = ?", (json.dumps(remaining), user_id))

        conn.commit()
        _reset_otp_store.pop(req.email, None)

        return {"message": "Contraseña actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[password_reset] Error: {e}")
        raise HTTPException(status_code=500, detail="Error al restablecer contraseña")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
