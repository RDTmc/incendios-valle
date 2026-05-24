import sqlite3
c = sqlite3.connect("/app/data/incendios.db")
count = c.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
print(f"Filas en SQLite: {count}")
for r in c.execute("SELECT report_id, tipo, estado FROM reports").fetchall():
    print(f"  {r[0]}  tipo={r[1]}  estado={r[2]}")
