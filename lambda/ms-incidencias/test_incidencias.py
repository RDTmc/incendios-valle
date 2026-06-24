import json
import os
import sys
import importlib.util

spec = importlib.util.spec_from_file_location(
    "incidencias_app",
    os.path.join(os.path.dirname(__file__), "app.py")
)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)

from unittest.mock import patch

class TestMsIncidencias:
    def test_list_reports_returns_array(self):
        with patch.object(app, 'reports_table') as mock_table:
            mock_table.scan.return_value = {
                'Items': [
                    {'reports_id': 'r1', 'tipo': 'FORESTAL', 'estado': 'ACTIVO'}
                ]
            }
            event = {
                "httpMethod": "GET",
                "path": "/reports",
                "queryStringParameters": {}
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 200
            items = json.loads(result["body"])
            assert isinstance(items, list)
            assert len(items) == 1

    def test_get_report_not_found(self):
        with patch.object(app, 'reports_table') as mock_table:
            mock_table.query.return_value = {'Items': []}
            event = {
                "httpMethod": "GET",
                "path": "/reports/nonexistent"
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 404
