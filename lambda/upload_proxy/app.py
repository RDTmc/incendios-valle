import json
import base64
import boto3
import os
import uuid

S3_BUCKET = os.environ.get("S3_BUCKET", "incendios-valle-sol")

s3 = boto3.client("s3")

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        image_bytes = base64.b64decode(body.get("body", ""))
        content_type = body.get("content_type", "image/jpeg")

        ext = "jpg" if content_type == "image/jpeg" else "png"
        key = f"reportes/{uuid.uuid4().hex}.{ext}"

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )

        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=7200,
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"foto_url": url}),
            "headers": {"Content-Type": "application/json"},
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"},
        }
