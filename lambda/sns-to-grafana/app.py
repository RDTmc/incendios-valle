import json
import os
import urllib.request
from datetime import datetime, timezone

GRAFANA_URL = os.environ.get('GRAFANA_URL', 'https://dashboard.keogh.lat/dashboard')
GRAFANA_TOKEN = os.environ['GRAFANA_TOKEN']

ANNOTATION_TEMPLATE = {
    "text": "",
    "tags": ["sistema", "alerta"],
    "time": 0,
}


def lambda_handler(event, context):
    try:
        for record in event.get('Records', []):
            sns_msg = json.loads(record['Sns']['Message'])
            text = sns_msg.get('text') or sns_msg.get('message', 'Evento sin descripción')
            tags = sns_msg.get('tags', ['sistema', 'alerta'])
            ts = sns_msg.get('timestamp', datetime.now(timezone.utc).isoformat())

            annotation = {
                "text": text,
                "tags": tags,
                "time": int(datetime.fromisoformat(ts).timestamp() * 1000),
            }

            req = urllib.request.Request(
                url=f"{GRAFANA_URL}/api/annotations",
                data=json.dumps(annotation).encode(),
                headers={
                    "Authorization": f"Bearer {GRAFANA_TOKEN}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[sns-to-grafana] Annotation created: {resp.read().decode()}")

        return {"statusCode": 200, "body": json.dumps({"status": "ok"})}

    except Exception as e:
        print(f"[sns-to-grafana] Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
