from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from dependencies import get_report_repository
from database_pg import query_pg_first

router = APIRouter(prefix="/public", tags=["public"])

_INTERNAL_ERROR = "Internal server error"


@router.get("/dashboard-stats")
def public_dashboard_stats():
    pg_rows = query_pg_first("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
    if pg_rows is None:
        return {"error": _INTERNAL_ERROR}
    by_estado = {r[0]: r[1] for r in pg_rows}
    pg_tipo = query_pg_first("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
    by_tipo = {r[0]: r[1] for r in pg_tipo} if pg_tipo else {}
    return {
        "focos_activos": by_estado.get("ACTIVO", 0) + by_estado.get("PENDIENTE", 0),
        "estado_pendiente": by_estado.get("PENDIENTE", 0),
        "estado_activo": by_estado.get("ACTIVO", 0),
        "estado_controlado": by_estado.get("CONTROLADO", 0),
        "estado_extinguido": by_estado.get("EXTINGUIDO", 0),
        "tipo_forestal": by_tipo.get("FORESTAL", 0),
        "tipo_urbano": by_tipo.get("URBANO", 0),
    }


@router.get("/map-coordinates")
def public_map_coordinates():
    pg_rows = query_pg_first("SELECT latitud, longitud, tipo, estado FROM reports")
    if pg_rows is None:
        return {"error": _INTERNAL_ERROR}
    peso = {"ACTIVO": 3, "PENDIENTE": 2, "CONTROLADO": 1, "EXTINGUIDO": 0}
    return [{
        "lat": float(r[0]) if r[0] else 0.0,
        "lng": float(r[1]) if r[1] else 0.0,
        "tipo": r[2],
        "estado": r[3],
        "intensidad": peso.get(r[3], 1),
    } for r in pg_rows if r[0] and r[1]]


@router.get("/external-reports")
def public_external_reports(source: Optional[str] = None):
    if source:
        pg_rows = query_pg_first("SELECT * FROM external_reports WHERE source = %s ORDER BY fh_inicio DESC LIMIT 100", (source,))
    else:
        pg_rows = query_pg_first("SELECT * FROM external_reports ORDER BY fh_inicio DESC LIMIT 100")
    if pg_rows is None:
        return []
    return [{
        "id": r[0], "source": r[1], "nombre": r[2], "region": r[3],
        "comuna": r[4], "provincia": r[5], "superficie": r[6],
        "causa": r[7], "latitud": r[8], "longitud": r[9],
        "fh_inicio": r[10], "fh_extinci": r[11], "temporada": r[12],
    } for r in pg_rows]


@router.get("/cluster-stats")
def public_cluster_stats():
    from datetime import datetime, timezone, timedelta
    corte = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    pg_rows = query_pg_first("SELECT report_id, latitud, longitud FROM reports WHERE created_at >= %s", (corte,))
    if pg_rows is None:
        return {"clusters": 0, "pares": [], "error": _INTERNAL_ERROR}
    return _build_clusters(pg_rows)


def _build_clusters(rows):
    clusters = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            try:
                lat_i, lng_i = float(rows[i][1]), float(rows[i][2])
                lat_j, lng_j = float(rows[j][1]), float(rows[j][2])
                if abs(lat_i - lat_j) < 0.0005 and abs(lng_i - lng_j) < 0.0005:
                    clusters.append([rows[i][0], rows[j][0]])
            except (ValueError, TypeError):
                continue
    return {"clusters": len(clusters), "pares": clusters}


@router.get("/stale-pendientes")
def public_stale_pendientes():
    pg_rows = query_pg_first("""
        SELECT report_id, created_at,
               ROUND(EXTRACT(EPOCH FROM NOW() - created_at::timestamp) / 60) AS minutos
        FROM reports
        WHERE estado = 'PENDIENTE'
          AND EXTRACT(EPOCH FROM NOW() - created_at::timestamp) / 60 > 30
        ORDER BY minutos DESC
    """)
    if pg_rows is None:
        return []
    return [{"report_id": r[0], "created_at": r[1], "minutos": int(r[2])} for r in pg_rows]


@router.get("/external-reports/sources")
def public_external_reports_sources():
    pg_rows = query_pg_first("SELECT source, COUNT(*) AS total FROM external_reports GROUP BY source ORDER BY total DESC")
    if pg_rows is None:
        return []
    return [{"source": r[0], "total": r[1]} for r in pg_rows]


@router.get("/weather/latest")
def public_weather_latest():
    pg_rows = query_pg_first("""
        SELECT DISTINCT ON (w1.region) w1.region, w1.temperature, w1.humidity, w1.wind_speed,
               w1.wind_direction, w1.weather_desc, w1.pressure, w1.fetched_at
        FROM weather_readings w1
        ORDER BY w1.region, w1.id DESC
    """)
    if pg_rows is None:
        return []
    columns = ["region", "temperature", "humidity", "wind_speed",
               "wind_direction", "weather_desc", "pressure", "fetched_at"]
    return [dict(zip(columns, r)) for r in pg_rows]


@router.get("/weather/history")
def public_weather_history(limit: int = 50):
    pg_rows = query_pg_first("""
        SELECT region, temperature, humidity, wind_speed,
               wind_direction, weather_desc, fetched_at
        FROM weather_readings
        ORDER BY fetched_at DESC
        LIMIT %s
    """, (limit,))
    if pg_rows is None:
        return []
    columns = ["region", "temperature", "humidity", "wind_speed",
               "wind_direction", "weather_desc", "fetched_at"]
    return [dict(zip(columns, r)) for r in pg_rows]


@router.get("/firms-hotspots")
def public_firms_hotspots():
    pg_rows = query_pg_first("SELECT * FROM firms_hotspots ORDER BY acq_date DESC, acq_time DESC LIMIT 200")
    if pg_rows is None:
        return []
    return [{
        "id": r[0], "latitude": r[1], "longitude": r[2],
        "brightness": r[3], "frp": r[4], "confidence": r[5],
        "satellite": r[6], "acq_date": r[7], "acq_time": r[8],
        "daynight": r[9], "source": r[10],
    } for r in pg_rows]


@router.get("/resources")
def public_resources():
    pg_rows = query_pg_first("""
        SELECT r.report_id, r.tipo, r.estado,
               ir.tipo_recurso, ir.cantidad, ir.unidad
        FROM reports r
        LEFT JOIN incident_resources ir ON r.report_id = ir.report_id
        ORDER BY ir.created_at DESC LIMIT 20
    """)
    if pg_rows is None:
        return []
    return [{
        "report_id": r[0], "tipo": r[1], "estado": r[2],
        "recurso": r[3], "cantidad": r[4], "unidad": r[5],
    } for r in pg_rows]
