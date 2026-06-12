#!/bin/bash
# Run this on EC2 host
# It fetches the dashboard from Grafana, adds a test target, and updates

# Login to Grafana via docker exec
docker exec incendios-grafana sh -c "curl -s -c /tmp/c -X POST http://localhost:3000/login -H 'Content-Type: application/json' -d '{\"user\":\"admin\",\"password\":\"ValleSol2026!Secure\"}' > /dev/null"

# Fetch dashboard
docker exec incendios-grafana sh -c "curl -s -b /tmp/c http://localhost:3000/api/dashboards/uid/incendios-valle-main" > /tmp/dash.json
echo "Dashboard fetched: $(wc -c < /tmp/dash.json) bytes"

# Process with Python on the host
python3 << 'PYEOF'
import json

with open('/tmp/dash.json') as f:
    dash = json.load(f)

p5 = next((p for p in dash['dashboard']['panels'] if p.get('id') == 5), None)
if not p5:
    print('ERROR: Panel 5 not found')
    exit(1)

print('Panel 5:', p5.get('title'))
ds = p5['targets'][0].get('datasource', {}) if p5.get('targets') else {}
p5.setdefault('targets', []).append({
    'rawQueryText': "SELECT 'https://picsum.photos/200/300' AS \"Imagen\", 'TEST' AS \"Reporte\"",
    'refId': 'B',
    'datasource': ds,
    'format': 'table'
})

with open('/tmp/dash_patched.json', 'w') as f:
    json.dump(dash, f)
print('Patched and saved')
PYEOF

# Copy patched dashboard into container
docker cp /tmp/dash_patched.json incendios-grafana:/tmp/dash_patched.json

# POST update
docker exec incendios-grafana sh -c "curl -s -b /tmp/c -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_patched.json" | python3 -c "import json,sys;d=json.load(sys.stdin);print('Status:', d.get('status','?'))"
