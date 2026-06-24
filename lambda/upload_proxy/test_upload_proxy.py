import json
import base64
import os
import sys
import importlib.util

spec = importlib.util.spec_from_file_location(
    "upload_proxy_app",
    os.path.join(os.path.dirname(__file__), "app.py")
)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)

from unittest.mock import patch

class TestUploadProxy:
    def test_upload_jpeg_success(self):
        with patch.object(app, 's3') as mock_s3:
            image_bytes = b'\xff\xd8\xff\xe0'
            event = {
                "body": base64.b64encode(image_bytes).decode(),
                "content_type": "image/jpeg"
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert "foto_url" in body
            assert body["foto_url"].startswith("reportes/")
            assert body["foto_url"].endswith(".jpg")
            mock_s3.put_object.assert_called_once()

    def test_upload_png_content_type(self):
        with patch.object(app, 's3') as mock_s3:
            image_bytes = b'\x89PNG\r\n\x1a\n'
            event = {
                "body": base64.b64encode(image_bytes).decode(),
                "content_type": "image/png"
            }
            result = app.lambda_handler(event, None)
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["foto_url"].endswith(".png")
