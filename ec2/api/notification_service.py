import os
import json
import boto3
import sqlite3

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:887513569063:incendios-alerts')
DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')

WELCOME_SUBJECT = "[Municipalidad Valle del Sol] Bienvenido al Sistema de Alerta Temprana"

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


def send_welcome_notification(email: str, nombre: str = "", rol: str = "VECINO") -> dict:
    name = nombre or email.split("@")[0]
    message = WELCOME_TEMPLATE.format(nombre=name, rol=rol)
    sns_id = ""
    status = "sent"

    try:
        sns = boto3.client("sns")
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=WELCOME_SUBJECT,
        )
        sns_id = response.get("MessageId", "")
    except Exception as e:
        print(f"[notifications] SNS publish error: {e}")
        status = "failed"

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notifications (type, recipient_email, recipient_name, message, status, sns_message_id) VALUES (?, ?, ?, ?, ?, ?)",
            ("welcome", email, nombre or "", message, status, sns_id),
        )
        conn.commit()
    except Exception as e:
        print(f"[notifications] DB insert error: {e}")
    finally:
        if conn is not None:
            conn.close()

    return {"status": status, "message_id": sns_id}
