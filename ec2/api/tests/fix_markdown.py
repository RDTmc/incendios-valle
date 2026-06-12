#!/usr/bin/env python3
"""Try Markdown+HTML cell type with img tag to see if sanitization allows it."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

# Fetch dashboard
out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)
print("Version:", dash['dashboard']['version'])

p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)

# Change SQL to wrap foto_url in an img tag with max-width/max-height
for t in p5['targets']:
    if t.get('refId') == 'A':
        t['rawQueryText'] = """SELECT report_id AS "ID", 
'<img src="' || foto_url || '" style="max-width:250px;max-height:300px;object-fit:contain;width:auto;height:auto" alt="reporte" />' AS "Imagen", 
descripcion AS "Descripcion", tipo AS "Tipo", estado AS "Estado", created_at AS "Fecha" 
FROM reports ORDER BY created_at DESC LIMIT 10"""

# Change the Imagen override to use markdown+html cell type
overrides = p5['fieldConfig']['overrides']
for o in overrides:
    if o.get('matcher', {}).get('options') == 'Imagen':
        for prop in o['properties']:
            if prop['id'] == 'custom.cellOptions':
                prop['value'] = {'type': 'markdown'}
                print("Changed Imagen to markdown cell type")
            if prop['id'] == 'custom.width':
                prop['value'] = 250

# Reset cellHeight to manageable
p5['options']['cellHeight'] = 300
p5['options']['footer']['enablePagination'] = False

# Write and POST
patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_md.json"],
    input=patched, text=True
)

out2, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_md.json")
print("Update:", out2[:300])
