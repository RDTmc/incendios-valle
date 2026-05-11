from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import boto3
import hashlib
import jwt
import os
import uuid
from datetime import datetime, timedelta

app = FastAPI(title="Incendios API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table('users')
reports_table = dynamodb.Table('reports')

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
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/login")
def login(req: LoginRequest):
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    
    response = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': req.email}
    )
    
    user = response.get('Items', [None])[0]
    
    if not user or user.get('password_hash') != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({
        'user_id': user['user_id'],
        'email': user['email'],
        'rol': user.get('rol', 'VECINO'),
        'exp': datetime.utcnow() + timedelta(hours=24)
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

@app.post("/register")
def register(req: RegisterRequest):
    response = users_table.query(
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={':email': req.email}
    )
    
    if response.get('Items'):
        raise HTTPException(status_code=409, detail="User already exists")
    
    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    
    users_table.put_item(Item={
        'user_id': user_id,
        'email': req.email,
        'password_hash': password_hash,
        'nombre': req.nombre,
        'rol': req.rol,
        'created_at': datetime.utcnow().isoformat()
    })
    
    token = jwt.encode({
        'user_id': user_id,
        'email': req.email,
        'rol': req.rol,
        'exp': datetime.utcnow() + timedelta(hours=24)
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

@app.post("/reports")
def create_report(req: ReportRequest, payload: dict = Depends(verify_token)):
    report_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'report_id': report_id,
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
    
    return {
        "report_id": report_id,
        "estado": "PENDIENTE",
        "created_at": timestamp
    }

@app.get("/reports")
def list_reports(estado: str = None, user_id: str = None, payload: dict = Depends(verify_token)):
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

@app.get("/reports/{report_id}")
def get_report(report_id: str, payload: dict = Depends(verify_token)):
    response = reports_table.get_item(Key={'report_id': report_id})
    item = response.get('Item')
    
    if not item:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return item

@app.put("/reports/{report_id}")
def update_report(report_id: str, estado: str = None, descripcion: str = None, payload: dict = Depends(verify_token)):
    update_expr = "SET "
    expr_values = {}
    
    if estado:
        update_expr += "#estado = :estado, "
        expr_values[':estado'] = estado
    if descripcion:
        update_expr += "descripcion = :descripcion, "
        expr_values[':descripcion'] = descripcion
    
    update_expr += "updated_at = :updated_at"
    expr_values[':updated_at'] = datetime.utcnow().isoformat()
    
    expr_names = {"#estado": "estado"} if estado else None
    
    reports_table.update_item(
        Key={'report_id': report_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames=expr_names
    )
    
    response = reports_table.get_item(Key={'report_id': report_id})
    return response.get('Item', {})

@app.get("/health")
def health():
    return {"status": "ok"}