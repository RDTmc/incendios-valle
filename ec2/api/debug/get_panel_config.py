#!/usr/bin/env python3
"""Get Grafana panel 5 config and check data link settings."""
import json, sys, urllib.request, base64

creds = base64.b64encode(b"admin:ValleSol2026!Secure").decode()
req = urllib.request.Request(
    "http://incendios-grafana:3000/api/dashboards/uid/incendios-valle-main",
    headers={"Authorization": f"Basic {creds}"}
)
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())

p5 = next(p for p in d["dashboard"]["panels"] if p.get("id") == 5)
for o in p5.get("fieldConfig", {}).get("overrides", []):
    matcher = o.get("matcher", {}).get("options", "")
    props = o.get("properties", [])
    print(f"Override for: {matcher}")
    for prop in props:
        val = json.dumps(prop["value"], ensure_ascii=False)
        print(f"  {prop['id']}: {val[:250]}")

print("\n--- Options ---")
print(json.dumps(p5.get("options", {}), ensure_ascii=False, indent=2)[:1000])

print("\n--- Targets ---")
for t in p5.get("targets", []):
    print(f"  {t.get('refId')}: {t.get('rawQueryText', '')[:200]}")
