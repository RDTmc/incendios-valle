import os
import jwt
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Header
from typing import Optional

SECRET_KEY = os.environ['JWT_SECRET']


def get_dynamodb_resource():
    import boto3
    return boto3.resource('dynamodb')


def get_users_table():
    return get_dynamodb_resource().Table('users')


def get_reports_table():
    return get_dynamodb_resource().Table('reports')


def get_user_repository():
    from repositories import UserRepository
    return UserRepository(get_users_table())


def get_report_repository():
    from repositories import ReportRepository
    return ReportRepository(get_reports_table())


def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def require_admin(payload: dict = Depends(verify_token)):
    if payload.get('rol') != 'ADMIN':
        raise HTTPException(status_code=403, detail="Se requiere rol ADMIN")
    return payload


def verify_token_optional(authorization: Optional[str] = Header(None)):
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def sync_to_sqlite(table: str, operation: str, data: dict) -> str:
    return sync_to_postgres(table, operation, data)


def sync_to_postgres(table: str, operation: str, data: dict) -> str:
    from database_pg import get_pg_connection, is_pg_configured
    if not is_pg_configured():
        return "pg not configured"
    try:
        with get_pg_connection() as conn:
            if conn is None:
                return "pg not available"
            with conn.cursor() as cur:
                if table == 'users' and operation == 'INSERT':
                    cur.execute('''
                        INSERT INTO users (user_id, email, nombre, rol, password_hash, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            email = EXCLUDED.email,
                            nombre = EXCLUDED.nombre,
                            rol = EXCLUDED.rol,
                            password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash),
                            created_at = COALESCE(EXCLUDED.created_at, users.created_at)
                    ''', (
                        data.get('user_id'),
                        data.get('email'),
                        data.get('nombre'),
                        data.get('rol', 'VECINO'),
                        data.get('password_hash', ''),
                        data.get('created_at'),
                    ))
                elif table == 'reports' and operation in ('INSERT', 'MODIFY'):
                    r_id = data.get('report_id') or data.get('reports_id')
                    cur.execute('''
                        INSERT INTO reports (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, foto_url, estado, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (report_id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            tipo = EXCLUDED.tipo,
                            latitud = EXCLUDED.latitud,
                            longitud = EXCLUDED.longitud,
                            geohash = EXCLUDED.geohash,
                            descripcion = EXCLUDED.descripcion,
                            foto_url = EXCLUDED.foto_url,
                            estado = EXCLUDED.estado,
                            updated_at = EXCLUDED.updated_at
                    ''', (
                        r_id,
                        data.get('user_id', 'ANONIMO'),
                        data.get('tipo', 'FORESTAL'),
                        data.get('latitud', '0'),
                        data.get('longitud', '0'),
                        data.get('geohash', ''),
                        data.get('descripcion', ''),
                        data.get('foto_url', ''),
                        data.get('estado', 'PENDIENTE'),
                        data.get('created_at'),
                        data.get('updated_at'),
                    ))
                conn.commit()
        return "synced"
    except Exception as e:
        print(f"[sync_to_postgres] Error: {e}")
        return "error"
