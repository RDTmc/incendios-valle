path = '/app/main.py'
with open(path) as f:
    c = f.read()

new = '''

@app.get("/public/map-coordinates")
def public_map_coordinates():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT latitud, longitud, tipo, estado FROM reports")
        rows = cursor.fetchall()
        conn.close()
        peso = {"ACTIVO": 3, "PENDIENTE": 2, "CONTROLADO": 1, "EXTINGUIDO": 0}
        return [{
            "lat": float(r[0]),
            "lng": float(r[1]),
            "tipo": r[2],
            "estado": r[3],
            "intensidad": peso.get(r[3], 1)
        } for r in rows if r[0] and r[1]]
    except Exception as e:
        return {"error": str(e)}'''

if '/public/map-coordinates' not in c:
    c = c.rstrip() + '\n' + new
    with open(path, 'w') as f:
        f.write(c)
    print('MAP ENDPOINT ADDED')
else:
    print('MAP ENDPOINT ALREADY EXISTS')
