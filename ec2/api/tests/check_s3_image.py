#!/usr/bin/env python3
"""Get the latest foto_url and check the image."""
import subprocess, struct, urllib.request

# Get foto_url from DB via API container
r = subprocess.run([
    "docker", "exec", "incendios-api", "python3", "-c",
    "import sqlite3; "
    "conn = sqlite3.connect('/app/data/reports.db'); "
    "r = conn.execute('SELECT foto_url FROM reports WHERE foto_url IS NOT NULL ORDER BY created_at DESC LIMIT 1').fetchone(); "
    "print(r[0] if r else '')"
], capture_output=True, text=True)

foto_url = r.stdout.strip()
print(f"URL from DB: {foto_url[:120]}...")

if not foto_url:
    print("No URL found")
    exit(1)

# Fetch the image
try:
    req = urllib.request.Request(foto_url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
        print(f"Status: {resp.status}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        print(f"Content-Length: {len(data)} bytes")
        print(f"First 4 hex: {data[:4].hex()}")

        if data[:2] == b'\xff\xd8':
            pos = 2
            width = height = 0
            while pos < len(data) - 1:
                if data[pos] != 0xFF:
                    break
                marker = data[pos+1]
                if marker in (0xC0, 0xC2):
                    height = struct.unpack('>H', data[pos+5:pos+7])[0]
                    width = struct.unpack('>H', data[pos+7:pos+9])[0]
                    print(f"JPEG dimensions: {width}x{height}")
                    break
                elif marker == 0xD9:
                    break
                else:
                    seg_len = struct.unpack('>H', data[pos+2:pos+4])[0]
                    if seg_len < 2:
                        break
                    pos += 2 + seg_len
            if width == 0:
                print("Could not parse JPEG dimensions")
        elif data[:4] == b'\x89PNG':
            width = struct.unpack('>I', data[16:20])[0]
            height = struct.unpack('>I', data[20:24])[0]
            print(f"PNG dimensions: {width}x{height}")
        elif data[:2] == b'GI':
            print("GIF format")
        else:
            print(f"Unknown format, first 20 hex: {data[:20].hex()}")

except Exception as e:
    print(f"Fetch error: {e}")
