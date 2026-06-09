import pytest
from unittest.mock import MagicMock, patch


class TestS3Service:
    @patch('s3_service.boto3.client')
    def test_get_s3_client(self, mock_boto_client):
        from s3_service import get_s3_client
        result = get_s3_client()
        mock_boto_client.assert_called_once_with("s3")
        assert result == mock_boto_client.return_value

    @patch('s3_service.boto3.client')
    def test_upload_image_jpeg(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/reportes/test.jpg"
        mock_boto_client.return_value = mock_s3

        from s3_service import upload_image
        result = upload_image(b'\xff\xd8\xff\xe0', "image/jpeg")

        mock_s3.put_object.assert_called_once()
        assert mock_s3.put_object.call_args[1]['Bucket'] == 'test-bucket'
        assert mock_s3.put_object.call_args[1]['Key'].startswith('reportes/')
        assert mock_s3.put_object.call_args[1]['Key'].endswith('.jpg')
        assert mock_s3.put_object.call_args[1]['ContentType'] == 'image/jpeg'
        mock_s3.generate_presigned_url.assert_called_once()
        assert result == "https://test-bucket.s3.amazonaws.com/reportes/test.jpg"

    @patch('s3_service.boto3.client')
    def test_upload_image_png(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/reportes/test.png"
        mock_boto_client.return_value = mock_s3

        from s3_service import upload_image
        result = upload_image(b'\x89PNG\r\n\x1a\n', "image/png")

        assert mock_s3.put_object.call_args[1]['Key'].endswith('.png')
        assert mock_s3.put_object.call_args[1]['ContentType'] == 'image/png'
        assert result == "https://test-bucket.s3.amazonaws.com/reportes/test.png"


class TestLambdaService:
    @patch('lambda_service.boto3.client')
    def test_get_lambda_client(self, mock_boto_client):
        from lambda_service import get_lambda_client
        result = get_lambda_client()
        mock_boto_client.assert_called_once_with("lambda")
        assert result == mock_boto_client.return_value

    @patch('lambda_service.boto3.client')
    def test_upload_image_success(self, mock_boto_client):
        mock_lambda = MagicMock()
        mock_payload = MagicMock()
        mock_payload.read.return_value = b'{"statusCode": 200, "body": "{\\"foto_url\\": \\"https://test.url/photo.jpg\\"}"}'
        mock_lambda.invoke.return_value = {"Payload": mock_payload}
        mock_boto_client.return_value = mock_lambda

        from lambda_service import upload_image
        result = upload_image(b'test-image-data', "image/jpeg")

        mock_lambda.invoke.assert_called_once()
        assert result == "https://test.url/photo.jpg"

    @patch('lambda_service.boto3.client')
    def test_upload_image_failure(self, mock_boto_client):
        mock_lambda = MagicMock()
        mock_payload = MagicMock()
        mock_payload.read.return_value = b'{"statusCode": 500, "body": "Internal error"}'
        mock_lambda.invoke.return_value = {"Payload": mock_payload}
        mock_boto_client.return_value = mock_lambda

        from lambda_service import upload_image
        with pytest.raises(RuntimeError, match="Internal error"):
            upload_image(b'test-image-data', "image/png")
