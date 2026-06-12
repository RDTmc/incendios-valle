#!/usr/bin/env python3
"""Remove data links from Grafana panel 5 Imagen field to avoid double encoding."""
import json, sys, urllib.request, base64

GRAFANA_URL = "http://incendios-grafana:3000"
creds = base64.b64encode(b"admin:ValleSol2026!Secure").decode()

def grafana(path, method="GET", data=None):
    req = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {creds}"
        },
        method=method
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# Get dashboard
dash = grafana("/api/dashboards/uid/incendios-valle-main")
p5 = next(p for p in dash["dashboard"]["panels"] if p.get("id") == 5)

print(f"Panel 5 title: {p5.get('title')}")

# Find imagen override and show current links
for o in p5["fieldConfig"]["overrides"]:
    if o.get("matcher", {}).get("options") == "Imagen":
        for prop in o["properties"]:
            if prop["id"] == "links":
                print(f"  Current links: {json.dumps(prop['value'], ensure_ascii=False)}")

# Remove links from the override
for o in p5["fieldConfig"]["overrides"]:
    if o.get("matcher", {}).get("options") == "Imagen":
        o["properties"] = [p for p in o["properties"] if p["id"] != "links"]

# Update dashboard
payload = json.dumps({
    "dashboard": dash["dashboard"],
    "overwrite": True
}).encode()

result = grafana("/api/dashboards/db", method="POST", data=payload)
print(f"Updated dashboard: {result.get('status', 'unknown')}")
print(f"New URL: {result.get('url', '')}")
