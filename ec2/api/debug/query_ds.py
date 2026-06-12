#!/usr/bin/env python3
"""Query the Grafana datasource directly to see what value is returned."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

# Query the datasource API directly
query_payload = json.dumps({
    "queries": [{
        "rawQueryText": "SELECT foto_url AS \"Imagen\" FROM reports WHERE foto_url IS NOT NULL AND foto_url != '' ORDER BY created_at DESC LIMIT 3",
        "refId": "A",
        "format": "table",
        "datasource": {"type": "frser-sqlite-datasource", "uid": "incendios-sqlite"}
    }],
    "from": "now-1h",
    "to": "now"
})

# Write query payload to container
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/query.json"],
    input=query_payload, text=True
)

# POST the query
out, err, rc = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/ds/query -H 'Content-Type: application/json' -d @/tmp/query.json")
print("Response length:", len(out))
print("First 2000 chars:", out[:2000])

# Parse and show the actual value
try:
    data = json.loads(out)
    frames = data.get('results', {}).get('A', {}).get('frames', [])
    if frames:
        values = frames[0].get('data', {}).get('values', [])
        if values and len(values) > 0:
            url = values[0][0]
            print("\n\n=== ACTUAL URL FROM DATASOURCE ===")
            print("Has %25:", "%25" in url)
            print("Has %2B:", "%2B" in url)
            print("First 100:", url[:100])
            print("Last 50:", url[-50:])
except Exception as e:
    print("Parse error:", e)
