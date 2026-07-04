import json, copy
import os

INFINITY_DS = {"type": "yesoreyeram-infinity-datasource", "uid": "incendios-api"}

ENDPOINT_FOR = {
    1:  "report-stats",
    2:  "weather-latest",
    3:  "report-stats",
    4:  "report-geo",
    5:  "report-geo",
    6:  "reports-recent",
    7:  "report-stats",
    8:  "resources",
    9:  "hotspots",
    10: "external-reports",
    11: "report-resources-summary",
    12: "resources-status",
}

_dir = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(_dir, "..", "grafana-provisioning", "dashboards", "dashboard_incendios.json")
dst = os.path.join(_dir, "..", "grafana-provisioning", "dashboards", "dashboard_incendios_v2.json")

with open(src) as f:
    dash = json.load(f)

dash["id"] = 2
dash["uid"] = "incendios-valle-v2"
dash["title"] = "Dashboard Incendios - Infinity"

for panel in dash["panels"]:
    pid = panel["id"]
    ep = ENDPOINT_FOR.get(pid)
    if ep is None:
        continue
    panel["datasource"] = copy.deepcopy(INFINITY_DS)
    panel["targets"] = [{
        "refId": "A",
        "datasource": copy.deepcopy(INFINITY_DS),
        "queryType": "json",
        "source": "url",
        "url": "http://incendios-api:8000/bff/grafana/" + ep,
        "method": "GET",
        "parser": "backend",
    }]

with open(dst, "w") as f:
    json.dump(dash, f, indent=2)

print("Written " + dst)
