import os
import json
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

PG_HOST = os.environ.get("PG_HOST", "")
PG_PORT = int(os.environ.get("PG_PORT", "5432"))
PG_USER = os.environ.get("PG_USER", "postgres")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "")
PG_DATABASE = os.environ.get("PG_DATABASE", "incendios")

_pool = None

def is_pg_configured():
    return bool(PG_HOST and PG_PASSWORD)

def get_pool():
    global _pool
    if _pool is None:
        if not is_pg_configured():
            return None
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DATABASE,
        )
    return _pool

@contextmanager
def get_pg_connection():
    pool = get_pool()
    if pool is None:
        yield None
        return
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

def init_pg_schema():
    with get_pg_connection() as conn:
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    nombre TEXT,
                    rol TEXT,
                    password_hash TEXT,
                    created_at TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    tipo TEXT,
                    latitud TEXT,
                    longitud TEXT,
                    geohash TEXT,
                    descripcion TEXT,
                    foto_url TEXT DEFAULT '',
                    estado TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS external_reports (
                    id SERIAL PRIMARY KEY,
                    source TEXT DEFAULT 'CIREN',
                    nombre TEXT,
                    region TEXT,
                    comuna TEXT,
                    provincia TEXT,
                    superficie REAL,
                    causa TEXT,
                    latitud REAL,
                    longitud REAL,
                    fh_inicio TEXT,
                    fh_extinci TEXT,
                    temporada TEXT,
                    fetched_at TEXT DEFAULT (NOW()::text),
                    UNIQUE(source, nombre, fh_inicio, latitud, longitud)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS incident_resources (
                    id SERIAL PRIMARY KEY,
                    report_id TEXT NOT NULL REFERENCES reports(report_id),
                    tipo_recurso TEXT NOT NULL,
                    cantidad INTEGER DEFAULT 1,
                    unidad TEXT DEFAULT '',
                    estado TEXT DEFAULT 'ASIGNADO',
                    created_at TEXT DEFAULT (NOW()::text),
                    updated_at TEXT DEFAULT (NOW()::text)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS firms_hotspots (
                    id SERIAL PRIMARY KEY,
                    latitude REAL,
                    longitude REAL,
                    brightness REAL,
                    frp REAL,
                    confidence TEXT,
                    satellite TEXT,
                    acq_date TEXT,
                    acq_time INTEGER,
                    daynight TEXT,
                    source TEXT,
                    fetched_at TEXT DEFAULT (NOW()::text),
                    UNIQUE(latitude, longitude, acq_date, acq_time, satellite)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weather_readings (
                    id SERIAL PRIMARY KEY,
                    lat REAL,
                    lon REAL,
                    region TEXT,
                    temperature REAL,
                    humidity INTEGER,
                    wind_speed REAL,
                    wind_direction REAL,
                    weather_desc TEXT,
                    pressure INTEGER,
                    fetched_at TEXT DEFAULT (NOW()::text)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    alert_type TEXT NOT NULL DEFAULT 'INFO',
                    message TEXT NOT NULL,
                    report_id TEXT DEFAULT '',
                    latitud REAL DEFAULT 0,
                    longitud REAL DEFAULT 0,
                    source TEXT DEFAULT 'system',
                    read INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (NOW()::text)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    action TEXT NOT NULL,
                    admin_id TEXT NOT NULL,
                    target_id TEXT,
                    details TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    type TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    recipient_name TEXT DEFAULT '',
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'sent',
                    sns_message_id TEXT DEFAULT '',
                    created_at TEXT DEFAULT (NOW()::text)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admin_2fa (
                    user_id TEXT PRIMARY KEY,
                    enabled INTEGER DEFAULT 0,
                    backup_codes TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()
