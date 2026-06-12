#!/usr/bin/env python3
"""Test: invoke Lambda directly with a valid JPEG and check the result."""
import subprocess, json, urllib.request

code = '''
import boto3, json, base64, urllib.request

# Download a known good JPEG
req = urllib.request.Request("https://picsum.photos/200/300")
with urllib.request.urlopen(req, timeout=15) as resp:
    jpeg_bytes = resp.read()

print(f"Original JPEG: {len(jpeg_bytes)} bytes, Valid: {jpeg_bytes[:2] == b'\\\\xff\\\\xd8'}")

# Invoke Lambda exactly as lambda_service does
client = boto3.client("lambda", region_name="us-east-1")
payload = {
    "body": base64.b64encode(jpeg_bytes).decode("utf-8"),
    "content_type": "image/jpeg",
}
response = client.invoke(
    FunctionName="upload-proxy",
    InvocationType="RequestResponse",
    Payload=json.dumps(payload),
)
result = json.loads(response["Payload"].read().decode("utf-8"))
print(f"Lambda status: {result.get('statusCode')}")

body = json.loads(result["body"])
url = body["foto_url"]
print(f"URL first 80: {url[:80]}")

# Verify the image via presigned URL
req2 = urllib.request.Request(url)
with urllib.request.urlopen(req2, timeout=15) as resp:
    data = resp.read()
    valid = data[:2] == b'\\\\xff\\\\xd8'
    print(f"Verify: Status={resp.status}, Size={len(data)}, Valid JPEG={valid}")
    if not valid:
        print(f"First 20 bytes: {list(data[:20])}")
        print(f"First 20 hex: {data[:20].hex()}")
'''

r = subprocess.run(
    ["docker", "exec", "incendios-api", "python3"],
    input=code, text=True, capture_output=True, timeout=30
)
print("STDOUT:", r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])
