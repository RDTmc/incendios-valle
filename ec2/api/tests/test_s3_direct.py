#!/usr/bin/env python3
"""Test: change the large test to use the S3 presigned URL directly to confirm diff."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)

p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)

# Get the actual S3 presigned URL from the DB via API container
r2 = subprocess.run(
    ["docker", "exec", "incendios-api", "python3", "-c",
     "import sqlite3; conn = sqlite3.connect('/app/data/incendios.db'); "
     "r = conn.execute('SELECT foto_url FROM reports WHERE foto_url IS NOT NULL AND foto_url != \"\" ORDER BY created_at DESC LIMIT 1').fetchone(); "
     "print(r[0] if r else 'NONE')"],
    capture_output=True, text=True
)
s3_url = r2.stdout.strip()
print("S3 URL:", s3_url[:80] if len(s3_url) > 10 else s3_url)

# Replace the test row with the actual S3 URL
for t in p5['targets']:
    if t.get('refId') == 'A':
        # Escape single quotes in the S3 URL for SQL
        escaped_url = s3_url.replace("'", "''")
        t['rawQueryText'] = (
            "SELECT report_id AS \"ID\", foto_url AS \"Imagen\", descripcion AS \"Descripcion\", tipo AS \"Tipo\", estado AS \"Estado\", created_at AS \"Fecha\" FROM reports WHERE foto_url IS NOT NULL AND foto_url != ''\n"
            "UNION ALL\n"
            f"SELECT '99' AS \"ID\", '{escaped_url}' AS \"Imagen\", 'S3 DIRECT TEST' AS \"Descripcion\", 'test' AS \"Tipo\", 'activo' AS \"Estado\", datetime('now') AS \"Fecha\"\n"
            "ORDER BY \"Fecha\" DESC LIMIT 15"
        )

# Ensure image cell type
overrides = p5['fieldConfig']['overrides']
for o in overrides:
    if o.get('matcher', {}).get('options') == 'Imagen':
        for prop in o['properties']:
            if prop['id'] == 'custom.cellOptions':
                prop['value'] = {'type': 'image'}

p5['options']['cellHeight'] = 300
p5['options']['footer']['enablePagination'] = False

patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_s3_test.json"],
    input=patched, text=True
)

out2, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_s3_test.json")
print("Update:", out2[:200])
