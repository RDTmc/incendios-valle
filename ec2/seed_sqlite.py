import sqlite3, uuid
from datetime import datetime, timezone

c = sqlite3.connect("/app/data/incendios.db")

# Check current count
count = c.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
print(f"Reports before: {count} filas")

ts = datetime.now(timezone.utc).isoformat()
test_data = [
    ("RPT-TEST-001", "usr-admin-001", "FORESTAL", "-33.4489", "-70.6693", "Incendio forestal zona norte", "PENDIENTE", ts, ts),
    ("RPT-TEST-002", "usr-vecino-001", "URBANO",   "-33.4567", "-70.6789", "Casa en llamas sector sur",   "ACTIVO",    ts, ts),
    ("RPT-TEST-003", "usr-vecino-002", "FORESTAL", "-33.4400", "-70.6600", "Quema controlada",           "CONTROLADO", ts, ts),
]
for row in test_data:
    c.execute("""
        INSERT OR REPLACE INTO reports
        (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, estado, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (*row[:6], "", *row[6:]))
c.commit()
print("Insertados 3 registros de prueba")

count_after = c.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
print(f"Reports total: {count_after} filas")

for r in c.execute("SELECT report_id, tipo, estado FROM reports ORDER BY report_id").fetchall():
    rid = r[0] or "NULL"
    tip = r[1] or "NULL"
    est = r[2] or "NULL"
    print(f"  {rid:20s}  tipo={tip:10s}  estado={est}")
