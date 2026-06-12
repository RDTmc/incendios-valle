import sqlite3
conn = sqlite3.connect("/app/data/incendios.db")
r = conn.execute("SELECT foto_url FROM reports WHERE foto_url != '' ORDER BY created_at DESC LIMIT 1").fetchone()
u = r[0]
print("Length:", len(u))
print("Double encode (%25):", "%25" in u)
print("URL[:120]:", u[:120])
print("URL[-60:]:", u[-60:])
