#!/usr/bin/env python3
"""Query datasource exactly as the Grafana table panel does."""
import subprocess, json, urllib.parse

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

# The exact payload that Grafana table panel would send
payload = json.dumps({
    "queries": [{
        "rawQueryText": "SELECT foto_url AS \"Imagen\" FROM reports WHERE foto_url IS NOT NULL AND foto_url != '' ORDER BY created_at DESC LIMIT 1",
        "refId": "A",
        "queryType": "table",
        "timeColumns": [],
        "datasource": {"type": "frser-sqlite-datasource", "uid": "incendios-sqlite"}
    }],
    "from": "now-1h",
    "to": "now"
})

subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/ds_query.json"],
    input=payload, text=True
)

out, err, rc = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/ds/query -H 'Content-Type: application/json' -d @/tmp/ds_query.json")

try:
    data = json.loads(out)
    frames = data.get('results', {}).get('A', {}).get('frames', [])
    if frames:
        vals = frames[0].get('data', {}).get('values', [])
        if vals and len(vals) > 0 and len(vals[0]) > 0:
            url = vals[0][0]
            print("URL from datasource:", url[:120])
            print("Has %25:", "%25" in url)
            print("Has %2B:", "%2B" in url)
            print("Full URL length:", len(url))
            # Check if URL decodes correctly
            decoded = urllib.parse.unquote(url)
            print("Decoded once:", decoded[:120])
            print("Decoded twice:", urllib.parse.unquote(decoded)[:120])
        else:
            print("No values in response")
            print(json.dumps(frames, indent=2)[:500])
    else:
        print("No frames in response")
        print(out[:500])
except Exception as e:
    print("Parse error:", e)
    print(out[:500])
