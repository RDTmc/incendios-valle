#!/usr/bin/env python3
"""Check S3 image raw bytes more carefully."""
import subprocess, urllib.request

r = subprocess.run(
    ["docker", "exec", "incendios-api", "python3", "-c",
     "import sqlite3; conn = sqlite3.connect('/app/data/incendios.db'); "
     "r = conn.execute('SELECT foto_url FROM reports WHERE foto_url IS NOT NULL AND foto_url != \"\" ORDER BY created_at DESC LIMIT 1').fetchone(); "
     "print(r[0] if r else 'NONE')"],
    capture_output=True, text=True
)
url = r.stdout.strip()
print(f"URL length: {len(url)}")

req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = resp.read()
    print(f"Status: {resp.status}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Content-Length: {len(data)}")
    print(f"First 20 raw bytes: {list(data[:20])}")
    
    jpeg_header = b'\xff\xd8'
    is_jpeg = data[:2] == jpeg_header
    print(f"Is JPEG: {is_jpeg}")
    
    if is_jpeg:
        print("VALID JPEG header")
    else:
        print("NOT a JPEG! First bytes hex:", data[:10].hex())
        try:
            text = data[:200].decode('utf-8', errors='replace')
            print("As text:", text[:200])
        except:
            print("Cannot decode as text")
