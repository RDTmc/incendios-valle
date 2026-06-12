#!/usr/bin/env python3
"""Check and fix API Gateway binary handling for multipart uploads."""
import subprocess, json

API_ID = "jywf027zj3"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        print(f"Error: {r.stderr}")
    return json.loads(r.stdout) if r.stdout else None

# Get resources
resources = run(f"aws apigateway get-resources --rest-api-id {API_ID} --query 'items[?path==`/api/{proxy+}`].id' --output json")
print("Resources:", resources)

# Actually let me use a simpler approach
res = subprocess.run(
    ["aws", "apigateway", "get-resources", "--rest-api-id", API_ID,
     "--query", "items[?path=='/api/{proxy+}'].id", "--output", "text"],
    capture_output=True, text=True
)
proxy_id = res.stdout.strip()
print(f"Proxy resource ID: {proxy_id}")

# Get integration
res2 = subprocess.run(
    ["aws", "apigateway", "get-integration", "--rest-api-id", API_ID,
     "--resource-id", proxy_id, "--http-method", "ANY"],
    capture_output=True, text=True
)
print(f"Integration:\n{res2.stdout[:500]}")
if res2.stderr:
    print(f"Stderr: {res2.stderr}")

# Get method
res3 = subprocess.run(
    ["aws", "apigateway", "get-method", "--rest-api-id", API_ID,
     "--resource-id", proxy_id, "--http-method", "ANY"],
    capture_output=True, text=True
)
print(f"Method:\n{res3.stdout[:500]}")
