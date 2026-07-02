"""
Reconciliación DynamoDB → SQLite (FASE 2 migración PostgreSQL).

Lee todos los registros de DynamoDB (users + reports) y los inserta en SQLite
si no existen. Previene datos huérfanos antes de migrar a PostgreSQL.

Uso:
    docker exec incendios-api python scripts/reconcile_dynamodb_to_sqlite.py

Salida:
    - N usuarios reconciliados / total DynamoDB
    - N reports reconciliados / total DynamoDB
    - Código 0 si todo OK, 1 si error
"""
import sys
import os

DB_PATH = os.environ.get('DB_PATH', '/data/incendios.db')


def get_db_connection():
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_dynamodb_resource():
    import boto3
    return boto3.resource('dynamodb')


def reconcile_users(cursor, table) -> int:
    existing = set()
    cursor.execute("SELECT user_id FROM users")
    for row in cursor.fetchall():
        existing.add(row[0])

    response = table.scan()
    items = response.get('Items', [])
    reconciled = 0

    for item in items:
        uid = item.get('user_id')
        if uid in existing:
            continue
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, email, nombre, rol, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            uid,
            item.get('email', ''),
            item.get('nombre', ''),
            item.get('rol', 'VECINO'),
            item.get('password_hash', ''),
            item.get('created_at', ''),
        ))
        reconciled += 1

    return reconciled, len(items)


def reconcile_reports(cursor, table) -> int:
    existing = set()
    cursor.execute("SELECT report_id FROM reports")
    for row in cursor.fetchall():
        existing.add(row[0])

    response = table.scan()
    items = response.get('Items', [])
    reconciled = 0

    for item in items:
        rid = item.get('reports_id') or item.get('report_id')
        if not rid or rid in existing:
            continue
        cursor.execute('''
            INSERT OR REPLACE INTO reports
            (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, foto_url, estado, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rid,
            item.get('user_id', 'ANONIMO'),
            item.get('tipo', 'FORESTAL'),
            item.get('latitud', '0'),
            item.get('longitud', '0'),
            item.get('geohash', ''),
            item.get('descripcion', ''),
            item.get('foto_url', ''),
            item.get('estado', 'PENDIENTE'),
            item.get('created_at', ''),
            item.get('updated_at', ''),
        ))
        reconciled += 1

    return reconciled, len(items)


def main():
    print("=" * 60)
    print("Reconciliación DynamoDB → SQLite")
    print("=" * 60)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print(f"\n✓ SQLite conectado: {DB_PATH}")
    except Exception as e:
        print(f"✗ Error conectando SQLite: {e}")
        return 1

    try:
        dynamodb = get_dynamodb_resource()
        users_table = dynamodb.Table('users')
        reports_table = dynamodb.Table('reports')
        print("✓ DynamoDB conectado")
    except Exception as e:
        print(f"✗ Error conectando DynamoDB: {e}")
        conn.close()
        return 1

    try:
        users_rec, users_total = reconcile_users(cursor, users_table)
        conn.commit()
        print(f"\nUsuarios: {users_rec} reconciliados de {users_total} en DynamoDB")

        reports_rec, reports_total = reconcile_reports(cursor, reports_table)
        conn.commit()
        print(f"Reports:  {reports_rec} reconciliados de {reports_total} en DynamoDB")

        cursor.execute("SELECT COUNT(*) FROM users")
        sqlite_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reports")
        sqlite_reports = cursor.fetchone()[0]

        print(f"\nTotal SQLite post-reconciliación:")
        print(f"  users:  {sqlite_users}")
        print(f"  reports: {sqlite_reports}")

        if sqlite_users >= users_total:
            print("\n✓ Users: SQLite ≥ DynamoDB — OK")
        else:
            print(f"\n⚠ Users: SQLite ({sqlite_users}) < DynamoDB ({users_total}) — revisar")

        if sqlite_reports >= reports_total:
            print("✓ Reports: SQLite ≥ DynamoDB — OK\n")
        else:
            print(f"⚠ Reports: SQLite ({sqlite_reports}) < DynamoDB ({reports_total}) — revisar\n")

        conn.close()
        return 0

    except Exception as e:
        print(f"\n✗ Error durante reconciliación: {e}")
        conn.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
