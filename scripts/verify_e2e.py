import urllib.request, json

BASE = "https://api.keogh.lat"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def req(url, data=None, token=None, method=None):
    h = {"User-Agent": UA}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if data:
        h["Content-Type"] = "application/json"
        d = json.dumps(data).encode()
    else:
        d = None
    r = urllib.request.Request(url, data=d, headers=h, method=method)
    return json.loads(urllib.request.urlopen(r, timeout=15).read())

print("=== VERIFICACION END-TO-END ===\n")

# 1. Login
auth = req(f"{BASE}/api/login", {"email":"test@example.com","password":"Test123!"})
token = auth["token"]
print(f"[1/6] Login: OK (token: {token[:20]}...)")

# 2. List reports
reports = req(f"{BASE}/api/reports", token=token)
print(f"[2/6] Reports: {len(reports)} reportes")

# 3. Create report
created = req(f"{BASE}/api/reports", {"tipo":"FORESTAL","latitud":-33.456,"longitud":-70.678,"descripcion":"Test E2E"}, token=token)
rid = created.get("report_id", created.get("reports_id", ""))
print(f"[3/6] Create report: OK (id: {rid[:8]}...)")

# 4. Dashboard stats
stats = req(f"{BASE}/api/dashboard/stats", token=token)
print(f"[4/6] Dashboard stats: {list(stats.keys())[:5]}")

# 5. Focos activos (public)
focos = req(f"{BASE}/api/focos-activos")
print(f"[5/6] Focos activos: {len(focos)} focos")

# 6. Health
health = req(f"{BASE}/api/health")
print(f"[6/6] Health: {health['status']}")

# Bonus: Alertas
alerts = req(f"{BASE}/api/alerts?read=0&limit=5")
print(f"[BONUS] Alerts: {len(alerts)} alerts")

print("\n=== VERIFICACION COMPLETADA ===")
