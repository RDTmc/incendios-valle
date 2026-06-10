import os
import json
import boto3
import sqlite3
import urllib.request
from datetime import datetime, timezone

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:887513569063:incendios-alerts')
DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')
GRAFANA_INTERNAL = os.environ.get('GRAFANA_INTERNAL', 'http://incendios-grafana:3000')
GRAFANA_TOKEN = os.environ.get('GRAFANA_TOKEN', 'glsa_xzECDdWZO6ixPttXFZI3oGVfXD0XPmJR_5019d7a0')

WELCOME_TEMPLATE = """Estimado/a {nombre},

¡Bienvenido/a al Sistema de Alerta Temprana de Incendios de la Municipalidad de Valle del Sol!

Su registro como {rol} ha sido exitoso. A partir de ahora podrá:
- Reportar incendios forestales y urbanos en tiempo real
- Recibir alertas de emergencia en su correo
- Consultar el mapa de focos activos en la aplicación
- Acceder al historial de sus reportes

Ante cualquier emergencia, reporte de inmediato a través de la aplicación.

Atentamente,
Dirección de Gestión del Riesgo
Municipalidad de Valle del Sol"""


def _create_grafana_annotation(text: str, tags: list[str]):
    try:
        annotation = json.dumps({
            "text": text,
            "tags": tags,
            "time": int(datetime.now(timezone.utc).timestamp() * 1000),
        }).encode()
        req = urllib.request.Request(
            url=f"{GRAFANA_INTERNAL}/api/annotations",
            data=annotation,
            headers={
                "Authorization": f"Bearer {GRAFANA_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"[notifications] Grafana annotation created: {resp.status}")
    except Exception as e:
        print(f"[notifications] Grafana annotation error: {e}")


def notify_new_user(email: str, nombre: str = "", rol: str = "VECINO") -> dict:
    name = nombre or email.split("@")[0]
    welcome_msg = WELCOME_TEMPLATE.format(nombre=name, rol=rol)
    sns_subject = "[Admin Valle del Sol] Nuevo usuario registrado"
    now = datetime.now(timezone.utc).isoformat()

    # Publish to SNS (email subscribers)
    sns_msg = json.dumps({
        "text": f"Nuevo usuario: {email} ({nombre or '—'}) - Rol: {rol}",
        "tags": ["usuario", "registro", "admin"],
        "timestamp": now,
    })
    sns_id = ""
    status = "sent"

    try:
        sns = boto3.client("sns")
        resp = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=sns_msg,
            Subject=sns_subject,
        )
        sns_id = resp.get("MessageId", "")
    except Exception as e:
        print(f"[notifications] SNS publish error: {e}")
        status = "failed"

    # Create Grafana annotation directly (internal Docker network)
    _create_grafana_annotation(
        text=f"Nuevo usuario: {email} ({nombre or '—'}) - Rol: {rol}",
        tags=["usuario", "registro", "admin"],
    )

    # Save to SQLite notifications table
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notifications (type, recipient_email, recipient_name, message, status, sns_message_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("welcome", email, nombre or "", welcome_msg, status, sns_id),
        )
        conn.commit()
    except Exception as e:
        print(f"[notifications] DB insert error: {e}")
    finally:
        if conn is not None:
            conn.close()

    return {"status": status, "message_id": sns_id}


def notify_new_report(report_id: str, email: str = "", nombre: str = "", tipo: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat()
    reporter = nombre or email or "Anónimo"
    _create_grafana_annotation(
        text=f"Nuevo reporte #{report_id[:8]}: {tipo} por {reporter}",
        tags=["reporte", tipo.lower() if tipo else "general"],
    )
