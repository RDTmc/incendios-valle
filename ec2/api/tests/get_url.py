#!/usr/bin/env python3
import subprocess, struct, json

# Run inside API container to query foto_url from the DB
cmd = ["docker", "exec", "incendios-api", "python3", "-c", """
import sqlite3
conn = sqlite3.connect('/app/data/reports.db')
try:
    r = conn.execute("SELECT foto_url FROM reports WHERE foto_url != '' AND foto_url IS NOT NULL ORDER BY created_at DESC LIMIT 1").fetchone()
    if r: print(r[0])
    else:
        r = conn.execute("SELECT foto_url FROM reports LIMIT 1").fetchone()
        print(r[0] if r else 'NO_ROWS')
except Exception as e:
    print('ERR:', e)
"""]
r = subprocess.run(cmd, capture_output=True, text=True)
foto_url = r.stdout.strip()
print(f"URL: {foto_url[:150] if len(foto_url) > 10 else foto_url}")

if 'http' not in foto_url:
    # Try incendios.db instead
    cmd2 = ["docker", "exec", "incendios-api", "python3", "-c", """
import sqlite3
conn = sqlite3.connect('/app/data/incendios.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
for t in tables:
    cnt = conn.execute("SELECT COUNT(*) FROM " + t[0]).fetchone()[0]
    if cnt > 0:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(" + t[0] + ")").fetchall()]
        sample = conn.execute("SELECT * FROM " + t[0] + " LIMIT 1").fetchone()
        print(f"{t[0]}: {cnt} rows, cols={cols}, sample={sample}")
"""]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    print(r2.stdout)
    if r2.stderr:
        print("STDERR:", r2.stderr[:300])
