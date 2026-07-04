"""
Backfill datos existentes de SQLite a PostgreSQL.
Ejecutar despues de validar que init_pg_schema() creo las tablas.
"""
import sqlite3, os, sys

sys.path.insert(0, '/app')

DB_PATH = os.environ.get('DB_PATH', '/app/data/incendios.db')

TABLES = {
    'users': {
        'columns': ['user_id', 'email', 'nombre', 'rol', 'password_hash', 'created_at'],
        'conflict': 'user_id',
        'update': ['email', 'nombre', 'rol'],
    },
    'reports': {
        'columns': ['report_id', 'user_id', 'tipo', 'latitud', 'longitud', 'geohash', 'descripcion', 'foto_url', 'estado', 'created_at', 'updated_at'],
        'conflict': 'report_id',
        'update': ['estado', 'updated_at'],
    },
    'alerts': {
        'columns': ['alert_type', 'message', 'report_id', 'latitud', 'longitud', 'source', 'read', 'created_at'],
        'conflict': None,
    },
    'external_reports': {
        'columns': ['source', 'nombre', 'region', 'comuna', 'provincia', 'superficie', 'causa', 'latitud', 'longitud', 'fh_inicio', 'fh_extinci', 'temporada'],
        'conflict': None,
    },
    'firms_hotspots': {
        'columns': ['latitude', 'longitude', 'brightness', 'frp', 'confidence', 'satellite', 'acq_date', 'acq_time', 'daynight', 'source'],
        'conflict': None,
    },
    'weather_readings': {
        'columns': ['lat', 'lon', 'region', 'temperature', 'humidity', 'wind_speed', 'wind_direction', 'weather_desc', 'pressure'],
        'conflict': None,
    },
    'incident_resources': {
        'columns': ['report_id', 'tipo_recurso', 'cantidad', 'unidad', 'estado'],
        'conflict': None,
    },
    'notifications': {
        'columns': ['type', 'recipient_email', 'recipient_name', 'message', 'status', 'sns_message_id'],
        'conflict': None,
    },
    'audit_log': {
        'columns': ['action', 'admin_id', 'target_id', 'details', 'created_at'],
        'conflict': None,
    },
}

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

        for table_name, cfg in TABLES.items():
            cols = cfg['columns']
            placeholders = ', '.join(['%s'] * len(cols))
            col_names = ', '.join(cols)
            conflict = cfg.get('conflict')

            cur.execute(f"SELECT {col_names} FROM {table_name}")
            rows = [dict(r) for r in cur.fetchall()]

            synced = 0
            skipped = 0
            for row in rows:
                rid = row.get(conflict) if conflict else True
                if conflict and not rid:
                    skipped += 1
                    continue
                vals = tuple(row.get(c, '') for c in cols)
                if conflict and cfg.get('update'):
                    update_set = ', '.join(f"{c} = EXCLUDED.{c}" for c in cfg['update'])
                    sql = f"""
                        INSERT INTO {table_name} ({col_names})
                        VALUES ({placeholders})
                        ON CONFLICT ({conflict}) DO UPDATE SET {update_set}
                    """
                else:
                    sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                try:
                    pgc.execute(sql, vals)
                    synced += 1
                except Exception as e:
                    skipped += 1

            pg.commit()
            pgc.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = pgc.fetchone()[0]
            print(f"  {table_name:22s}: {synced:4d} sincronizados, {total:4d} en PG  ({skipped} saltados)")

    sq.close()
    print(f"\nBackfill completado.")

if __name__ == "__main__":
    backfill()
