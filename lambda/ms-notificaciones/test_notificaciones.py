import json
import os
import sys
import importlib.util

spec = importlib.util.spec_from_file_location(
    "notificaciones_app",
    os.path.join(os.path.dirname(__file__), "app.py")
)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)

from unittest.mock import patch

class TestMsNotificaciones:
    def test_send_notification_success(self):
        with patch.object(app, 'sns') as mock_sns:
            event = {
                "httpMethod": "POST",
                "body": json.dumps({
                    "message": "Incendio detectado",
                    "alert_type": "ALERTA",
                    "report_id": "r1"
                })
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["status"] == "sent"
            mock_sns.publish.assert_called_once()

    def test_send_notification_empty_message_returns_400(self):
        with patch.object(app, 'sns'):
            event = {
                "httpMethod": "POST",
                "body": json.dumps({"message": ""})
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 400
