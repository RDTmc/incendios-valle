import os
import json
import boto3
import sqlite3
import http.client
import ssl
import urllib.request
from datetime import datetime, timezone

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:887513569063:incendios-alerts')
DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')
GRAFANA_INTERNAL = os.environ.get('GRAFANA_INTERNAL', 'http://incendios-grafana:3000')
GRAFANA_TOKEN = os.environ.get('GRAFANA_TOKEN', 'glsa_xzECDdWZO6ixPttXFZI3oGVfXD0XPmJR_5019d7a0')
MAILTRAP_TOKEN = os.environ.get('MAILTRAP_TOKEN', '')
MAILTRAP_SENDER = os.environ.get('MAILTRAP_SENDER', 'hello@demomailtrap.co')
MAILTRAP_SENDER_NAME = os.environ.get('MAILTRAP_SENDER_NAME', 'Incendios Valle del Sol')

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


def _send_email_via_mailtrap(to_email: str, subject: str, text: str, html: str = "") -> bool:
    if not MAILTRAP_TOKEN:
        print("[notifications] Mailtrap token not configured, skipping email")
        return False
    try:
        payload = json.dumps({
            "from": {"email": MAILTRAP_SENDER, "name": MAILTRAP_SENDER_NAME},
            "to": [{"email": to_email}],
            "subject": subject,
            "text": text,
            "html": html or "",
            "category": "welcome",
        })
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection("send.api.mailtrap.io", 443, context=ctx, timeout=10)
        conn.request("POST", "/api/send", body=payload, headers={
            "Authorization": f"Bearer {MAILTRAP_TOKEN}",
            "Content-Type": "application/json",
        })
        resp = conn.getresponse()
        body = resp.read().decode()
        if resp.status == 200:
            print(f"[notifications] Mailtrap email sent to {to_email}: {resp.status}")
            return True
        else:
            print(f"[notifications] Mailtrap error: {resp.status} {body[:200]}")
            return False
    except Exception as e:
        print(f"[notifications] Mailtrap error: {e}")
        return False


def _send_welcome_email(to_email: str, nombre: str, rol: str):
    name = nombre or to_email.split("@")[0]
    subject = "Bienvenido/a al Sistema de Alerta Temprana de Incendios"
    text = WELCOME_TEMPLATE.format(nombre=name, rol=rol)
    return _send_email_via_mailtrap(to_email, subject, text)


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

    # Send welcome email via Mailtrap
    email_ok = _send_welcome_email(email, nombre, rol)
    mailtrap_status = "sent" if email_ok else "skipped" if not MAILTRAP_TOKEN else "failed"

    # Save to SQLite notifications table
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notifications (type, recipient_email, recipient_name, message, status, sns_message_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("welcome", email, nombre or "", f"{welcome_msg}\n---\nMailtrap: {mailtrap_status}", status, sns_id),
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


def notify_status_change(report_id: str, estado_nuevo: str, admin_id: str, estado_anterior: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat()
    short_id = report_id[:8]
    short_admin = admin_id[:8]
    labels = {"PENDIENTE": "pendiente", "ACTIVO": "activo", "CONTROLADO": "controlado", "EXTINGUIDO": "extinguido"}
    tag = labels.get(estado_nuevo, "desconocido")

    # Grafana annotation directa (internal Docker network)
    _create_grafana_annotation(
        text=f"Reporte #{short_id}: {estado_anterior or '—'} → {estado_nuevo} (por admin {short_admin})",
        tags=["reporte", "cambio-estado", tag],
    )

    # SNS publish (email + Lambda sns-to-grafana)
    try:
        sns = boto3.client("sns")
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps({
                "text": f"Reporte #{short_id} cambió a {estado_nuevo} (admin {short_admin})",
                "tags": ["reporte", "cambio-estado", tag],
                "timestamp": now,
            }),
            Subject=f"[Incendios] Reporte {short_id} → {estado_nuevo}",
        )
    except Exception as e:
        print(f"[notifications] SNS publish error en notify_status_change: {e}")
