from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Annotated
import boto3
import bcrypt
import jwt
import os
import uuid
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from lambda_service import upload_image
import httpx
import asyncio
import json

from repositories import UserRepository, ReportRepository
from factories import ReportFactory
from circuit_breaker import CircuitBreakerRegistry
from routers.bff import router as bff_router
from routers.auth import router as auth_router
from routers.reports import router as reports_router
from routers.public import router as public_router
from routers.alerts import router as alerts_router
from dependencies import verify_token, verify_token_optional, sync_to_sqlite
from models import SyncRequest, ExternalReportRequest

_background_tasks: set[asyncio.Task] = set()

ALLOWED_MIME = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024

app = FastAPI(
    title="Incendios API",
    root_path="/api"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://incendios-valle.pages.dev",
        "https://dashboard.keogh.lat",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bff_router)
app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(public_router)
app.include_router(alerts_router)


def get_dynamodb_resource():
    return boto3.resource('dynamodb')


def get_users_table():
    return get_dynamodb_resource().Table('users')


def get_reports_table():
    return get_dynamodb_resource().Table('reports')


def get_user_repository() -> UserRepository:
    return UserRepository(get_users_table())


def get_report_repository() -> ReportRepository:
    return ReportRepository(get_reports_table())


DB_PATH = os.environ.get('DB_PATH', "/app/data/incendios.db")
SYNC_TOKEN = os.environ['SYNC_TOKEN']

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            nombre TEXT,
            rol TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
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
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS external_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            fetched_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source, nombre, fh_inicio, latitud, longitud)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incident_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            tipo_recurso TEXT NOT NULL,
            cantidad INTEGER DEFAULT 1,
            unidad TEXT DEFAULT '',
            estado TEXT DEFAULT 'ASIGNADO',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (report_id) REFERENCES reports(report_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firms_hotspots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            fetched_at TEXT DEFAULT (datetime('now')),
            UNIQUE(latitude, longitude, acq_date, acq_time, satellite)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            region TEXT,
            temperature REAL,
            humidity INTEGER,
            wind_speed REAL,
            wind_direction REAL,
            weather_desc TEXT,
            pressure INTEGER,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL DEFAULT 'INFO',
            message TEXT NOT NULL,
            report_id TEXT DEFAULT '',
            latitud REAL DEFAULT 0,
            longitud REAL DEFAULT 0,
            source TEXT DEFAULT 'system',
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')
    try:
        cursor.execute("ALTER TABLE reports ADD COLUMN foto_url TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


init_db()


def seed_resources():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM incident_resources")
    if cursor.fetchone()[0] == 0:
        resources = [
            ("test-qa-singular-12345", "BOMBEROS", 2, "CB-1, CB-2"),
            ("test-qa-singular-12345", "VEHICULO", 1, "V-101"),
            ("test-qa-singular-12345", "BRIGADA", 1, "Brigada Forestal Este"),
            ("43c0b7b0-4828-47fb-a298-973d27b9f1d9", "BOMBEROS", 1, "CB-3"),
            ("43c0b7b0-4828-47fb-a298-973d27b9f1d9", "CAMION_CISTERNA", 1, "CC-501"),
        ]
        cursor.executemany(
            "INSERT INTO incident_resources (report_id, tipo_recurso, cantidad, unidad) VALUES (?, ?, ?, ?)",
            resources
        )
        conn.commit()
    conn.close()


seed_resources()


def encode_geohash(lat: float, lon: float) -> str:
    lat_hash = int(lat * 1000000)
    lon_hash = int(lon * 1000000)
    return f"{lat_hash // 1000}-{lon_hash // 1000}"


@app.post("/reports/upload", responses={
    400: {"description": "Solo se permiten imágenes JPEG o PNG"},
    500: {"description": "Error al subir imagen"},
})
def upload_report_image(file: Annotated[UploadFile, File()]):
    try:
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Solo se permiten imágenes JPEG o PNG")
        contents = file.file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="La imagen no debe superar los 5MB")
        url = upload_image(contents, file.content_type)
        return {"foto_url": url}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[upload] Error: {e}")
        raise HTTPException(status_code=500, detail="Error al subir imagen")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/focos-activos", responses={
    500: {"description": "Error fetching focos"},
})
def get_focos_activos():
    try:
        LAT_MIN, LAT_MAX = -34.5, -32.5
        LNG_MIN, LNG_MAX = -71.5, -69.5
        repo = get_report_repository()
        items = repo.find_in_bbox(LAT_MIN, LAT_MAX, LNG_MIN, LNG_MAX)
        focos = []
        for item in items:
            try:
                lat = float(item.get('latitud', 0))
                lng = float(item.get('longitud', 0))
            except (ValueError, TypeError):
                continue
            if lat == 0 and lng == 0:
                continue
            focos.append({
                'id': item.get('report_id') or item.get('reports_id', ''),
                'lat': lat,
                'lng': lng,
                'estado': item.get('estado', 'DESCONOCIDO'),
                'tipo': item.get('tipo', 'FORESTAL'),
                'descripcion': item.get('descripcion', ''),
                'foto_url': item.get('foto_url', ''),
                'created_at': item.get('created_at', '')
            })
        focos.sort(key=lambda f: f['created_at'], reverse=True)
        return focos
    except Exception as e:
        print(f"[focos] Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching focos")


@app.post("/sync", responses={
    403: {"description": "Invalid sync token"},
})
def sync_from_lambda(req: SyncRequest, x_sync_token: Annotated[str, Header()]):
    if x_sync_token != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid sync token")
    result = sync_to_sqlite(req.table, req.operation, req.data)
    return {"status": "synced", "operation": req.operation, "result": result}


S3_BACKUP_PATH = "/app/data/backups"
SEED_PATH = "/app/data/seed.json"


def backup_sqlite_to_s3():
    import subprocess
    try:
        bucket = os.environ.get('AWS_S3_BUCKET', 'incendios-valle-sol')
        subprocess.run(
            ["aws", "s3", "cp", DB_PATH,
             f"s3://{bucket}/backups/incendios-latest.db"],
            capture_output=True, timeout=30
        )
        subprocess.run(
            ["aws", "s3", "cp", DB_PATH,
             f"s3://{bucket}/backups/incendios-$(date +%Y%m%d-%H%M%S).db"],
            capture_output=True, timeout=30
        )
        print("[S3] Backup completado")
    except Exception as e:
        print(f"[S3] Backup error: {e}")


def restore_sqlite_from_s3():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM external_reports")
        count = cursor.fetchone()[0]
    finally:
        conn.close()
    if count > 0:
        print("[S3] BD ya tiene datos, no se restaura")
        return
    import subprocess
    try:
        bucket = os.environ.get('AWS_S3_BUCKET', 'incendios-valle-sol')
        result = subprocess.run(
            ["aws", "s3", "cp", f"s3://{bucket}/backups/incendios-latest.db", DB_PATH],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            print("[S3] BD restaurada desde S3")
    except Exception as e:
        print(f"[S3] Restore error: {e}")


def export_external_reports_seed():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, region, comuna, provincia, superficie, causa, latitud, longitud, fh_inicio, fh_extinci, temporada FROM external_reports ORDER BY fh_inicio DESC LIMIT 50")
        rows = cursor.fetchall()
        if rows:
            seed = [{
                "nombre": r[0], "region": r[1], "comuna": r[2],
                "provincia": r[3], "superficie": r[4], "causa": r[5],
                "latitud": r[6], "longitud": r[7],
                "fh_inicio": r[8], "fh_extinci": r[9], "temporada": r[10]
            } for r in rows if r[0]]
            with open(SEED_PATH, "w") as f:
                json.dump(seed, f, indent=2, ensure_ascii=False)
            print(f"[SEED] Exportados {len(seed)} registros a seed.json")
    except Exception as e:
        print(f"[SEED] Export error: {e}")
    finally:
        if conn is not None:
            conn.close()


def load_seed_if_empty():
    if not os.path.exists(SEED_PATH):
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM external_reports")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    try:
        with open(SEED_PATH) as f:
            seed = json.load(f)
        for row in seed:
            cursor.execute("""
                INSERT OR IGNORE INTO external_reports
                (source, nombre, region, comuna, provincia, superficie, causa,
                 latitud, longitud, fh_inicio, fh_extinci, temporada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "CIREN", row.get("nombre"), row.get("region"),
                row.get("comuna"), row.get("provincia"),
                row.get("superficie"), row.get("causa"),
                row.get("latitud"), row.get("longitud"),
                row.get("fh_inicio"), row.get("fh_extinci"),
                row.get("temporada"),
            ))
        conn.commit()
        print(f"[SEED] Cargados {len(seed)} registros desde seed.json")
    except Exception as e:
        print(f"[SEED] Load error: {e}")
    conn.close()


async def fetch_ciren_data():
    url = (
        "https://esri.ciren.cl/server/rest/services/"
        "INCENDIOS_FORESTALES/FeatureServer/16/query"
        "?where=codreg+IN+(13,5,6)"
        "&outFields=nombre,region,provincia,comuna,superficie,"
        "causa_gene,fh_inicio,fh_extinci,temporada"
        "&f=json&outSR=4326&resultRecordCount=2000"
    )
    breaker = CircuitBreakerRegistry.get("ciren", failure_threshold=3, recovery_timeout=60.0)

    async def fetch():
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=30)
            return r.json()

    try:
        data = await breaker.call(fetch)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            inserted = 0
            for feature in data.get("features", []):
                attrs = feature.get("attributes", {})
                geo = feature.get("geometry", {})
                lng = geo.get("x")
                lat = geo.get("y")
                if lat is None or lng is None:
                    continue
                cursor.execute("""
                    INSERT OR IGNORE INTO external_reports
                    (source, nombre, region, comuna, provincia, superficie, causa,
                     latitud, longitud, fh_inicio, fh_extinci, temporada)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "CIREN",
                    attrs.get("nombre"), attrs.get("region"),
                    attrs.get("comuna"), attrs.get("provincia"),
                    attrs.get("superficie"), attrs.get("causa_gene"),
                    lat, lng,
                    attrs.get("fh_inicio"), attrs.get("fh_extinci"),
                    attrs.get("temporada"),
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            conn.commit()
        finally:
            conn.close()
        print(f"[CIREN] Fetched: {len(data.get('features', []))} features, {inserted} new")
        if inserted > 0:
            export_external_reports_seed()
            backup_sqlite_to_s3()
    except Exception as e:
        print(f"[CIREN] Error: {e}")


async def periodic_fetch_ciren():
    await asyncio.sleep(30)
    while True:
        await fetch_ciren_data()
        await asyncio.sleep(3600)


FIRMS_BBOX = "-72.5,-35.0,-69.5,-32.5"
FIRMS_SOURCES = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]


async def fetch_firms_hotspots():
    api_key = os.environ.get('FIRMS_API_KEY', '')
    if not api_key:
        print("[FIRMS] No API key configured")
        return
    import csv, io
    breaker = CircuitBreakerRegistry.get("firms", failure_threshold=3, recovery_timeout=60.0)
    for source in FIRMS_SOURCES:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/{source}/{FIRMS_BBOX}/2"

        async def fetch(source=source, url=url):
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=30)
            if r.status_code != 200:
                raise Exception(f"[FIRMS] {source}: HTTP {r.status_code}")
            return r

        try:
            r = await breaker.call(fetch)
            reader = csv.DictReader(io.StringIO(r.text))
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                inserted = 0
                for item in reader:
                    cursor.execute("""
                        INSERT OR IGNORE INTO firms_hotspots
                        (latitude, longitude, brightness, frp, confidence, satellite, acq_date, acq_time, daynight, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("latitude"), item.get("longitude"),
                        item.get("bright_ti4") or item.get("brightness"),
                        item.get("frp"),
                        str(item.get("confidence", "")),
                        item.get("satellite", ""),
                        item.get("acq_date", ""),
                        item.get("acq_time"),
                        item.get("daynight", ""), source
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                conn.commit()
            finally:
                conn.close()
            print(f"[FIRMS] {source}: {inserted} new hotpots")
        except Exception as e:
            print(f"[FIRMS] Error {source}: {e}")


async def periodic_fetch_firms():
    await asyncio.sleep(60)
    while True:
        await fetch_firms_hotspots()
        await asyncio.sleep(1800)


WEATHER_ZONES = [
    {"region": "Valparaíso", "lat": -33.05, "lon": -71.62},
    {"region": "Metropolitana", "lat": -33.45, "lon": -70.67},
    {"region": "O'Higgins", "lat": -34.17, "lon": -70.74},
]


async def fetch_weather_data():
    api_key = os.environ.get('OWM_API_KEY', '')
    if not api_key:
        print("[OWM] No API key configured")
        return
    breaker = CircuitBreakerRegistry.get("owm", failure_threshold=3, recovery_timeout=60.0)
    for zone in WEATHER_ZONES:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={zone['lat']}&lon={zone['lon']}&units=metric&appid={api_key}"

        async def fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=15)
            if r.status_code != 200:
                raise Exception(f"[OWM] {zone['region']}: HTTP {r.status_code}")
            return r.json()

        try:
            data = await breaker.call(fetch)
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO weather_readings
                    (lat, lon, region, temperature, humidity, wind_speed, wind_direction, weather_desc, pressure)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    zone['lat'], zone['lon'], zone['region'],
                    data.get("main", {}).get("temp"),
                    data.get("main", {}).get("humidity"),
                    data.get("wind", {}).get("speed"),
                    data.get("wind", {}).get("deg"),
                    data.get("weather", [{}])[0].get("description", ""),
                    data.get("main", {}).get("pressure"),
                ))
                conn.commit()
            finally:
                conn.close()
            w = data.get("main", {})
            print(f"[OWM] {zone['region']}: {w.get('temp')}°C, {w.get('humidity')}% humedad")
        except Exception as e:
            print(f"[OWM] Error {zone['region']}: {e}")


async def periodic_fetch_weather():
    await asyncio.sleep(90)
    while True:
        await fetch_weather_data()
        await asyncio.sleep(1800)


@app.on_event("startup")
async def start_background_tasks():
    await asyncio.sleep(5)
    restore_sqlite_from_s3()
    load_seed_if_empty()
    for fn in (periodic_fetch_ciren, periodic_fetch_firms, periodic_fetch_weather):
        task = asyncio.create_task(fn())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


@app.post("/v1/external-reports/trigger", responses={
    403: {"description": "Invalid token"},
})
async def trigger_external_fetch(authorization: Annotated[Optional[str], Header()] = None):
    if not authorization or authorization.replace("Bearer ", "") != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    task = asyncio.create_task(fetch_ciren_data())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return {"status": "triggered", "message": "Fetch iniciado en background"}


@app.post("/v1/external-reports/conaf", responses={
    403: {"description": "Invalid token"},
    500: {"description": "Internal server error"},
})
def receive_external_report(req: ExternalReportRequest, authorization: Annotated[Optional[str], Header()] = None):
    if not authorization or authorization.replace("Bearer ", "") != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO external_reports
                (source, nombre, region, comuna, provincia, superficie, causa,
                 latitud, longitud, fh_inicio, fh_extinci, temporada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req.source, req.nombre, req.region, req.comuna, req.provincia,
                req.superficie, req.causa,
                req.latitud, req.longitud,
                req.fh_inicio, req.fh_extinci, req.temporada
            ))
            conn.commit()
            new_id = cursor.lastrowid
            return {"status": "inserted", "id": new_id}
        finally:
            conn.close()
    except Exception as e:
        print(f"[sync] Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/dashboard/stats", responses={
    500: {"description": "Internal server error"},
})
def get_dashboard_stats(payload: Annotated[dict, Depends(verify_token)]):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reports")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
        by_estado = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
        by_tipo = {row[0]: row[1] for row in cursor.fetchall()}
        return {
            "total": total,
            "by_estado": by_estado,
            "by_tipo": by_tipo
        }
    except Exception as e:
        print(f"[dashboard] stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()
