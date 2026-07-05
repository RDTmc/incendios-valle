#!/bin/bash
# Exporta dashboards desde Grafana API → JSON files
# Uso: ./export_dashboards.sh
# Los JSON se guardan en /home/ec2-user/incendios-data/api/grafana-exports/
set -euo pipefail

echo "Exportando dashboards desde Grafana (usando admin credentials)..."

OUTPUT_DIR="/app/data/grafana-exports"

docker exec incendios-api python3 <<'PYEOF'
import urllib.request, json, base64, os

import os
pwd = os.environ.get("GRAFANA_ADMIN_PASSWORD", "")
auth = "Basic " + base64.b64encode(f"admin:{pwd}".encode()).decode()
out_dir = "/app/data/grafana-exports"
os.makedirs(out_dir, exist_ok=True)

headers = {"Authorization": auth}

req = urllib.request.Request(
    "http://incendios-grafana:3000/api/search?type=dash-db",
    headers=headers,
)
resp = urllib.request.urlopen(req, timeout=10)
dashboards = json.loads(resp.read())

for db in dashboards:
    uid = db["uid"]
    title = db.get("title", "unknown").replace(" ", "_").replace("/", "_")
    req2 = urllib.request.Request(
        f"http://incendios-grafana:3000/api/dashboards/uid/{uid}",
        headers=headers,
    )
    resp2 = urllib.request.urlopen(req2, timeout=10)
    data = json.loads(resp2.read())
    filepath = os.path.join(out_dir, f"{title}.json")
    with open(filepath, "w") as f:
        json.dump(data["dashboard"], f, indent=2, ensure_ascii=False)
    print(f"  OK  {title}.json")

print(f"\nExportados {len(dashboards)} dashboards a {out_dir}")
PYEOF

HOST_DIR="/home/ec2-user/incendios-data/api/grafana-exports"
echo ""
echo "Los archivos estan en: $HOST_DIR"
echo ""
echo "Para copiarlos local:"
echo "  scp -i key.pem ec2-user@HOST:$HOST_DIR/Dashboard_Incendios_-_Valle_del_Sol.json ./"
echo ""
echo "Luego reemplazar el provisioning:"
echo "  cp Dashboard_Incendios_-_Valle_del_Sol.json ec2/grafana-provisioning/dashboards/dashboard_incendios_v2.json"
echo "  git commit -m 'sync: exportar dashboard desde Grafana'"
echo "  git push"
