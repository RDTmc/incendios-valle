#!/usr/bin/env python3
"""Test with known large image URL to confirm size theory."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)
print("Version:", dash['dashboard']['version'])

p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)

# simple test: just add a test row with a known 4000x3000 image
for t in p5['targets']:
    if t.get('refId') == 'A':
        t['rawQueryText'] = """SELECT report_id AS "ID", foto_url AS "Imagen", descripcion AS "Descripcion", tipo AS "Tipo", estado AS "Estado", created_at AS "Fecha" FROM reports WHERE foto_url IS NOT NULL AND foto_url != ''
UNION ALL
SELECT '99' AS "ID", 'https://picsum.photos/4000/3000' AS "Imagen", 'LARGE TEST 4000x3000' AS "Descripcion", 'test' AS "Tipo", 'activo' AS "Estado", datetime('now') AS "Fecha"
ORDER BY "Fecha" DESC LIMIT 15"""

# Reset to image cell type
overrides = p5['fieldConfig']['overrides']
for o in overrides:
    if o.get('matcher', {}).get('options') == 'Imagen':
        for prop in o['properties']:
            if prop['id'] == 'custom.cellOptions':
                prop['value'] = {'type': 'image'}
                print("Image cell type confirmed")

p5['options']['cellHeight'] = 300
p5['options']['footer']['enablePagination'] = False

patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_large_test.json"],
    input=patched, text=True
)

out2, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_large_test.json")
print("Update:", out2[:300])
