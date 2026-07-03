"""
Investiga usuarios en DynamoDB que no están en SQLite.
Genera reporte para toma de decisión (FASE 2 migración PostgreSQL).
"""
import boto3
import sqlite3
import json

DB_PATH = "/app/data/incendios.db"

def main():
    dynamo = boto3.resource("dynamodb")
    users_table = dynamo.Table("users")
    resp = users_table.scan()
    ddb_users = {item["user_id"]: item for item in resp.get("Items", [])}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, email, nombre, rol, created_at, password_hash FROM users")
    sqlite_users = {row[0]: row for row in cur.fetchall()}
    conn.close()

    missing = []
    for uid, item in ddb_users.items():
        if uid not in sqlite_users:
            missing.append(item)

    orphans = []
    for sid, row in sqlite_users.items():
        if sid not in ddb_users:
            orphans.append(row)

    print("=" * 70)
    print("REPORTE: Discrepancia usuarios DynamoDB vs SQLite")
    print("=" * 70)
    print(f"\nTotal DynamoDB: {len(ddb_users)}")
    print(f"Total SQLite:   {len(sqlite_users)}")
    print(f"Diferencia:     {len(ddb_users) - len(sqlite_users)}")

    print(f"\n{'─' * 70}")
    print(f"USUARIOS EN DynamoDB PERO NO EN SQLITE ({len(missing)}):")
    print(f"{'─' * 70}")
    for u in missing:
        print(f"  user_id:     {u.get('user_id')}")
        print(f"  email:       {u.get('email')}")
        print(f"  nombre:      {u.get('nombre')}")
        print(f"  rol:         {u.get('rol')}")
        print(f"  created_at:  {u.get('created_at')}")
        print(f"  password:    {'<HASHEADA>' if u.get('password_hash') else 'VACÍA'}")
        print()

    print(f"{'─' * 70}")
    print(f"USUARIOS EN SQLITE PERO NO EN DynamoDB ({len(orphans)}):")
    print(f"{'─' * 70}")
    for o in orphans:
        print(f"  user_id:     {o[0]}")
        print(f"  email:       {o[1]}")
        print(f"  nombre:      {o[2]}")
        print(f"  rol:         {o[3]}")
        print(f"  created_at:  {o[4]}")
        print(f"  password:    {'<HASHEADA>' if o[5] else 'VACÍA'}")
        print()

    print(f"{'─' * 70}")
    print("POSIBLES CAUSAS:")
    print(f"{'─' * 70}")
    if missing:
        print("• Usuarios creados vía Lambda ms-usuarios (login auto-register)")
        print("  → Lambda usa handle_auth() unificado que crea user en DynamoDB")
        print("  → El endpoint /sync (POST) es el encargado de replicar a SQLite")
        print("  → Si /sync no se llamó, esos usuarios nunca llegaron a SQLite\n")
    if orphans:
        print("• Usuarios creados vía API/EC2 directamente (bootstrap, admin)")
        print("  → La API escribe primero en SQLite, luego replica a DynamoDB")
        print("  → Si la replica falló, quedan huérfanos en SQLite\n")

    print(f"{'─' * 70}")
    print("RECOMENDACIÓN:")
    print(f"{'─' * 70}")
    if missing:
        print(f"Insertar manualmente los {len(missing)} usuarios faltantes en SQLite")
        print("  INSERT OR IGNORE INTO users (user_id, email, nombre, rol, password_hash, created_at)")
        print("  VALUES ('<id>', '<email>', '<nombre>', '<rol>', '<hash>', '<created>');\n")
    if orphans:
        print(f"Insertar los {len(orphans)} huérfanos en DynamoDB (vía script)")
        print("  o ignorar si son registros de prueba.\n")
    print("Opción más simple para migración: reconciliar con INSERT OR REPLACE")
    print("  desde DynamoDB → SQLite ignorando la diferencia de 4 usuarios")
    print("  si esos 4 son cuentas Lambda auto-creadas sin reports asociados.\n")


if __name__ == "__main__":
    main()
