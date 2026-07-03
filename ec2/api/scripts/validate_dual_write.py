import psycopg2, os

conn = psycopg2.connect(
    host=os.environ['PG_HOST'],
    user=os.environ['PG_USER'],
    password=os.environ['PG_PASSWORD'],
    dbname=os.environ['PG_DATABASE']
)
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [t[0] for t in cur.fetchall()]
print(f"Tablas en PG ({len(tables)}): {tables}")

cur.execute("SELECT user_id, email, nombre, rol FROM users WHERE user_id='test-dual-001'")
row = cur.fetchone()
if row:
    print(f"test-dual-001 ENCONTRADO: {row[0]} | {row[1]} | {row[2]} | {row[3]}")
else:
    print("test-dual-001: NO ENCONTRADO")

for table in ['users', 'reports']:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"Total {table} en PG: {cur.fetchone()[0]}")

conn.close()
print("\nVALIDACION DUAL-WRITE COMPLETA")
