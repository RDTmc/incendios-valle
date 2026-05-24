import sqlite3

db_path = '/tmp/grafana.db'
c = sqlite3.connect(db_path)
uid = 'sqlite-incendios'
count_before = c.execute("SELECT COUNT(*) FROM data_source WHERE uid=?", (uid,)).fetchone()[0]
print(f"Datasources with uid='{uid}' before: {count_before}")
c.execute("DELETE FROM data_source WHERE uid=?", (uid,))
c.commit()
count_after = c.execute("SELECT COUNT(*) FROM data_source WHERE uid=?", (uid,)).fetchone()[0]
print(f"Datasources with uid='{uid}' after:  {count_after}")
print("Done")
