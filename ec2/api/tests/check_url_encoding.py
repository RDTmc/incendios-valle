#!/usr/bin/env python3
"""Check foto_url in DB for double encoding."""
import sqlite3

conn = sqlite3.connect("/app/data/incendios.db")
cur = conn.execute(
    "SELECT report_id, descripcion, foto_url FROM reports WHERE descripcion LIKE ? ORDER BY created_at DESC LIMIT 1",
    ("%test imagen%",)
)
for row in cur.fetchall():
    print("ID:", row[0])
    print("Desc:", row[1])
    url = row[2]
    print("URL:", url[:250])
    if "%252" in url:
        print("DOUBLE ENCODING detected in DB (%%252B, %%253D)")
    elif "%25" in url:
        print("DOUBLE ENCODING (%%25 pattern) detected in DB")
    else:
        print("URL looks single-encoded (normal)")
    print("Has %2B:", "%2B" in url)
    print("Has %3D:", "%3D" in url)
conn.close()
