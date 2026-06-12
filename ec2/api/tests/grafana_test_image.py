import urllib.request, urllib.parse, json, sys

BASE = 'https://dashboard.keogh.lat'
TOKEN = 'glsa_xzECDdWZO6ixPttXFZI3oGVfXD0XPmJR_5019d7a0'

headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

# Get dashboard
req = urllib.request.Request(f'{BASE}/api/dashboards/uid/incendios-valle-main', headers=headers)
try:
    r = urllib.request.urlopen(req)
except Exception as e:
    print('GET dashboard failed:', e)
    # Try login instead
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    login_data = json.dumps({'user':'admin','password':'ValleSol2026!Secure'}).encode()
    login_req = urllib.request.Request(f'{BASE}/login', data=login_data,
        headers={'Content-Type':'application/json'},
        method='POST')
    try:
        resp = opener.open(login_req)
        print('Login success:', resp.status)
        r = opener.open(f'{BASE}/api/dashboards/uid/incendios-valle-main')
        dash = json.loads(r.read())
    except Exception as e2:
        print('Login failed:', e2)
        sys.exit(1)

dash = json.loads(r.read())
print('Got dashboard:', r.status)

panels = dash['dashboard']['panels']
p5 = next((p for p in panels if p.get('id') == 5), None)
if not p5:
    print('ERROR: Panel 5 not found')
    sys.exit(1)

print('Panel 5 title:', p5.get('title'))
print('Existing targets:', len(p5.get('targets', [])))

# Get datasource from existing target
ds = None
if p5.get('targets'):
    ds = p5['targets'][0].get('datasource', {})
    print('Datasource:', ds)

targets = p5.get('targets', [])
targets.append({
    'rawQueryText': "SELECT 'https://picsum.photos/200/300' AS \"Imagen\", 'TEST' AS \"Reporte\"",
    'refId': 'B',
    'datasource': ds or {'type':'grafana-sqlite-datasource','uid':'P5D3B89D65558F6B9'},
    'format': 'table'
})

payload = json.dumps({
    'dashboard': dash['dashboard'],
    'overwrite': True,
    'message': 'temporary test - external image'
}).encode()

print('Updating dashboard...')

# Use opener if we have one, else use token
if 'opener' in dir():
    r = opener.open(f'{BASE}/api/dashboards/db', payload)
else:
    req = urllib.request.Request(f'{BASE}/api/dashboards/db', data=payload,
        headers=headers, method='POST')
    r = urllib.request.urlopen(req)

resp = json.loads(r.read())
print('Update:', r.status)
if r.status == 200:
    print('SUCCESS! Panel 5 now has test query B with picsum image')
    print('Go refresh the dashboard to see if the test image renders')
else:
    print('Error:', resp)
