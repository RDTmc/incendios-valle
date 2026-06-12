#!/usr/bin/env python3
import urllib.request, json, base64, os

auth = "Basic " + base64.b64encode(b"admin:ValleSol2026!Secure").decode()
out_dir = "/app/data/grafana-exports"
os.makedirs(out_dir, exist_ok=True)

# List dashboards
req = urllib.request.Request(
    "http://incendios-grafana:3000/api/search?type=dash-db",
    headers={"Authorization": auth}
)
resp = urllib.request.urlopen(req, timeout=10)
dashboards = json.loads(resp.read())
print(f"Found {len(dashboards)} dashboards:")

for db in dashboards:
    uid = db["uid"]
    title = db.get("title", "unknown").replace(" ", "_").replace("/", "_")
    print(f"  Exporting: {db.get('title')} (uid={uid})")

    req2 = urllib.request.Request(
        f"http://incendios-grafana:3000/api/dashboards/uid/{uid}",
        headers={"Authorization": auth}
    )
    resp2 = urllib.request.urlopen(req2, timeout=10)
    data = json.loads(resp2.read())
    filepath = os.path.join(out_dir, f"{title}.json")
    with open(filepath, "w") as f:
        json.dump(data["dashboard"], f, indent=2, ensure_ascii=False)
    print(f"    -> Saved {title}.json")

print(f"\nDone. Files in {out_dir}")
