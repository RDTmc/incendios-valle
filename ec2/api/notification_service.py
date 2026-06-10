import os
import boto3
import sqlite3
from datetime import datetime, timezone

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:887513569063:incendios-alerts')
DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')

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


def notify_new_user(email: str, nombre: str = "", rol: str = "VECINO") -> dict:
    name = nombre or email.split("@")[0]
    welcome_msg = WELCOME_TEMPLATE.format(nombre=name, rol=rol)
    sns_subject = "[Admin Valle del Sol] Nuevo usuario registrado"
    sns_msg = (
        f"Nuevo usuario registrado en el Sistema de Alerta Temprana.\n\n"
        f"Email: {email}\n"
        f"Nombre: {nombre or '—'}\n"
        f"Rol: {rol}\n"
        f"Hora: {datetime.now(timezone.utc).isoformat()}"
    )
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
