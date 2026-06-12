#!/usr/bin/env python3
"""Fix: set cellHeight to 300, add imageSize contain, remove test B."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

# 1. Fetch dashboard
out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)
print("Current version:", dash['dashboard']['version'])

p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)

# Remove test targets
p5['targets'] = [t for t in p5['targets'] if t.get('refId') != 'B']

# Set cellHeight to 300 (number)
p5['options']['cellHeight'] = 300

# Disable pagination
p5['options']['footer']['enablePagination'] = False

# Update image override to add imageSize
overrides = p5['fieldConfig']['overrides']
for o in overrides:
    if o.get('matcher', {}).get('options') == 'Imagen':
        for prop in o['properties']:
            if prop['id'] == 'custom.cellOptions':
                prop['value']['type'] = 'image'
                prop['value']['imageSize'] = 'contain'
                print("Set imageSize to contain")
                break

# 2. Write patched JSON
patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_final.json"],
    input=patched, text=True
)

# 3. POST update
out2, err2, rc2 = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_final.json")
print("Update result:", out2[:300])
