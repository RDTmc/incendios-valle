import json
with open('/var/lib/grafana/plugins/frser-sqlite-datasource/plugin.json') as f:
    p = json.load(f)
print('id:', p.get('id'))
print('type:', p.get('type'))
