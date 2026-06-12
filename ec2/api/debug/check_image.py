import urllib.request
import sqlite3
import struct

conn = sqlite3.connect("/app/data/incendios.db")
r = conn.execute("SELECT foto_url FROM reports ORDER BY created_at DESC LIMIT 1").fetchone()
url = r[0]

req = urllib.request.Request(url)
resp = urllib.request.urlopen(req, timeout=10)
data = resp.read()

print(f"Status: {resp.status}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")
print(f"Size: {len(data)} bytes")
print(f"First 4 hex: {data[:4].hex()}")
print(f"Is JPEG: {data[:2] == b'\\xff\\xd8'}")
if data[:2] == b'\xff\xd8':
    # Parse JPEG dimensions
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            break
        marker = data[pos+1]
        if marker == 0xC0 or marker == 0xC2:
            height = struct.unpack('>H', data[pos+5:pos+7])[0]
            width = struct.unpack('>H', data[pos+7:pos+9])[0]
            print(f"JPEG dimensions: {width}x{height}")
            break
        elif marker == 0xD9:
            break
        else:
            seg_len = struct.unpack('>H', data[pos+2:pos+4])[0]
            pos += 2 + seg_len
else:
    print("WARNING: Not a valid JPEG!")
    print(f"First 100 bytes: {data[:100]}")
