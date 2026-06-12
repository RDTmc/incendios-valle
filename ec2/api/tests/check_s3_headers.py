#!/usr/bin/env python3
"""Check S3 image response headers."""
import subprocess, json, urllib.request

# Get S3 URL from DB
r = subprocess.run(
    ["docker", "exec", "incendios-api", "python3", "-c",
     "import sqlite3; conn = sqlite3.connect('/app/data/incendios.db'); "
     "r = conn.execute('SELECT foto_url FROM reports WHERE foto_url IS NOT NULL AND foto_url != \"\" ORDER BY created_at DESC LIMIT 1').fetchone(); "
     "print(r[0] if r else 'NONE')"],
    capture_output=True, text=True
)
url = r.stdout.strip()
print("URL:", url[:80])

# Fetch with headers
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("Status:", resp.status)
        print("Headers:")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")
        data = resp.read()
        print(f"Body: {len(data)} bytes")
        print(f"First 4 hex: {data[:4].hex()}")
except Exception as e:
    print("Error:", e)
