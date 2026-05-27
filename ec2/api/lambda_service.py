import boto3
import json
import base64
import os

LAMBDA_FUNCTION_NAME = os.environ.get("LAMBDA_FUNCTION_NAME", "upload-proxy")

def get_lambda_client():
    return boto3.client("lambda")

def upload_image(file_bytes: bytes, content_type: str) -> str:
    client = get_lambda_client()
    # Enviar solo el string base64 crudo, sin wrapper JSON.
    # La Lambda upload-proxy recibe el base64 directamente en event.
    raw_b64 = base64.b64encode(file_bytes).decode("utf-8")
    response = client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=raw_b64.encode("utf-8"),
    )
    result = json.loads(response["Payload"].read().decode("utf-8"))
    if result.get("statusCode") != 200:
        raise Exception(result.get("body", "Lambda invocation failed"))
    body = json.loads(result["body"])
    return body["foto_url"]
