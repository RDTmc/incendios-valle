import json
import os
import sys
import importlib.util

os.environ.setdefault('GRAFANA_TOKEN', 'test-token')
os.environ.setdefault('GRAFANA_URL', 'https://grafana.test')

spec = importlib.util.spec_from_file_location(
    "sns_to_grafana_app",
    os.path.join(os.path.dirname(__file__), "app.py")
)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)

from unittest.mock import patch, MagicMock

class TestSnsToGrafana:
    @patch.object(app, 'urllib')
    def test_sns_event_creates_annotation(self, mock_urllib):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"id": 1}'
        mock_urllib.request.urlopen.return_value.__enter__.return_value = mock_response

        event = {
            "Records": [{
                "Sns": {
                    "Message": json.dumps({
                        "text": "Incendio activo",
                        "tags": ["sistema", "incendio"],
                        "timestamp": "2026-06-20T12:00:00"
                    })
                }
            }]
        }
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 200
        mock_urllib.request.urlopen.assert_called_once()

    def test_sns_event_malformed_returns_500(self):
        event = {"Records": [{"Sns": {"Message": "not-json"}}]}
        result = app.lambda_handler(event, None)
        assert result["statusCode"] == 500
