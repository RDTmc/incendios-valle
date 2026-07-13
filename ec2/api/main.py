from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Annotated
import boto3
import bcrypt
import jwt
import os
import uuid
from datetime import datetime, timedelta, timezone
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
from routers.admin import router as admin_router
from routers.password_reset import router as password_reset_router
from routers.bootstrap import router as bootstrap_router
from routers.grafana_bff import router as grafana_bff_router
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
app.include_router(admin_router)
app.include_router(password_reset_router)
app.include_router(bootstrap_router)
app.include_router(grafana_bff_router)


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


SYNC_TOKEN = os.environ['SYNC_TOKEN']

from database_pg import init_pg_schema
try:
    init_pg_schema()
except Exception:
    pass


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
        api_url = f"https://api.keogh.lat/api/images/{url}"
        return {"foto_url": api_url}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[upload] Error: {e}")
        raise HTTPException(status_code=500, detail="Error al subir imagen")


IMAGE_EXPIRATION = 604800  # 7 días


@app.get("/images/{key:path}")
def image_proxy(key: str):
    """Genera presigned URL y redirige. key ej: reportes/uuid.jpg"""
    try:
        s3 = boto3.client("s3")
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "incendios-valle-sol", "Key": key},
            ExpiresIn=IMAGE_EXPIRATION,
        )
        return RedirectResponse(url)
    except Exception as e:
        print(f"[image_proxy] Error: {e}")
        raise HTTPException(status_code=404, detail="Imagen no encontrada")


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
        from database_pg import get_pg_connection
        with get_pg_connection() as conn:
            if conn is not None:
                with conn.cursor() as cur:
                    inserted = 0
                    for feature in data.get("features", []):
                        attrs = feature.get("attributes", {})
                        geo = feature.get("geometry", {})
                        lng = geo.get("x")
                        lat = geo.get("y")
                        if lat is None or lng is None:
                            continue
                        cur.execute("""
                            INSERT INTO external_reports
                            (source, nombre, region, comuna, provincia, superficie, causa,
                             latitud, longitud, fh_inicio, fh_extinci, temporada)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (source, nombre, fh_inicio, latitud, longitud) DO NOTHING
                        """, (
                            "CIREN",
                            attrs.get("nombre"), attrs.get("region"),
                            attrs.get("comuna"), attrs.get("provincia"),
                            attrs.get("superficie"), attrs.get("causa_gene"),
                            lat, lng,
                            attrs.get("fh_inicio"), attrs.get("fh_extinci"),
                            attrs.get("temporada"),
                        ))
                        if cur.rowcount > 0:
                            inserted += 1
                    conn.commit()
            else:
                inserted = 0
        print(f"[CIREN] Fetched: {len(data.get('features', []))} features, {inserted} new")
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
                raise RuntimeError(f"[FIRMS] {source}: HTTP {r.status_code}")
            return r

        try:
            r = await breaker.call(fetch)
            reader = csv.DictReader(io.StringIO(r.text))
            from database_pg import get_pg_connection
            with get_pg_connection() as conn:
                if conn is not None:
                    with conn.cursor() as cur:
                        inserted = 0
                        for item in reader:
                            cur.execute("""
                                INSERT INTO firms_hotspots
                                (latitude, longitude, brightness, frp, confidence, satellite, acq_date, acq_time, daynight, source)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (latitude, longitude, acq_date, acq_time, satellite) DO NOTHING
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
                            if cur.rowcount > 0:
                                inserted += 1
                        conn.commit()
                else:
                    inserted = 0
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
    {"region": "Melipilla", "lat": -33.69, "lon": -71.21},
]


async def fetch_weather_data():
    api_key = os.environ.get('OWM_API_KEY', '')
    if not api_key:
        print("[OWM] No API key configured")
        return
    breaker = CircuitBreakerRegistry.get("owm", failure_threshold=3, recovery_timeout=60.0)
    for zone in WEATHER_ZONES:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={zone['lat']}&lon={zone['lon']}&units=metric&appid={api_key}"

        async def fetch(url=url, zone=zone):
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=15)
            if r.status_code != 200:
                raise RuntimeError(f"[OWM] {zone['region']}: HTTP {r.status_code}")
            return r.json()

        try:
            data = await breaker.call(fetch)
            from database_pg import get_pg_connection
            with get_pg_connection() as conn:
                if conn is not None:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO weather_readings
                            (lat, lon, region, temperature, humidity, wind_speed, wind_direction, weather_desc, pressure)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    from database_pg import get_pg_connection
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO external_reports
                    (source, nombre, region, comuna, provincia, superficie, causa,
                     latitud, longitud, fh_inicio, fh_extinci, temporada)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, nombre, fh_inicio, latitud, longitud) DO NOTHING
                    RETURNING id
                """, (
                    req.source, req.nombre, req.region, req.comuna, req.provincia,
                    req.superficie, req.causa,
                    req.latitud, req.longitud,
                    req.fh_inicio, req.fh_extinci, req.temporada
                ))
                row = cur.fetchone()
                conn.commit()
                new_id = row[0] if row else None
                return {"status": "inserted", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[sync] Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/dashboard/stats", responses={
    500: {"description": "Internal server error"},
})
def get_dashboard_stats(payload: Annotated[dict, Depends(verify_token)]):
    from database_pg import query_pg_first
    total_row = query_pg_first("SELECT COUNT(*) FROM reports", fetch='one')
    total = total_row[0] if total_row else 0
    by_estado_rows = query_pg_first("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
    by_estado = {r[0]: r[1] for r in by_estado_rows} if by_estado_rows else {}
    by_tipo_rows = query_pg_first("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
    by_tipo = {r[0]: r[1] for r in by_tipo_rows} if by_tipo_rows else {}
    return {"total": total, "by_estado": by_estado, "by_tipo": by_tipo}
