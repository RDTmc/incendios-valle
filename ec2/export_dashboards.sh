#!/bin/bash
# Exporta dashboards desde Grafana API → JSON files
# Uso: ./export_dashboards.sh
# Los JSON se guardan en /home/ec2-user/incendios-data/api/grafana-exports/
set -euo pipefail

echo "Exportando dashboards desde Grafana..."

GRAFANA_TOKEN=$(grep GRAFANA_TOKEN /home/ec2-user/.env 2>/dev/null | cut -d= -f2)
if [ -z "$GRAFANA_TOKEN" ]; then
    echo "ERROR: GRAFANA_TOKEN no encontrado en /home/ec2-user/.env"
    exit 1
fi

OUTPUT_DIR="/app/data/grafana-exports"

docker exec \
    -e GRAFANA_TOKEN="$GRAFANA_TOKEN" \
    -e OUTPUT_DIR="$OUTPUT_DIR" \
    incendios-api python3 <<'PYEOF'
import urllib.request, json, os

token = os.environ["GRAFANA_TOKEN"]
out_dir = os.environ["OUTPUT_DIR"]

os.makedirs(out_dir, exist_ok=True)

headers = {"Authorization": f"Bearer {token}"}

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
        json.dump(data["dashboard"], f, indent=2)
    print(f"  OK  {title}.json")

print(f"\nExportados {len(dashboards)} dashboards a {out_dir}")
PYEOF

HOST_DIR="/home/ec2-user/incendios-data/api/grafana-exports"
echo ""
echo "Los archivos estan en: $HOST_DIR"
echo "Para copiarlos local: scp -i key.pem ec2-user@HOST:$HOST_DIR/*.json ./"
