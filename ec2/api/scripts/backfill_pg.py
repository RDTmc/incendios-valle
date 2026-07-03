"""
Backfill datos existentes de SQLite a PostgreSQL.
Ejecutar despues de validar que init_pg_schema() creo las tablas.
"""
import sqlite3, os, sys

sys.path.insert(0, '/app')

DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')

def backfill():
    from database_pg import get_pg_connection, is_pg_configured
    if not is_pg_configured():
        print("PG no configurado, abortando")
        return

    sq = sqlite3.connect(DB_PATH)
    sq.row_factory = sqlite3.Row
    cur = sq.cursor()

    with get_pg_connection() as pg:
        if pg is None:
            print("PG no disponible")
            sq.close()
            return
        pgc = pg.cursor()

        cur.execute("SELECT * FROM users")
        users = [dict(r) for r in cur.fetchall()]
        for u in users:
            pgc.execute("""
                INSERT INTO users (user_id, email, nombre, rol, password_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    email = EXCLUDED.email,
                    nombre = EXCLUDED.nombre,
                    rol = EXCLUDED.rol
            """, (u['user_id'], u.get('email'), u.get('nombre'),
                  u.get('rol', 'VECINO'), u.get('password_hash', ''),
                  u.get('created_at')))

        cur.execute("SELECT * FROM reports")
        reports = [dict(r) for r in cur.fetchall()]
        skipped = 0
        for r in reports:
            rid = r.get('report_id')
            if not rid:
                skipped += 1
                continue
            pgc.execute("""
                INSERT INTO reports (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, foto_url, estado, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (report_id) DO UPDATE SET
                    estado = EXCLUDED.estado,
                    updated_at = EXCLUDED.updated_at
            """, (rid, r.get('user_id', 'ANONIMO'), r.get('tipo', 'FORESTAL'),
                  r.get('latitud', '0'), r.get('longitud', '0'), r.get('geohash', ''),
                  r.get('descripcion', ''), r.get('foto_url', ''),
                  r.get('estado', 'PENDIENTE'), r.get('created_at'), r.get('updated_at')))

        pg.commit()

        pgc.execute("SELECT COUNT(*) FROM users")
        pg_users = pgc.fetchone()[0]
        pgc.execute("SELECT COUNT(*) FROM reports")
        pg_reports = pgc.fetchone()[0]

    sq.close()

    print(f"Backfill completado:")
    print(f"  Users:   {len(users)} sincronizados, {pg_users} en PG")
    print(f"  Reports: {len(reports)} sincronizados ({skipped} sin report_id), {pg_reports} en PG")

if __name__ == "__main__":
    backfill()
