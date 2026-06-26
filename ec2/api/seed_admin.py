import os, json, bcrypt, uuid, jwt, sqlite3, time, tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from pathlib import Path

os.environ['JWT_SECRET'] = 'test-secret-key-para-pruebas'
os.environ['SYNC_TOKEN'] = 'test-sync-token'
os.environ['AWS_S3_BUCKET'] = 'test-bucket'
os.environ['FIRMS_API_KEY'] = ''
os.environ['OWM_API_KEY'] = ''
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DB_PATH'] = tempfile.mkdtemp() + '/test_admin_prueba.db'

DB_PATH = os.environ['DB_PATH']
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH, timeout=5)
conn.execute("PRAGMA journal_mode=WAL")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, email TEXT UNIQUE, nombre TEXT, rol TEXT, created_at TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS reports (report_id TEXT PRIMARY KEY, user_id TEXT, tipo TEXT, latitud TEXT, longitud TEXT, geohash TEXT, descripcion TEXT, foto_url TEXT DEFAULT '', estado TEXT, created_at TEXT, updated_at TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS external_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT DEFAULT 'CIREN', nombre TEXT, region TEXT, comuna TEXT, provincia TEXT, superficie REAL, causa REAL, latitud REAL, longitud REAL, fh_inicio TEXT, fh_extinci TEXT, temporada TEXT, fetched_at TEXT DEFAULT (datetime('now')), UNIQUE(source, nombre, fh_inicio, latitud, longitud))")
cursor.execute("CREATE TABLE IF NOT EXISTS incident_resources (id INTEGER PRIMARY KEY AUTOINCREMENT, report_id TEXT NOT NULL, tipo_recurso TEXT NOT NULL, cantidad INTEGER DEFAULT 1, unidad TEXT DEFAULT '', estado TEXT DEFAULT 'ASIGNADO', created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (report_id) REFERENCES reports(report_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS firms_hotspots (id INTEGER PRIMARY KEY AUTOINCREMENT, latitude REAL, longitude REAL, brightness REAL, frp REAL, confidence TEXT, satellite TEXT, acq_date TEXT, acq_time INTEGER, daynight TEXT, source TEXT, fetched_at TEXT DEFAULT (datetime('now')), UNIQUE(latitude, longitude, acq_date, acq_time, satellite))")
cursor.execute("CREATE TABLE IF NOT EXISTS weather_readings (id INTEGER PRIMARY KEY AUTOINCREMENT, lat REAL, lon REAL, region TEXT, temperature REAL, humidity INTEGER, wind_speed REAL, wind_direction REAL, weather_desc TEXT, pressure INTEGER, fetched_at TEXT DEFAULT (datetime('now')))")
cursor.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT NOT NULL DEFAULT 'INFO', message TEXT NOT NULL, report_id TEXT DEFAULT '', latitud REAL DEFAULT 0, longitud REAL DEFAULT 0, source TEXT DEFAULT 'system', read INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))")
cursor.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, admin_id TEXT NOT NULL, target_id TEXT, details TEXT DEFAULT '', created_at TEXT NOT NULL)")
conn.commit()
conn.close()

conn = sqlite3.connect(DB_PATH, timeout=5)
cursor = conn.cursor()
seed_password = os.environ.get('SEED_ADMIN_PASSWORD', 'admin123')
password_hash = bcrypt.hashpw(seed_password.encode(), bcrypt.gensalt()).decode()
admin_user_id = str(uuid.uuid4())
timestamp = datetime.now(timezone.utc).isoformat()
cursor.execute(
    "INSERT INTO users (user_id, email, nombre, rol, created_at) VALUES (?, ?, ?, ?, ?)",
    (admin_user_id, 'admin@prueba.cl', 'Admin Prueba', 'ADMIN', timestamp)
)
conn.commit()
conn.close()

table_users = MagicMock()
table_reports = MagicMock()

def mock_query(**kwargs):
    if kwargs.get('IndexName') == 'email-index':
        email = kwargs.get('ExpressionAttributeValues', {}).get(':email')
        if email == 'admin@prueba.cl':
            return {'Items': [{
                'user_id': admin_user_id,
                'email': 'admin@prueba.cl',
                'password_hash': password_hash,
                'nombre': 'Admin Prueba',
                'rol': 'ADMIN',
                'created_at': timestamp,
            }]}
    return {'Items': []}

def mock_get_item(**kwargs):
    uid = kwargs.get('Key', {}).get('user_id')
    if uid == admin_user_id:
        return {'Item': {
            'user_id': admin_user_id,
            'email': 'admin@prueba.cl',
            'password_hash': password_hash,
            'nombre': 'Admin Prueba',
            'rol': 'ADMIN',
            'created_at': timestamp,
        }}
    return {}

def mock_scan(**kwargs):
    return {'Items': [{
        'user_id': admin_user_id,
        'email': 'admin@prueba.cl',
        'password_hash': password_hash,
        'nombre': 'Admin Prueba',
        'rol': 'ADMIN',
        'created_at': timestamp,
    }]}

table_users.query = mock_query
table_users.get_item = mock_get_item
table_users.scan = mock_scan
table_users.put_item = MagicMock()
table_users.update_item = MagicMock()
table_users.delete_item = MagicMock()
table_reports.scan.return_value = {'Items': []}
table_reports.query.return_value = {'Items': []}
table_reports.get_item.return_value = {}

patches = [
    patch('main.get_users_table', return_value=table_users),
    patch('main.get_reports_table', return_value=table_reports),
    patch('dependencies.get_users_table', return_value=table_users),
    patch('dependencies.get_reports_table', return_value=table_reports),
    patch('main.upload_image', return_value="https://test-bucket.s3.amazonaws.com/test.jpg"),
]
for p in patches:
    p.start()

import main
import uvicorn

token = jwt.encode({
    'user_id': admin_user_id,
    'email': 'admin@prueba.cl',
    'rol': 'ADMIN',
    'exp': datetime.now(timezone.utc) + timedelta(hours=24),
}, os.environ['JWT_SECRET'], algorithm='HS256')

print(f"ADMIN_USER_ID={admin_user_id}")
print(f"TOKEN={token}")
print(f"EMAIL=admin@prueba.cl")
print(f"PASSWORD=admin123")
print("SERVER_READY")

uvicorn.run(main.app, host='127.0.0.1', port=8000, log_level='warning')

for p in patches:
    p.stop()
