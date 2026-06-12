#!/usr/bin/env python3
"""Set cellHeight to 300px, remove test target B."""
import json, subprocess

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)
print(f"Version: {dash['dashboard'].get('version')}")

p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)
p5['targets'] = [t for t in p5['targets'] if t.get('refId') != 'B']
p5['options']['cellHeight'] = '300px'

patched = json.dumps(dash)

# Write to container
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_patched.json"],
    input=patched, text=True
)

out2, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_patched.json")
print("Update:", out2[:300])
