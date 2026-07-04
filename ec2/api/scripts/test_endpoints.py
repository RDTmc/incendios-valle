import httpx
r = httpx.get("http://localhost:8000/bff/dashboard")
d = r.json()
s = d.get("stats", {})
print(f"BFF OK: focos_activos={s.get('focos_activos')}, alerts={s.get('estado_pendiente')}")

r2 = httpx.get("http://localhost:8000/alerts")
print(f"Alerts: {len(r2.json())}")

r3 = httpx.get("http://localhost:8000/public/external-reports")
print(f"External: {len(r3.json())}")

r4 = httpx.get("http://localhost:8000/public/weather/latest")
print(f"Weather: {len(r4.json())}")

r5 = httpx.get("http://localhost:8000/public/firms-hotspots")
print(f"Firms: {len(r5.json())}")
