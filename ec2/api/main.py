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
import json

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
    conn = sqlite3.connect(DB_PATH, timeout=5)
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

S3_BACKUP_PATH = "/app/data/backups"
SEED_PATH = "/app/data/seed.json"

def backup_sqlite_to_s3():
    """Sube incendios.db a S3 como respaldo"""
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
    """Intenta restaurar incendios.db desde S3 si esta vacio"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM external_reports")
    count = cursor.fetchone()[0]
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
    """Exporta external_reports a seed.json para post-reset"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, region, comuna, provincia, superficie, causa, latitud, longitud, fh_inicio, fh_extinci, temporada FROM external_reports ORDER BY fh_inicio DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
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

def load_seed_if_empty():
    """Carga seed.json si external_reports esta vacio"""
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
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=30)
            data = r.json()

        conn = get_db_connection()
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

# ==================== NASA FIRMS BACKGROUND TASK ====================

FIRMS_BBOX = "-72.5,-35.0,-69.5,-32.5"
FIRMS_SOURCES = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]

async def fetch_firms_hotspots():
    api_key = os.environ.get('FIRMS_API_KEY', '')
    if not api_key:
        print("[FIRMS] No API key configured")
        return
    for source in FIRMS_SOURCES:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/json/{api_key}/{source}/{FIRMS_BBOX}/2"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=30)
            if r.status_code != 200:
                print(f"[FIRMS] {source}: HTTP {r.status_code}")
                continue
            data = r.json()
            if not isinstance(data, list):
                continue
            conn = get_db_connection()
            cursor = conn.cursor()
            inserted = 0
            for item in data:
                cursor.execute("""
                    INSERT OR IGNORE INTO firms_hotspots
                    (latitude, longitude, brightness, frp, confidence, satellite, acq_date, acq_time, daynight, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("latitude"), item.get("longitude"),
                    item.get("brightness"), item.get("frp"),
                    str(item.get("confidence", "")),
                    item.get("satellite", ""),
                    item.get("acq_date", ""),
                    item.get("acq_time"),
                    item.get("daynight", ""), source
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            conn.commit()
            conn.close()
            print(f"[FIRMS] {source}: {len(data)} received, {inserted} new")
        except Exception as e:
            print(f"[FIRMS] Error {source}: {e}")

async def periodic_fetch_firms():
    await asyncio.sleep(60)
    while True:
        await fetch_firms_hotspots()
        await asyncio.sleep(1800)

# ==================== OPENWEATHERMAP BACKGROUND TASK ====================

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
    async with httpx.AsyncClient() as client:
        for zone in WEATHER_ZONES:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={zone['lat']}&lon={zone['lon']}&units=metric&appid={api_key}"
            try:
                r = await client.get(url, timeout=15)
                if r.status_code != 200:
                    print(f"[OWM] {zone['region']}: HTTP {r.status_code}")
                    continue
                data = r.json()
                conn = get_db_connection()
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
    asyncio.create_task(periodic_fetch_ciren())
    asyncio.create_task(periodic_fetch_firms())
    asyncio.create_task(periodic_fetch_weather())

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

@app.get("/public/firms-hotspots")
def public_firms_hotspots():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT latitude, longitude, brightness, frp, confidence,
                   satellite, acq_date, acq_time, source, fetched_at
            FROM firms_hotspots
            WHERE fetched_at >= datetime('now', '-3 days')
            ORDER BY acq_date DESC, acq_time DESC
            LIMIT 1000
        """)
        rows = cursor.fetchall()
        conn.close()
        columns = ["lat", "lng", "brightness", "frp", "confidence",
                   "satellite", "acq_date", "acq_time", "source", "fetched_at"]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/public/weather/latest")
def public_weather_latest():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w1.region, w1.temperature, w1.humidity, w1.wind_speed,
                   w1.wind_direction, w1.weather_desc, w1.pressure, w1.fetched_at
            FROM weather_readings w1
            WHERE w1.id IN (SELECT MAX(id) FROM weather_readings GROUP BY region)
            ORDER BY w1.region
        """)
        rows = cursor.fetchall()
        conn.close()
        columns = ["region", "temperature", "humidity", "wind_speed",
                   "wind_direction", "weather_desc", "pressure", "fetched_at"]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/public/weather/history")
def public_weather_history(limit: int = 50):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT region, temperature, humidity, wind_speed,
                   wind_direction, weather_desc, fetched_at
            FROM weather_readings
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        columns = ["region", "temperature", "humidity", "wind_speed",
                   "wind_direction", "weather_desc", "fetched_at"]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/external-reports/trigger")
async def trigger_external_fetch(authorization: Optional[str] = Header(None)):
    if not authorization or authorization.replace("Bearer ", "") != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    asyncio.create_task(fetch_ciren_data())
    return {"status": "triggered", "message": "Fetch iniciado en background"}

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

@app.post("/v1/external-reports/conaf")
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