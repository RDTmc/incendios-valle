import os
import sqlite3
import jwt
from datetime import datetime, timezone
from fastapi import HTTPException, Header
from typing import Optional

SECRET_KEY = os.environ['JWT_SECRET']
DB_PATH = os.environ.get('DB_PATH', "/app/data/incendios.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


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
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if table == 'users':
            if operation == 'INSERT':
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, email, nombre, rol, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (data.get('user_id'), data.get('email'), data.get('nombre'),
                      data.get('rol', 'VECINO'), data.get('created_at')))
            result = "user synced"
        elif table == 'reports':
            if operation in ['INSERT', 'MODIFY']:
                r_id = data.get('report_id') or data.get('reports_id')
                cursor.execute('''
                    INSERT OR REPLACE INTO reports
                    (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, foto_url, estado, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (r_id, data.get('user_id'), data.get('tipo'),
                      data.get('latitud'), data.get('longitud'), data.get('geohash'),
                      data.get('descripcion'), data.get('foto_url', ''),
                      data.get('estado'), data.get('created_at'), data.get('updated_at')))
            result = "report synced"
        else:
            result = "unknown table"
        conn.commit()
        return result
    except Exception as e:
        print(f"[sync_to_sqlite] Error: {e}")
        return "error"
    finally:
        if conn is not None:
            conn.close()
