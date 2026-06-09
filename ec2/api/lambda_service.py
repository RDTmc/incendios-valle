import boto3
import json
import base64
import os

LAMBDA_FUNCTION_NAME = os.environ.get("LAMBDA_FUNCTION_NAME", "upload-proxy")

def get_lambda_client():
    return boto3.client("lambda")

def upload_image(file_bytes: bytes, content_type: str) -> str:
    client = get_lambda_client()
    payload = {
        "body": base64.b64encode(file_bytes).decode("utf-8"),
        "content_type": content_type,
    }
    response = client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    result = json.loads(response["Payload"].read().decode("utf-8"))
    if result.get("statusCode") != 200:
        raise RuntimeError(result.get("body", "Lambda invocation failed"))
    body = json.loads(result["body"])
    return body["foto_url"]
