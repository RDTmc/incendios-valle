import io
import pytest

class TestUpload:
    @pytest.mark.fast
    def test_upload_image_jpeg(self, client, mock_lambda_service):
        file_content = b'\xff\xd8\xff\xe0'  # JPEG magic bytes
        response = client.post("/reports/upload", files={
            "file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")
        })
        assert response.status_code == 200
        assert "foto_url" in response.json()

    @pytest.mark.fast
    def test_upload_image_png(self, client, mock_lambda_service):
        file_content = b'\x89PNG\r\n\x1a\n'
        response = client.post("/reports/upload", files={
            "file": ("test.png", io.BytesIO(file_content), "image/png")
        })
        assert response.status_code == 200

    @pytest.mark.fast
    def test_upload_invalid_mime_type(self, client, mock_lambda_service):
        response = client.post("/reports/upload", files={
            "file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")
        })
        assert response.status_code == 400
        assert "JPEG o PNG" in response.json()["detail"]

    @pytest.mark.fast
    def test_upload_file_too_large(self, client, mock_lambda_service):
        large_content = b'x' * (6 * 1024 * 1024)
        response = client.post("/reports/upload", files={
            "file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")
        })
        assert response.status_code == 400
        assert "5MB" in response.json()["detail"]
