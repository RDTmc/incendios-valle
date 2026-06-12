#!/usr/bin/env python3
"""Restore panel 5 to original query and clean up test data."""
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

# Restore original query
for t in p5['targets']:
    if t.get('refId') == 'A':
        t['rawQueryText'] = """SELECT report_id AS "ID", COALESCE(NULLIF(foto_url, ''), '') AS "Imagen", descripcion AS "Descripcion", tipo AS "Tipo", estado AS "Estado", created_at AS "Fecha" FROM reports ORDER BY created_at DESC LIMIT 10"""

# Ensure image cell type
for o in p5['fieldConfig']['overrides']:
    if o.get('matcher', {}).get('options') == 'Imagen':
        for prop in o['properties']:
            if prop['id'] == 'custom.cellOptions':
                prop['value'] = {'type': 'image'}

p5['options']['cellHeight'] = 300
p5['options']['footer']['enablePagination'] = False

# Remove sort by Imagen
p5['options']['sortBy'] = [{"desc": True, "displayName": "Fecha"}]

patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_clean.json"],
    input=patched, text=True
)

out2, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_clean.json")
print("Restored:", out2[:150])
