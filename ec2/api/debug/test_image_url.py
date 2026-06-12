import urllib.request
import sqlite3

conn = sqlite3.connect("/app/data/incendios.db")
r = conn.execute("SELECT foto_url FROM reports ORDER BY created_at DESC LIMIT 1").fetchone()
url = r[0]

print("URL length:", len(url))
print("Testing URL from Python...")
try:
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=10)
    print("Status:", resp.status)
    print("Content-Type:", resp.headers.get("Content-Type"))
    data = resp.read()
    print("Body length:", len(data))
    if len(data) > 4:
        print("First 4 bytes (hex):", data[:4].hex())
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print("Body:", e.read()[:300])
