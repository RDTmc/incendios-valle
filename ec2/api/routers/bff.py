from fastapi import APIRouter, HTTPException
from typing import Optional
from database_pg import query_pg_first

router = APIRouter(prefix="/bff", tags=["bff"])


def _get_db():
    from main import get_db_connection
    return get_db_connection()


def _get_report_repo():
    from main import get_report_repository
    return get_report_repository()


@router.get("/dashboard", responses={
    500: {"description": "BFF dashboard error"},
})
def bff_dashboard():
    stats_pg = _try_pg_stats()
    if stats_pg is not None:
        return stats_pg
    return _sqlite_dashboard()


def _try_pg_stats():
    by_estado_rows = query_pg_first("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
    if by_estado_rows is None:
        return None
    by_estado = {r[0]: r[1] for r in by_estado_rows}
    by_tipo_rows = query_pg_first("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
    by_tipo = {r[0]: r[1] for r in by_tipo_rows} if by_tipo_rows else {}

    weather_row = query_pg_first("""
        SELECT temperature, humidity, wind_speed, weather_desc, region, fetched_at
        FROM weather_readings
        WHERE fetched_at = (SELECT MAX(fetched_at) FROM weather_readings)
    """, fetch='one')
    weather = {}
    if weather_row:
        weather = {
            "temperature": weather_row[0],
            "humidity": weather_row[1],
            "wind_speed": weather_row[2],
            "description": weather_row[3],
            "region": weather_row[4],
            "fetched_at": weather_row[5],
        }

    hc = query_pg_first("""
        SELECT COUNT(*) FROM firms_hotspots WHERE fetched_at = (SELECT MAX(fetched_at) FROM firms_hotspots)
    """, fetch='one')
    hotspots_count = hc[0] if hc else 0

    cc = query_pg_first("SELECT COUNT(*) FROM external_reports", fetch='one')
    ciren_total = cc[0] if cc else 0

    ac = query_pg_first("SELECT COUNT(*) FROM reports WHERE estado IN ('ACTIVO', 'PENDIENTE')", fetch='one')
    active_reports = ac[0] if ac else 0

    repo = _get_report_repo()
    all_items = repo.find_all()
    focos = []
    for item in all_items:
        try:
            lat = float(item.get('latitud', 0))
            lng = float(item.get('longitud', 0))
        except (ValueError, TypeError):
            continue
        if lat == 0 and lng == 0:
            continue
        focos.append({
            'id': item.get('report_id') or item.get('reports_id', ''),
            'lat': lat,
            'lng': lng,
            'estado': item.get('estado', ''),
            'tipo': item.get('tipo', ''),
        })

    return {
        "stats": {
            "focos_activos": by_estado.get("ACTIVO", 0) + by_estado.get("PENDIENTE", 0),
            "estado_pendiente": by_estado.get("PENDIENTE", 0),
            "estado_activo": by_estado.get("ACTIVO", 0),
            "estado_controlado": by_estado.get("CONTROLADO", 0),
            "estado_extinguido": by_estado.get("EXTINGUIDO", 0),
            "total_reportes": sum(by_estado.values()),
            "forestales": by_tipo.get("FORESTAL", 0),
            "urbanos": by_tipo.get("URBANO", 0),
            "active_reports": active_reports,
        },
        "weather": weather,
        "hotspots": {
            "total_firms": hotspots_count,
            "ciren_records": ciren_total,
        },
        "focos": focos,
    }


def _sqlite_dashboard():
    conn = None
    try:
        conn = _get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
        by_estado = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
        by_tipo = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT temperature, humidity, wind_speed, weather_desc, region, fetched_at
            FROM weather_readings
            WHERE fetched_at = (SELECT MAX(fetched_at) FROM weather_readings)
        """)
        weather_row = cursor.fetchone()
        weather = {}
        if weather_row:
            weather = {
                "temperature": weather_row[0],
                "humidity": weather_row[1],
                "wind_speed": weather_row[2],
                "description": weather_row[3],
                "region": weather_row[4],
                "fetched_at": weather_row[5],
            }

        cursor.execute("SELECT COUNT(*) FROM firms_hotspots WHERE fetched_at = (SELECT MAX(fetched_at) FROM firms_hotspots)")
        hotspots_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM external_reports")
        ciren_total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reports WHERE estado IN ('ACTIVO', 'PENDIENTE')")
        active_reports = cursor.fetchone()[0]

        repo = _get_report_repo()
        all_items = repo.find_all()
        focos = []
        for item in all_items:
            try:
                lat = float(item.get('latitud', 0))
                lng = float(item.get('longitud', 0))
            except (ValueError, TypeError):
                continue
            if lat == 0 and lng == 0:
                continue
            focos.append({
                'id': item.get('report_id') or item.get('reports_id', ''),
                'lat': lat,
                'lng': lng,
                'estado': item.get('estado', ''),
                'tipo': item.get('tipo', ''),
            })

        return {
            "stats": {
                "focos_activos": by_estado.get("ACTIVO", 0) + by_estado.get("PENDIENTE", 0),
                "estado_pendiente": by_estado.get("PENDIENTE", 0),
                "estado_activo": by_estado.get("ACTIVO", 0),
                "estado_controlado": by_estado.get("CONTROLADO", 0),
                "estado_extinguido": by_estado.get("EXTINGUIDO", 0),
                "total_reportes": sum(by_estado.values()),
                "forestales": by_tipo.get("FORESTAL", 0),
                "urbanos": by_tipo.get("URBANO", 0),
                "active_reports": active_reports,
            },
            "weather": weather,
            "hotspots": {
                "total_firms": hotspots_count,
                "ciren_records": ciren_total,
            },
            "focos": focos,
        }
    except Exception as e:
        print(f"[bff] Dashboard error: {e}")
        raise HTTPException(status_code=500, detail="BFF dashboard error")
    finally:
        if conn is not None:
            conn.close()
