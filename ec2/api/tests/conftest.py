import pytest
import sys
import os
import sqlite3
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ['JWT_SECRET'] = 'test-secret-key'
os.environ['SYNC_TOKEN'] = 'test-sync-token'
os.environ['AWS_S3_BUCKET'] = 'test-bucket'
os.environ['FIRMS_API_KEY'] = ''
os.environ['OWM_API_KEY'] = ''
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

DB_PATH = "/tmp/test_incendios.db"
os.environ['DB_PATH'] = DB_PATH

@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

@pytest.fixture
def db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=DELETE")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, email TEXT UNIQUE, nombre TEXT, rol TEXT, created_at TEXT, password_hash TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS reports (report_id TEXT PRIMARY KEY, user_id TEXT, tipo TEXT, latitud TEXT, longitud TEXT, geohash TEXT, descripcion TEXT, foto_url TEXT DEFAULT '', estado TEXT, created_at TEXT, updated_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS external_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT DEFAULT 'CIREN', nombre TEXT, region TEXT, comuna TEXT, provincia TEXT, superficie REAL, causa TEXT, latitud REAL, longitud REAL, fh_inicio TEXT, fh_extinci TEXT, temporada TEXT, fetched_at TEXT DEFAULT (datetime('now')), UNIQUE(source, nombre, fh_inicio, latitud, longitud))")
    cursor.execute("CREATE TABLE IF NOT EXISTS incident_resources (id INTEGER PRIMARY KEY AUTOINCREMENT, report_id TEXT NOT NULL, tipo_recurso TEXT NOT NULL, cantidad INTEGER DEFAULT 1, unidad TEXT DEFAULT '', estado TEXT DEFAULT 'ASIGNADO', created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (report_id) REFERENCES reports(report_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS firms_hotspots (id INTEGER PRIMARY KEY AUTOINCREMENT, latitude REAL, longitude REAL, brightness REAL, frp REAL, confidence TEXT, satellite TEXT, acq_date TEXT, acq_time INTEGER, daynight TEXT, source TEXT, fetched_at TEXT DEFAULT (datetime('now')), UNIQUE(latitude, longitude, acq_date, acq_time, satellite))")
    cursor.execute("CREATE TABLE IF NOT EXISTS weather_readings (id INTEGER PRIMARY KEY AUTOINCREMENT, lat REAL, lon REAL, region TEXT, temperature REAL, humidity INTEGER, wind_speed REAL, wind_direction REAL, weather_desc TEXT, pressure INTEGER, fetched_at TEXT DEFAULT (datetime('now')))")
    cursor.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT NOT NULL DEFAULT 'INFO', message TEXT NOT NULL, report_id TEXT DEFAULT '', latitud REAL DEFAULT 0, longitud REAL DEFAULT 0, source TEXT DEFAULT 'system', read INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')))")
    cursor.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, admin_id TEXT NOT NULL, target_id TEXT, details TEXT DEFAULT '', created_at TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, recipient_email TEXT NOT NULL, recipient_name TEXT DEFAULT '', message TEXT NOT NULL, status TEXT DEFAULT 'sent', sns_message_id TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')))")
    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def mock_dynamodb():
    table_users = MagicMock()
    table_reports = MagicMock()
    with patch('main.get_users_table', return_value=table_users) as mu, \
         patch('main.get_reports_table', return_value=table_reports) as mr, \
         patch('dependencies.get_users_table', return_value=table_users), \
         patch('dependencies.get_reports_table', return_value=table_reports):
        yield table_users, table_reports

@pytest.fixture
def mock_lambda_service():
    with patch('main.upload_image') as mock:
        mock.return_value = "https://test-bucket.s3.amazonaws.com/test.jpg"
        yield mock

@pytest.fixture(autouse=True)
def mock_sns():
    with patch('notification_service.boto3.client') as mock:
        sns_mock = MagicMock()
        sns_mock.publish.return_value = {"MessageId": "mock-sns-id-123"}
        mock.return_value = sns_mock
        yield sns_mock

@pytest.fixture
def client(mock_dynamodb, db_connection):
    from main import app
    from fastapi.testclient import TestClient
    test_client = TestClient(app)
    return test_client
