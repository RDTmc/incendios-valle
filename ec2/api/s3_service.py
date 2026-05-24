import boto3
import os
import uuid

S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "incendios-valle-sol")
PRESIGNED_EXPIRY = 7200  # 2 horas

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
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=PRESIGNED_EXPIRY,
    )
