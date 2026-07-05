import secrets
import bcrypt
import json
from fastapi import APIRouter, HTTPException
from models import ForgotPasswordRequest, ResetPasswordRequest
from dependencies import SECRET_KEY
from database_pg import query_pg_first, get_pg_connection
from notification_service import send_otp_email
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["auth"])

_reset_otp_store: dict[str, dict] = {}
OTP_EXPIRE_MINUTES = 10


def _generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


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

    pg_user = query_pg_first("SELECT user_id, email FROM users WHERE email = %s", (req.email,), fetch='one')
    if pg_user is None:
        raise HTTPException(status_code=404, detail="Email no registrado")

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

    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:

                cur.execute("SELECT user_id FROM users WHERE email = %s", (req.email,))
                user = cur.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")

                user_id = user[0]

                cur.execute("SELECT enabled, backup_codes FROM admin_2fa WHERE user_id = %s", (user_id,))
                twofa_row = cur.fetchone()
                twofa_enabled = bool(twofa_row[0]) if twofa_row else False
                backup_codes = json.loads(twofa_row[1]) if twofa_row and twofa_row[1] else []

                if twofa_enabled:
                    if req.backup_code:
                        if req.backup_code not in backup_codes:
                            raise HTTPException(status_code=400, detail="Código de respaldo inválido")
                        backup_codes.remove(req.backup_code)
                    else:
                        cur.execute("UPDATE admin_2fa SET enabled = 0 WHERE user_id = %s", (user_id,))
                        conn.commit()

                new_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
                cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, user_id))

                if twofa_enabled and req.backup_code:
                    remaining = [c for c in backup_codes]
                    cur.execute("UPDATE admin_2fa SET backup_codes = %s WHERE user_id = %s", (json.dumps(remaining), user_id))

                conn.commit()
                _reset_otp_store.pop(req.email, None)

                return {"message": "Contraseña actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[password_reset] Error: {e}")
        raise HTTPException(status_code=500, detail="Error al restablecer contraseña")
