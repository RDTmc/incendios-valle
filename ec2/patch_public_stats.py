import re

path = '/app/main.py'
with open(path) as f:
    c = f.read()

# Find the health endpoint and add a public stats endpoint after it
old = '''@app.get("/health")
def health():
    return {"status": "ok"}'''

new = '''@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/public/dashboard-stats")
def public_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
        by_estado = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
        by_tipo = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {
            "focos_activos": by_estado.get("ACTIVO", 0) + by_estado.get("PENDIENTE", 0),
            "estado_pendiente": by_estado.get("PENDIENTE", 0),
            "estado_activo": by_estado.get("ACTIVO", 0),
            "estado_controlado": by_estado.get("CONTROLADO", 0),
            "estado_extinguido": by_estado.get("EXTINGUIDO", 0),
            "tipo_forestal": by_tipo.get("FORESTAL", 0),
            "tipo_urbano": by_tipo.get("URBANO", 0)
        }
    except Exception as e:
        return {"focos_activos": 0, "estado_pendiente": 0, "estado_activo": 0, "estado_controlado": 0, "estado_extinguido": 0, "tipo_forestal": 0, "tipo_urbano": 0, "error": str(e)}'''

if old in c:
    c = c.replace(old, new)
    with open(path, 'w') as f:
        f.write(c)
    print('PUBLIC ENDPOINT ADDED')
else:
    print('OLDPATTERN NOT FOUND')
