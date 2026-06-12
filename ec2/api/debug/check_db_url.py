#!/usr/bin/env python3
"""Check foto_url encoding in incendios.db (the one used by Grafana)."""
import subprocess

code = """
import sqlite3
conn = sqlite3.connect("/app/data/incendios.db")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
if ("reports",) in tables or "reports" in [t[0] for t in tables]:
    r = conn.execute("SELECT foto_url FROM reports WHERE foto_url IS NOT NULL AND foto_url != '' ORDER BY created_at DESC LIMIT 1").fetchone()
    if r:
        url = r[0]
        print("URL length:", len(url))
        print("Has %25:", "%25" in url)
        print("Has %2B:", "%2B" in url)
        print("Has %3D:", "%3D" in url)
        print("First 100:", url[:100])
        print("Last 50:", url[-50:])
    else:
        print("No foto_url found")
else:
    print("No reports table in incendios.db")
    # Try reports.db
    conn2 = sqlite3.connect("/app/data/reports.db")
    tables2 = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("reports.db tables:", [t[0] for t in tables2])
"""

r = subprocess.run(
    ["docker", "exec", "-i", "incendios-api", "python3"],
    input=code, text=True, capture_output=True
)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr[:500] if r.stderr else "")
