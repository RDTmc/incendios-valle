#!/usr/bin/env python3
import sqlite3, subprocess

r = subprocess.run([
    "docker", "exec", "-i", "incendios-api", "python3", "-c", """
import sqlite3, json
conn = sqlite3.connect('/app/data/reports.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
for t in tables:
    cols = conn.execute("PRAGMA table_info(%s)" % t[0]).fetchall()
    print('  %s cols:' % t[0], [c[1] for c in cols])
    cnt = conn.execute("SELECT COUNT(*) FROM %s" % t[0]).fetchone()[0]
    print('  %s rows:' % t[0], cnt)
    if cnt > 0:
        sample = conn.execute("SELECT * FROM %s LIMIT 3" % t[0]).fetchall()
        print('  Sample:', sample)
"""], capture_output=True, text=True)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:300])
