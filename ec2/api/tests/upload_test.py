#!/usr/bin/env python3
"""Upload a test JPEG to S3 and verify it works."""
import subprocess

code = '''
import boto3, urllib.request, uuid

req = urllib.request.Request("https://picsum.photos/200/300")
with urllib.request.urlopen(req, timeout=15) as resp:
    jpeg_bytes = resp.read()

is_jpeg = jpeg_bytes[:2] == b"\\xff\\xd8"
print("Downloaded: %d bytes, Valid JPEG: %s" % (len(jpeg_bytes), is_jpeg))
if not is_jpeg:
    print("First bytes:", list(jpeg_bytes[:10]))
    exit(1)

s3 = boto3.client("s3", region_name="us-east-1")
key = "reportes/test_%s.jpg" % uuid.uuid4().hex
s3.put_object(Bucket="incendios-valle-sol", Key=key, Body=jpeg_bytes, ContentType="image/jpeg")
print("Uploaded:", key)

url = s3.generate_presigned_url("get_object", Params={"Bucket": "incendios-valle-sol", "Key": key}, ExpiresIn=604800)
print("URL first 100:", url[:100])
print("URL len:", len(url))

req2 = urllib.request.Request(url)
with urllib.request.urlopen(req2, timeout=15) as resp:
    data = resp.read()
    valid2 = data[:2] == b"\\xff\\xd8"
    print("Verify: Status=%d, Size=%d, Valid JPEG=%s" % (resp.status, len(data), valid2))
    if not valid2:
        print("First 20 bytes:", list(data[:20]))

print("KEY=" + key)
print("URL=" + url)
'''

r = subprocess.run(
    ["docker", "exec", "incendios-api", "python3"],
    input=code, text=True, capture_output=True, timeout=30
)
print("STDOUT:")
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:1000])
