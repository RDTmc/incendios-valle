import os
import json
import secrets
import random
import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_user_repository, verify_token, require_admin, sync_to_sqlite, SECRET_KEY, get_db_connection, DB_PATH
from models import LoginRequest, RegisterRequest, TwoFactorVerifyRequest
from notification_service import notify_new_user, send_otp_email
import jwt
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["auth"])

OTP_EXPIRE_MINUTES = 5
BACKUP_CODE_COUNT = 1


def _init_2fa_table():
    conn = None
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_2fa (
                user_id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                backup_codes TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"[2fa] table init error: {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _get_2fa_config(user_id: str) -> dict | None:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, enabled, backup_codes FROM admin_2fa WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            codes = json.loads(row[2]) if row[2] else []
            return {"user_id": row[0], "enabled": bool(row[1]), "backup_codes": codes}
        return None
    except Exception as e:
        print(f"[2fa] get error: {e}")
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _save_2fa_config(user_id: str, enabled: bool, backup_codes: list[str] | None = None):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        codes_json = json.dumps(backup_codes or [])
        cursor.execute("""
            INSERT OR REPLACE INTO admin_2fa (user_id, enabled, backup_codes, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, 1 if enabled else 0, codes_json, now))
        conn.commit()
    except Exception as e:
        print(f"[2fa] save error: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar configuración 2FA")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _generate_backup_codes() -> list[str]:
    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        code = f"{code[:4]}-{code[4:]}"
        codes.append(code)
    return codes


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


@router.post("/login", responses={
    500: {"description": "Login error"},
})
def login(req: LoginRequest):
    try:
        import bcrypt
        user = None
        from_db = "dynamodb"

        repo = get_user_repository()
        user = repo.find_by_email(req.email)
        if user:
            stored_hash = user.get('password_hash', '')
            if not bcrypt.checkpw(req.password.encode(), stored_hash.encode()):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT password_hash FROM users WHERE email = ?", (req.email,))
                    row = cursor.fetchone()
                    conn.close()
                    if row and row[0]:
                        if bcrypt.checkpw(req.password.encode(), row[0].encode()):
                            from_db = "sqlite"
                        else:
                            raise HTTPException(status_code=401, detail="Credenciales inválidas")
                    else:
                        raise HTTPException(status_code=401, detail="Credenciales inválidas")
                except HTTPException:
                    raise
                except Exception:
                    raise HTTPException(status_code=401, detail="Credenciales inválidas")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, email, nombre, rol, created_at, password_hash FROM users WHERE email = ?", (req.email,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            if not row[5] or not bcrypt.checkpw(req.password.encode(), row[5].encode()):
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            user = {
                "user_id": row[0],
                "email": row[1],
                "nombre": row[2] or "",
                "rol": row[3],
                "created_at": row[4] or "",
            }
            from_db = "sqlite"

        _init_2fa_table()
        twofa = _get_2fa_config(user['user_id'])

        # Sync DynamoDB role to SQLite (critical: SQLite role is authoritative when 2FA is active)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            dyn_role = user.get('rol', '')
            if dyn_role:
                cursor.execute("UPDATE users SET rol = ? WHERE user_id = ? AND rol != ?", (dyn_role, user['user_id'], dyn_role))
                conn.commit()
            conn.close()
        except Exception:
            pass

        if twofa and twofa['enabled']:
            otp = _generate_otp()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

            temp_token = jwt.encode({
                'user_id': user['user_id'],
                'purpose': '2fa',
                'otp': otp,
                'exp': expires_at,
            }, SECRET_KEY, algorithm='HS256')

            send_otp_email(user.get('email', ''), otp)

            return {
                "two_factor_required": True,
                "temp_token": temp_token,
            }

        role = user.get('rol', 'VECINO')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT rol FROM users WHERE user_id = ?", (user['user_id'],))
            row = cursor.fetchone()
            if row:
                role = row[0]
            conn.close()
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
            if temp_payload.get('purpose') != '2fa':
                raise HTTPException(status_code=400, detail="Token inválido")
            user_id = temp_payload['user_id']
            expected_otp = temp_payload.get('otp', '')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Código expirado, inicie sesión nuevamente")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")

        if req.code == expected_otp:
            repo = get_user_repository()
            user = repo.find_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            role = user.get('rol', 'VECINO')
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT rol FROM users WHERE user_id = ?", (user['user_id'],))
                row = cursor.fetchone()
                if row:
                    role = row[0]
                conn.close()
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
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT rol FROM users WHERE user_id = ?", (user['user_id'],))
                    row = cursor.fetchone()
                    if row:
                        role = row[0]
                    conn.close()
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
    _init_2fa_table()

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
    _init_2fa_table()
    _save_2fa_config(user_id, False)
    return {"status": "disabled"}


@router.get("/admin/2fa/status")
def get_2fa_status(payload: dict = Depends(require_admin)):
    _init_2fa_table()
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
