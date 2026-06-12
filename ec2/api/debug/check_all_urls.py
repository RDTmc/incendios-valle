#!/usr/bin/env python3
"""Check ALL foto_urls from DB avoiding quoting issues."""
import subprocess, urllib.request

code = '''
import sqlite3
conn = sqlite3.connect("/app/data/incendios.db")
rows = conn.execute(
    "SELECT report_id, foto_url FROM reports "
    "WHERE foto_url IS NOT NULL AND foto_url != '' "
    "ORDER BY created_at DESC"
).fetchall()
print(f"COUNT:{len(rows)}")
for r in rows:
    print(f"ID:{r[0]}|URL:{r[1]}")
'''

r = subprocess.run(
    ["docker", "exec", "-i", "incendios-api", "python3"],
    input=code, text=True, capture_output=True
)
lines = r.stdout.strip().split('\n')
urls = []
for line in lines:
    if line.startswith("ID:"):
        parts = line.split("|URL:", 1)
        urls.append(parts[1])
    elif line.startswith("COUNT:"):
        print(f"Total records with URLs: {line}")

print(f"Parsed URLs: {len(urls)}")

for i, url in enumerate(urls):
    print(f"\n--- URL {i} ---")
    print(f"URL: {url[:80]}...")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            is_jpeg = data[:2] == b'\xff\xd8'
            print(f"  Status: {resp.status}, Size: {len(data)}, Valid JPEG: {is_jpeg}")
            if not is_jpeg:
                print(f"  First 20 hex: {data[:20].hex()}")
    except Exception as e:
        print(f"  Error: {e}")
