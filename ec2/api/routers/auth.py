import os
import json
import secrets
from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_user_repository, verify_token, require_admin, sync_to_sqlite, SECRET_KEY
from models import LoginRequest, RegisterRequest, TwoFactorVerifyRequest
from notification_service import notify_new_user, send_otp_email
from database_pg import query_pg_first, get_pg_connection
import jwt
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["auth"])

OTP_EXPIRE_MINUTES = 5
BACKUP_CODE_COUNT = 1

_otp_store: dict[str, dict] = {}


def _clean_expired_otp():
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _otp_store.items() if v.get("expires_at", now) < now]
    for k in expired:
        _otp_store.pop(k, None)


def _get_2fa_config(user_id: str) -> dict | None:
    pg_row = query_pg_first("SELECT user_id, enabled, backup_codes FROM admin_2fa WHERE user_id = %s", (user_id,), fetch='one')
    if pg_row is None:
        return None
    codes = json.loads(pg_row[2]) if pg_row[2] else []
    return {"user_id": pg_row[0], "enabled": bool(pg_row[1]), "backup_codes": codes}


def _save_2fa_config(user_id: str, enabled: bool, backup_codes: list[str] | None = None):
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                now = datetime.now(timezone.utc).isoformat()
                codes_json = json.dumps(backup_codes or [])
                cur.execute("""
                    INSERT INTO admin_2fa (user_id, enabled, backup_codes, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        enabled = EXCLUDED.enabled,
                        backup_codes = EXCLUDED.backup_codes
                """, (user_id, 1 if enabled else 0, codes_json, now))
                conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        print(f"[2fa] save error: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar configuración 2FA")


def _generate_backup_codes() -> list[str]:
    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        code = f"{code[:4]}-{code[4:]}"
        codes.append(code)
    return codes


def _generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


@router.post("/login", responses={
    500: {"description": "Login error"},
})
def login(req: LoginRequest):
    try:
        import bcrypt
        user = None

        repo = get_user_repository()
        user = repo.find_by_email(req.email)
        if user:
            stored_hash = user.get('password_hash', '')
            if not bcrypt.checkpw(req.password.encode(), stored_hash.encode()):
                pg_row = query_pg_first("SELECT password_hash FROM users WHERE email = %s", (req.email,), fetch='one')
                if pg_row and pg_row[0]:
                    if not bcrypt.checkpw(req.password.encode(), pg_row[0].encode()):
                        raise HTTPException(status_code=401, detail="Credenciales inválidas")
                else:
                    raise HTTPException(status_code=401, detail="Credenciales inválidas")
        else:
            pg_row = query_pg_first(
                "SELECT user_id, email, nombre, rol, created_at, password_hash FROM users WHERE email = %s",
                (req.email,), fetch='one'
            )
            if pg_row and pg_row[5]:
                if bcrypt.checkpw(req.password.encode(), pg_row[5].encode()):
                    user = {
                        "user_id": pg_row[0],
                        "email": pg_row[1],
                        "nombre": pg_row[2] or "",
                        "rol": pg_row[3],
                        "created_at": pg_row[4] or "",
                    }
                else:
                    raise HTTPException(status_code=401, detail="Credenciales inválidas")
            else:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

        twofa = _get_2fa_config(user['user_id'])

        if twofa and twofa['enabled']:
            otp = _generate_otp()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

            _clean_expired_otp()
            _otp_store[user['user_id']] = {
                "otp": otp,
                "expires_at": expires_at,
            }

            temp_token = jwt.encode({
                'user_id': user['user_id'],
                'purpose': '2fa',
                'exp': expires_at,
            }, SECRET_KEY, algorithm='HS256')

            send_otp_email(user.get('email', ''), otp)

            return {
                "two_factor_required": True,
                "temp_token": temp_token,
            }

        role = user.get('rol', 'VECINO')
        try:
            pg_row = query_pg_first("SELECT rol FROM users WHERE user_id = %s", (user['user_id'],), fetch='one')
            if pg_row:
                role = pg_row[0]
        except Exception:
            pass

        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'rol': role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        }, SECRET_KEY, algorithm='HS256')

        return {
            "token": token,
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "rol": role,
                "nombre": user.get('nombre', ''),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[auth] Login error: {e}")
        raise HTTPException(status_code=500, detail="Error al iniciar sesión")


@router.post("/auth/2fa/verify")
def verify_2fa(req: TwoFactorVerifyRequest):
    try:
        try:
            temp_payload = jwt.decode(req.temp_token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Código expirado, inicie sesión nuevamente")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")
        if temp_payload.get('purpose') != '2fa':
            raise HTTPException(status_code=400, detail="Token inválido")
        user_id = temp_payload['user_id']

        _clean_expired_otp()
        otp_entry = _otp_store.get(user_id)
        if not otp_entry:
            raise HTTPException(status_code=401, detail="Código expirado, inicie sesión nuevamente")

        if req.code == otp_entry["otp"]:
            _otp_store.pop(user_id, None)
            repo = get_user_repository()
            user = repo.find_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            role = user.get('rol', 'VECINO')
            try:
                pg_row = query_pg_first("SELECT rol FROM users WHERE user_id = %s", (user['user_id'],), fetch='one')
                if pg_row:
                    role = pg_row[0]
            except Exception:
                pass

            token = jwt.encode({
                'user_id': user['user_id'],
                'email': user['email'],
                'rol': role,
                'exp': datetime.now(timezone.utc) + timedelta(hours=24),
            }, SECRET_KEY, algorithm='HS256')

            return {
                "token": token,
                "user": {
                    "user_id": user['user_id'],
                    "email": user['email'],
                    "rol": role,
                    "nombre": user.get('nombre', ''),
                },
            }

        # Verify backup code
        twofa = _get_2fa_config(user_id)
        print(f"[2fa] verify backup code check: twofa={twofa}, code={req.code}")
        if twofa and twofa['backup_codes']:
            codes = twofa['backup_codes']
            print(f"[2fa] backup codes in DB: {codes}")
            if req.code in codes:
                codes.remove(req.code)
                _save_2fa_config(user_id, True, codes)

                repo = get_user_repository()
                user = repo.find_by_id(user_id)
                if not user:
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")

                role = user.get('rol', 'VECINO')
                try:
                    pg_row = query_pg_first("SELECT rol FROM users WHERE user_id = %s", (user['user_id'],), fetch='one')
                    if pg_row:
                        role = pg_row[0]
                except Exception:
                    pass

                token = jwt.encode({
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'rol': role,
                    'exp': datetime.now(timezone.utc) + timedelta(hours=24),
                }, SECRET_KEY, algorithm='HS256')

                return {
                    "token": token,
                    "user": {
                        "user_id": user['user_id'],
                        "email": user['email'],
                        "rol": role,
                        "nombre": user.get('nombre', ''),
                    },
                }

        raise HTTPException(status_code=401, detail="Código inválido")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[2fa] verify_2fa unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {type(e).__name__}")


@router.post("/admin/2fa/setup")
def setup_2fa(payload: dict = Depends(require_admin)):
    user_id = payload['user_id']

    existing = _get_2fa_config(user_id)
    if existing and existing['enabled']:
        raise HTTPException(status_code=400, detail="2FA ya está activado")

    backup_codes = _generate_backup_codes()
    _save_2fa_config(user_id, True, backup_codes)

    return {
        "status": "enabled",
        "backup_codes": backup_codes,
    }


@router.post("/admin/2fa/disable")
def disable_2fa(payload: dict = Depends(require_admin)):
    user_id = payload['user_id']
    _save_2fa_config(user_id, False)
    return {"status": "disabled"}


@router.get("/admin/2fa/status")
def get_2fa_status(payload: dict = Depends(require_admin)):
    twofa = _get_2fa_config(payload['user_id'])
    if twofa:
        remaining = len(twofa.get('backup_codes', []))
        return {
            "enabled": twofa['enabled'],
            "remaining_backup_codes": remaining,
        }
    return {"enabled": False, "remaining_backup_codes": 0}


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

        notify_new_user(
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
        raise HTTPException(status_code=500, detail="Error al registrarse")
