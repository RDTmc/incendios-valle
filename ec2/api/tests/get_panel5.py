import sqlite3, json

conn = sqlite3.connect('/tmp/grafana.db')
rows = conn.execute("SELECT uid, title, data FROM dashboard").fetchall()
print(f"Found {len(rows)} dashboards:")
for uid, title, data in rows:
    print(f"  UID: {uid}, Title: {title}")
print()

# Try all dashboards
for uid, title, data in rows:
    dash = json.loads(data)
    for p in dash.get('panels', []):
        if p.get('id') == 5 or p.get('title') == 'Reportes Ciudadanos':
            print(f'Dashboard: {title} ({uid})')
            print('=== fieldConfig ===')
            print(json.dumps(p.get('fieldConfig', {}), indent=2))
            print('=== options ===')
            print(json.dumps(p.get('options', {}), indent=2))
