#!/usr/bin/env python3
"""Add test target to Panel 5 using basic auth."""
import json, subprocess, sys

AUTH = "admin:ValleSol2026!Secure"

def curl_in_grafana(args):
    """Run curl inside the grafana container with given args"""
    cmd = f'curl -s -u "{AUTH}" {args}'
    full = ["docker", "exec", "incendios-grafana", "sh", "-c", cmd]
    r = subprocess.run(full, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:", r.stderr[:200])
    return r.stdout

# Fetch dashboard
data = curl_in_grafana('http://localhost:3000/api/dashboards/uid/incendios-valle-main')
dash = json.loads(data)
print(f"Dashboard: {len(data)} bytes")

p5 = next((p for p in dash['dashboard']['panels'] if p.get('id') == 5), None)
if not p5:
    print("Panel 5 not found!")
    sys.exit(1)

print(f"Panel 5: {p5.get('title')}")
ds = p5['targets'][0].get('datasource', {}) if p5.get('targets') else {}
p5.setdefault('targets', []).append({
    'rawQueryText': "SELECT 'https://picsum.photos/200/300' AS \"Imagen\", 'TEST' AS \"Reporte\"",
    'refId': 'B',
    'datasource': ds,
    'format': 'table'
})

# Write patched JSON into container
patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_patched.json"],
    input=patched, text=True
)

# POST update
out = curl_in_grafana(
    '-X POST http://localhost:3000/api/dashboards/db '
    '-H "Content-Type: application/json" '
    '-d @/tmp/dash_patched.json'
)
print("Update:", out[:300])
