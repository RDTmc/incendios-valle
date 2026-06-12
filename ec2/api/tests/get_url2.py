#!/usr/bin/env python3
import sqlite3, subprocess, struct, urllib.request, json

# Run script inside API container to query ALL foto_urls
code = """
import sqlite3, json
conn = sqlite3.connect('/app/data/reports.db')
try:
    rows = conn.execute("SELECT report_id, foto_url FROM reports WHERE foto_url IS NOT NULL AND foto_url != '' ORDER BY created_at DESC LIMIT 5").fetchall()
    print(json.dumps([{"id": r[0], "url": r[1][:80]} for r in rows]))
except Exception as e:
    print('ERR:' + str(e))
"""

r = subprocess.run(["docker", "exec", "incendios-api", "python3", "-c", code], capture_output=True, text=True)
print("API container result:", r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:200])

# Try from the host - maybe the db is in a volume?
r2 = subprocess.run(["docker", "inspect", "incendios-api", "--format", "{{json .Mounts}}"], capture_output=True, text=True)
print("\nMounts:", r2.stdout[:500])
