import sqlite3
c = sqlite3.connect("/app/data/incendios.db")
cols = c.execute("PRAGMA table_info(reports)").fetchall()
for col in cols:
    print(f"{col[1]} ({col[2]})")
