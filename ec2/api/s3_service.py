import boto3
import os
import uuid

S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "incendios-valle-uploads")

def get_s3_client():
    return boto3.client("s3")

def upload_image(file_bytes: bytes, content_type: str) -> str:
    ext = "jpg" if content_type == "image/jpeg" else "png"
    key = f"reportes/{uuid.uuid4().hex}.{ext}"
    client = get_s3_client()
    client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"
