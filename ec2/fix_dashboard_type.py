import json

path = '/home/ec2-user/grafana-provisioning/dashboards/dashboard_incendios.json'
with open(path) as f:
    content = f.read()

old = '"type": "sqlite3"'
new = '"type": "frser-sqlite-datasource"'
if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('DASHBOARD JSON: FIXED')
    count = content.count(new)
    print(f'Replaced {count} occurrences')
else:
    print('No sqlite3 type found - checking current...')
    import re
    for m in re.finditer(r'"type"\s*:\s*"[^"]+"', content):
        print(f'  Found: {m.group()}')
