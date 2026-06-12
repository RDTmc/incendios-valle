#!/usr/bin/env python3
"""Debug: check raw output from DB query."""
import subprocess

r = subprocess.run(
    ["docker", "exec", "incendios-api", "python3", "-c",
     "import sqlite3; conn = sqlite3.connect('/app/data/incendios.db'); "
     "rows = conn.execute('SELECT report_id, foto_url FROM reports WHERE foto_url IS NOT NULL AND foto_url != \"\" ORDER BY created_at DESC').fetchall(); "
     "print(f'Row count: {len(rows)}'); "
     "for i, row in enumerate(rows): print(f'  [{i}] ID={row[0]}, foto_url present={bool(row[1])}, foto_url[:60]={row[1][:60] if row[1] else \"NONE\"}')"],
    capture_output=True, text=True
)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr[:500] if r.stderr else "")
