import json
d = json.load(open("ec2/grafana-provisioning/dashboards/dashboard_incendios_v2.json"))
for p in d["panels"]:
    ds = p["datasource"]["uid"]
    url = p["targets"][0]["url"]
    print(f'Panel {p["id"]}: ds={ds}, url={url}')
