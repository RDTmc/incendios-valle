from fastapi import FastAPI, HTTPException, Depends, Header
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

# Configuración DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('users')
reports_table = dynamodb.Table('reports')

# Configuración SQLite
DB_PATH = "/app/data/incendios.db"
SYNC_TOKEN = os.environ.get('SYNC_TOKEN', 'incendios-sync-secret-token')

Path("/app/data").mkdir(parents=True, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
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
            estado TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

SECRET_KEY = os.environ.get('JWT_SECRET', 'incendios-valle-secret-key')

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str = ""
    rol: str = "VECINO"

class ReportRequest(BaseModel):
    user_id: str
    tipo: str = "INCENDIO"
    latitud: float
    longitud: float
    descripcion: str = ""

class SyncRequest(BaseModel):
    table: str
    operation: str
    data: dict

def encode_geohash(lat, lon):
    lat_hash = int(lat * 1000000)
    lon_hash = int(lon * 1000000)
    return f"{lat_hash // 1000}-{lon_hash // 1000}"

def verify_token(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== ENDPOINTS ====================

@app.post("/login")
def login(req: LoginRequest):
    try:
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
        
        # bcrypt check
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
def create_report(req: ReportRequest, payload: dict = Depends(verify_token)):
    try:
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        item = {
            'reports_id': report_id,
            'user_id': req.user_id,
            'tipo': req.tipo,
            'latitud': str(req.latitud),
            'longitud': str(req.longitud),
            'geohash': encode_geohash(req.latitud, req.longitud),
            'descripcion': req.descripcion,
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

@app.get("/reports")
def list_reports(estado: str = None, user_id: str = None, payload: dict = Depends(verify_token)):
    try:
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
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List reports error: {str(e)}")

@app.get("/reports/{report_id}")
def get_report(report_id: str, payload: dict = Depends(verify_token)):
    try:
        response = reports_table.get_item(Key={'reports_id': report_id})
        item = response.get('Item')
        if not item:
            raise HTTPException(status_code=404, detail="Report not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get report error: {str(e)}")

@app.put("/reports/{report_id}")
def update_report(report_id: str, estado: str = None, descripcion: str = None, payload: dict = Depends(verify_token)):
    try:
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
        
        reports_table.update_item(
            Key={'reports_id': report_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names if expr_names else None
        )
        
        response = reports_table.get_item(Key={'reports_id': report_id})
        return response.get('Item', {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update report error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/focos-activos")
def get_focos_activos():
    try:
        response = reports_table.scan()
        items = response.get('Items', [])
        
        focos = []
        for item in items:
            focos.append({
                'id': item.get('reports_id', ''),
                'lat': float(item.get('latitud', 0)),
                'lng': float(item.get('longitud', 0)),
                'estado': item.get('estado', 'DESCONOCIDO'),
                'tipo': item.get('tipo', 'FORESTAL'),
                'created_at': item.get('created_at', '')
            })
        
        return focos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching focos: {str(e)}")

@app.post("/sync")
def sync_from_lambda(req: SyncRequest, x_sync_token: str = Header(...)):
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
                cursor.execute('''
                    INSERT OR REPLACE INTO reports
                    (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, estado, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (data.get('report_id'), data.get('user_id'), data.get('tipo'),
                      data.get('latitud'), data.get('longitud'), data.get('geohash'),
                      data.get('descripcion'), data.get('estado'),
                      data.get('created_at'), data.get('updated_at')))
            result = "report synced"
        else:
            result = "unknown table"
        
        conn.commit()
        conn.close()
        return result
    except Exception as e:
        return f"error: {str(e)}"

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
