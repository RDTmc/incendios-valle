from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
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

ALLOWED_MIME = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app = FastAPI(
    title="Incendios API",
    root_path="/api"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración DynamoDB - Inicialización dinámica para soportar rotación de credenciales AWS Academy
def get_dynamodb_resource():
    """Obtiene el recurso DynamoDB con credenciales frescas en cada request"""
    return boto3.resource('dynamodb')

def get_users_table():
    return get_dynamodb_resource().Table('users')

def get_reports_table():
    return get_dynamodb_resource().Table('reports')

# Configuración SQLite Local (Caché de Sincronización y Dashboard)
DB_PATH = "/app/data/incendios.db"
SYNC_TOKEN = os.environ.get('SYNC_TOKEN', 'incendios-sync-secret-token')

Path("/app/data").mkdir(parents=True, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=DELETE")
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

    # Migración preventiva por si la columna foto_url no existe en la BD local
    try:
        cursor.execute("ALTER TABLE reports ADD COLUMN foto_url TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Ya existe la columna

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

SECRET_KEY = os.environ.get('JWT_SECRET', 'incendios-valle-secret-key')

# Models Pydantic
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str = ""
    rol: str = "VECINO"

class ReportRequest(BaseModel):
    user_id: Optional[str] = None
    tipo: str = "INCENDIO"
    latitud: float
    longitud: float
    descripcion: str = ""
    foto_url: str = ""
    device_id: Optional[str] = None

class SyncRequest(BaseModel):
    table: str
    operation: str
    data: dict

def encode_geohash(lat: float, lon: float) -> str:
    lat_hash = int(lat * 1000000)
    lon_hash = int(lon * 1000000)
    return f"{lat_hash // 1000}-{lon_hash // 1000}"

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_token_optional(authorization: Optional[str] = Header(None)):
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None

# ==================== ENDPOINTS ====================

@app.post("/reports/upload")
def upload_report_image(file: UploadFile = File(...)):
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
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")

@app.post("/login")
def login(req: LoginRequest):
    try:
        users_table = get_users_table()
        response = users_table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': req.email}
        )
        
        items = response.get('Items', [])
        if not items:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = items[0]
        stored_hash = user.get('password_hash', '')
        
        if not bcrypt.checkpw(req.password.encode(), stored_hash.encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'rol': user.get('rol', 'VECINO'),
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        return {
            "token": token,
            "user": {
                "user_id": user['user_id'],
                "email": user['email'],
                "rol": user.get('rol', 'VECINO'),
                "nombre": user.get('nombre', '')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/register")
def register(req: RegisterRequest):
    try:
        users_table = get_users_table()
        response = users_table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': req.email}
        )
        
        if response.get('Items'):
            raise HTTPException(status_code=409, detail="User already exists")
        
        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        users_table.put_item(Item={
            'user_id': user_id,
            'email': req.email,
            'password_hash': password_hash,
            'nombre': req.nombre,
            'rol': req.rol,
            'created_at': timestamp
        })
        
        sync_to_sqlite('users', 'INSERT', {
            'user_id': user_id,
            'email': req.email,
            'nombre': req.nombre,
            'rol': req.rol,
            'created_at': timestamp
        })
        
        token = jwt.encode({
            'user_id': user_id,
            'email': req.email,
            'rol': req.rol,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        return {
            "token": token,
            "user": {
                "user_id": user_id,
                "email": req.email,
                "rol": req.rol,
                "nombre": req.nombre
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Register error: {str(e)}")

@app.post("/reports")
def create_report(req: ReportRequest, payload: Optional[dict] = Depends(verify_token_optional)):
    try:
        if not payload:
            if not req.device_id:
                raise HTTPException(status_code=400, detail="device_id requerido para reportes anónimos")
            user_id = "ANONIMO"
        else:
            user_id = req.user_id or payload.get('user_id', 'ANONIMO')
        
        reports_table = get_reports_table()
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        item = {
            'reports_id': report_id,
            'report_id': report_id,
            'user_id': user_id,
            'device_id': req.device_id or '',
            'tipo': req.tipo,
            'latitud': str(req.latitud),
            'longitud': str(req.longitud),
            'geohash': encode_geohash(req.latitud, req.longitud),
            'descripcion': req.descripcion,
            'foto_url': req.foto_url,
            'estado': 'PENDIENTE',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        reports_table.put_item(Item=item)
        sync_to_sqlite('reports', 'INSERT', item)
        
        return {
            "report_id": report_id,
            "estado": "PENDIENTE",
            "created_at": timestamp
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create report error: {str(e)}")

@app.post("/api/reportar")
@app.post("/reportar")
def reportar_anonimo(req: ReportRequest, payload: Optional[dict] = Depends(verify_token_optional)):
    return create_report(req, payload)

@app.get("/reports")
def list_reports(estado: Optional[str] = None, user_id: Optional[str] = None, payload: dict = Depends(verify_token)):
    try:
        reports_table = get_reports_table()
        if user_id:
            response = reports_table.query(
                IndexName='user-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            items = response.get('Items', [])
        else:
            response = reports_table.scan()
            items = response.get('Items', [])
        
        if estado:
            items = [i for i in items if i.get('estado') == estado]
        
        for item in items:
            item['report_id'] = item.get('reports_id', '')
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List reports error: {str(e)}")

@app.get("/reports/{report_id}")
def get_report(report_id: str, payload: dict = Depends(verify_token)):
    try:
        reports_table = get_reports_table()
        response = reports_table.get_item(Key={'reports_id': report_id})
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="Report not found")
        item['report_id'] = item.get('reports_id', '')
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get report error: {str(e)}")

@app.put("/reports/{report_id}")
def update_report(report_id: str, estado: Optional[str] = None, descripcion: Optional[str] = None, payload: dict = Depends(verify_token)):
    try:
        reports_table = get_reports_table()
        update_expr = "SET "
        expr_values = {}
        expr_names = {}

        if estado:
            update_expr += "#estado = :estado, "
            expr_values[':estado'] = estado
            expr_names['#estado'] = 'estado'
        if descripcion:
            update_expr += "descripcion = :descripcion, "
            expr_values[':descripcion'] = descripcion

        update_expr += "updated_at = :updated_at"
        expr_values[':updated_at'] = datetime.now(timezone.utc).isoformat()

        update_kwargs = {
            'Key': {'reports_id': report_id},
            'UpdateExpression': update_expr,
            'ExpressionAttributeValues': expr_values,
        }
        if expr_names:
            update_kwargs['ExpressionAttributeNames'] = expr_names

        reports_table.update_item(**update_kwargs)

        response = reports_table.get_item(Key={'reports_id': report_id})
        item = response.get('Item', {})
        if item:
            item['report_id'] = item.get('reports_id', '')
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update report error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/public/dashboard-stats")
def public_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
        by_estado = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
        by_tipo = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {
            "focos_activos": by_estado.get("ACTIVO", 0) + by_estado.get("PENDIENTE", 0),
            "estado_pendiente": by_estado.get("PENDIENTE", 0),
            "estado_activo": by_estado.get("ACTIVO", 0),
            "estado_controlado": by_estado.get("CONTROLADO", 0),
            "estado_extinguido": by_estado.get("EXTINGUIDO", 0),
            "tipo_forestal": by_tipo.get("FORESTAL", 0),
            "tipo_urbano": by_tipo.get("URBANO", 0)
        }
    except Exception as e:
        return {"focos_activos": 0, "estado_pendiente": 0, "estado_activo": 0, "estado_controlado": 0, "estado_extinguido": 0, "tipo_forestal": 0, "tipo_urbano": 0, "error": str(e)}

@app.get("/public/map-coordinates")
def public_map_coordinates():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT latitud, longitud, tipo, estado FROM reports")
        rows = cursor.fetchall()
        conn.close()
        peso = {"ACTIVO": 3, "PENDIENTE": 2, "CONTROLADO": 1, "EXTINGUIDO": 0}
        return [{
            "lat": float(r[0]) if r[0] else 0.0,
            "lng": float(r[1]) if r[1] else 0.0,
            "tipo": r[2],
            "estado": r[3],
            "intensidad": peso.get(r[3], 1)
        } for r in rows if r[0] and r[1]]
    except Exception as e:
        return {"error": str(e)}

@app.get("/public/cluster-stats")
def public_cluster_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        corte = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        
        # Corregido para asegurar nombres en español y orden estricto de fetch en SQLite
        cursor.execute(
            "SELECT report_id, latitud, longitud FROM reports WHERE created_at >= ?",
            (corte,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        clusters = []
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                try:
                    lat_i, lng_i = float(rows[i][1]), float(rows[i][2])
                    lat_j, lng_j = float(rows[j][1]), float(rows[j][2])
                    if abs(lat_i - lat_j) < 0.0005 and abs(lng_i - lng_j) < 0.0005:
                        clusters.append([rows[i][0], rows[j][0]])
                except (ValueError, TypeError):
                    continue # Ignora registros corruptos o vacíos de lat/lng de forma segura
        return {"clusters": len(clusters), "pares": clusters}
    except Exception as e:
        return {"clusters": 0, "pares": [], "error": str(e)}

@app.get("/public/stale-pendientes")
def public_stale_pendientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT report_id, created_at,
                   ROUND((julianday('now') - julianday(created_at)) * 1440) AS minutos
            FROM reports
            WHERE estado = 'PENDIENTE'
              AND (julianday('now') - julianday(created_at)) * 1440 > 30
            ORDER BY minutos DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [{"report_id": r[0], "created_at": r[1], "minutos": int(r[2])} for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/focos-activos")
def get_focos_activos():
    try:
        reports_table = get_reports_table()
        response = reports_table.scan()
        items = response.get('Items', [])
        
        # Coordenadas de la zona de operación (Valle del Sol, Chile central)
        LAT_MIN, LAT_MAX = -34.5, -32.5
        LNG_MIN, LNG_MAX = -71.5, -69.5
        
        focos = []
        for item in items:
            raw_lat = item.get('latitud')
            raw_lng = item.get('longitud')
            
            if not raw_lat or not raw_lng:
                continue
            try:
                lat = float(raw_lat)
                lng = float(raw_lng)
            except (ValueError, TypeError):
                continue
            if lat == 0 and lng == 0:
                continue
            if not (LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX):
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
        raise HTTPException(status_code=500, detail=f"Error fetching focos: {str(e)}")

@app.post("/sync")
def sync_from_lambda(req: SyncRequest, x_sync_token: str = Header(...)):
    """
    Endpoint Lambda Proxy para sincronización desde AWS Lambda.
    El body debe contener las claves obligatorias: table, operation y data.
    Usado exclusivamente por el trigger de DynamoDB Streams.
    """
    if x_sync_token != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid sync token")
    result = sync_to_sqlite(req.table, req.operation, req.data)
    return {"status": "synced", "operation": req.operation, "result": result}

def sync_to_sqlite(table: str, operation: str, data: dict) -> str:
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
                # Mapeo unificado usando 'report_id' seguro
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
        conn.close()
        return result
    except Exception as e:
        return f"error: {str(e)}"

# ==================== CIREN / CONAF BACKGROUND TASK ====================

async def fetch_ciren_data():
    url = (
        "https://esri.ciren.cl/server/rest/services/"
        "INCENDIOS_FORESTALES/FeatureServer/16/query"
        "?where=codreg+IN+(13,5,6)"
        "&outFields=nombre,region,comuna,provincia,superficie,"
        "causa_gene,fh_inicio,fh_extinci,temporada"
        "&f=geojson"
    )
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=30)
            data = r.json()

        conn = get_db_connection()
        cursor = conn.cursor()
        inserted = 0
        for feature in data.get("features", []):
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            cursor.execute("""
                INSERT OR IGNORE INTO external_reports
                (source, nombre, region, comuna, provincia, superficie, causa,
                 latitud, longitud, fh_inicio, fh_extinci, temporada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "CIREN", props.get("nombre"), props.get("region"),
                props.get("comuna"), props.get("provincia"),
                props.get("superficie"), props.get("causa_gene"),
                coords[1], coords[0],
                props.get("fh_inicio"), props.get("fh_extinci"),
                props.get("temporada")
            ))
            if cursor.rowcount > 0:
                inserted += 1
        conn.commit()
        conn.close()
        print(f"[CIREN] Fetched: {len(data.get('features', []))} features, {inserted} new")
    except Exception as e:
        print(f"[CIREN] Error: {e}")

async def periodic_fetch_ciren():
    await asyncio.sleep(30)
    while True:
        await fetch_ciren_data()
        await asyncio.sleep(3600)

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(periodic_fetch_ciren())

# ==================== NEW PUBLIC ENDPOINTS ====================

@app.get("/public/external-reports")
def public_external_reports(source: Optional[str] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if source:
            cursor.execute(
                "SELECT id, source, nombre, region, comuna, provincia, superficie, causa, latitud, longitud, fh_inicio, fh_extinci, temporada, fetched_at FROM external_reports WHERE source = ? ORDER BY fh_inicio DESC LIMIT 500",
                (source,)
            )
        else:
            cursor.execute("SELECT id, source, nombre, region, comuna, provincia, superficie, causa, latitud, longitud, fh_inicio, fh_extinci, temporada, fetched_at FROM external_reports ORDER BY fh_inicio DESC LIMIT 500")
        rows = cursor.fetchall()
        conn.close()
        columns = ["id", "source", "nombre", "region", "comuna", "provincia", "superficie", "causa", "lat", "lng", "fh_inicio", "fh_extinci", "temporada", "fetched_at"]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/public/external-reports/sources")
def public_external_reports_sources():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT source, COUNT(*) AS total FROM external_reports GROUP BY source ORDER BY total DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"source": r[0], "total": r[1]} for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/external-reports/trigger")
def trigger_external_fetch(authorization: Optional[str] = Header(None)):
    if not authorization or authorization.replace("Bearer ", "") != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fetch_ciren_data())
    loop.close()
    return {"status": "triggered"}

class ExternalReportRequest(BaseModel):
    source: str = "CIREN"
    nombre: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    provincia: Optional[str] = None
    superficie: Optional[float] = None
    causa: Optional[str] = None
    latitud: float
    longitud: float
    fh_inicio: Optional[str] = None
    fh_extinci: Optional[str] = None
    temporada: Optional[str] = None

@app.post("/api/v1/external-reports/conaf")
def receive_external_report(req: ExternalReportRequest, authorization: Optional[str] = Header(None)):
    if not authorization or authorization.replace("Bearer ", "") != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    try:
        conn = get_db_connection()
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
        conn.close()
        return {"status": "inserted", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/public/resources")
def public_resources():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.report_id, r.tipo, r.estado,
                   ir.tipo_recurso, ir.cantidad, ir.unidad
            FROM reports r
            LEFT JOIN incident_resources ir ON r.report_id = ir.report_id
            ORDER BY ir.created_at DESC
            LIMIT 20
        """)
        rows = cursor.fetchall()
        conn.close()
        return [{
            "report_id": r[0], "tipo": r[1], "estado": r[2],
            "recurso": r[3], "cantidad": r[4], "unidad": r[5]
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}

# ==================== AUTHENTICATED ENDPOINTS ====================

@app.get("/dashboard/stats")
def get_dashboard_stats(payload: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM reports")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
    by_estado = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
    by_tipo = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total": total,
        "by_estado": by_estado,
        "by_tipo": by_tipo
    }