import boto3, sqlite3, json, os

DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')
ADMIN_ID = '81d02e8d-375c-40b9-9f1e-968be9a2c5ae'

print("Obteniendo admin desde DynamoDB...")
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('users')
resp = table.get_item(Key={'user_id': ADMIN_ID})
user = resp.get('Item')
if not user:
    print("ERROR: admin no encontrado en DynamoDB")
    exit(1)

print(f"Email: {user.get('email')}")
print(f"Nombre: {user.get('nombre')}")
print(f"Rol: {user.get('rol')}")
print(f"Password hash: {user.get('password_hash', '')[:20]}...")

print(f"\nInsertando en SQLite...")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
try:
    cur.execute('''
        INSERT OR IGNORE INTO users (user_id, email, nombre, rol, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        ADMIN_ID,
        user.get('email'),
        user.get('nombre'),
        user.get('rol', 'VECINO'),
        user.get('password_hash', ''),
        user.get('created_at'),
    ))
    conn.commit()
    if cur.rowcount > 0:
        print(f"OK: admin insertado en SQLite")
    else:
        print("INFO: admin ya existía en SQLite (IGNORE)")
except Exception as e:
    print(f"ERROR: {e}")
    conn.rollback()
finally:
    conn.close()

print(f"\nVerificando...")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT user_id, email, rol FROM users WHERE email = 'admin@valledelsol.cl'")
for row in cur.fetchall():
    print(f"  SQLite - user_id: {row[0]}, email: {row[1]}, rol: {row[2]}")
conn.close()

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM users")
total = cur.fetchone()[0]
conn.close()
print(f"\nTotal usuarios en SQLite: {total}")
