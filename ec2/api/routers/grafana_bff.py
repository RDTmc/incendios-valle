from fastapi import APIRouter
from database_pg import query_pg_first

router = APIRouter(prefix="/bff/grafana", tags=["grafana-bff"])


@router.get("/report-stats")
def grafana_report_stats():
    by_estado = query_pg_first("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
    by_tipo = query_pg_first("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
    rows = []
    for estado, count in (by_estado or []):
        rows.append({"metric": f"estado_{estado}", "value": count})
    for tipo, count in (by_tipo or []):
        rows.append({"metric": f"tipo_{tipo}", "value": count})
    total = query_pg_first("SELECT COUNT(*) FROM reports", fetch='one')
    if total:
        rows.insert(0, {"metric": "total_reportes", "value": total[0]})
    return rows if rows else [{"metric": "no_data", "value": 0}]


@router.get("/report-geo")
def grafana_report_geo():
    rows = query_pg_first("""
        SELECT report_id, latitud, longitud, estado, tipo, descripcion, created_at
        FROM reports WHERE latitud IS NOT NULL AND longitud IS NOT NULL
          AND CAST(latitud AS REAL) != 0 AND CAST(longitud AS REAL) != 0
        ORDER BY created_at DESC
    """)
    result = []
    for r in rows or []:
        try:
            lat = float(r[1])
            lng = float(r[2])
        except (ValueError, TypeError):
            continue
        result.append({
            "report_id": r[0], "latitud": lat, "longitud": lng,
            "estado": r[3], "tipo": r[4],
            "descripcion": r[5] or "", "created_at": r[6] or "",
        })
    return result


@router.get("/weather-latest")
def grafana_weather_latest():
    rows = query_pg_first("""
        SELECT DISTINCT ON (region) region, temperature, humidity, wind_speed,
          wind_direction, weather_desc, pressure, fetched_at
        FROM weather_readings ORDER BY region, fetched_at DESC
    """)
    return [
        {
            "region": r[0], "temperature": r[1], "humidity": r[2],
            "wind_speed": r[3], "wind_direction": r[4],
            "weather_desc": r[5] or "", "pressure": r[6],
            "fetched_at": r[7] or "",
        }
        for r in rows or []
    ] or [{"region": "sin_datos", "temperature": 0}]


@router.get("/hotspots")
def grafana_hotspots():
    rows = query_pg_first("""
        SELECT latitude, longitude, brightness, frp, confidence,
               satellite, acq_date, acq_time, daynight
        FROM firms_hotspots
        WHERE acq_date >= (NOW() - INTERVAL '3 days')::date
        ORDER BY acq_date DESC, acq_time DESC
    """)
    return [
        {
            "latitude": r[0], "longitude": r[1], "brightness": r[2],
            "frp": r[3], "confidence": r[4], "satellite": r[5],
            "acq_date": r[6], "acq_time": r[7], "daynight": r[8],
        }
        for r in rows or []
    ]


@router.get("/resources")
def grafana_resources():
    rows = query_pg_first("""
        SELECT r.report_id, r.tipo_recurso, r.cantidad, r.unidad,
               r.estado, r.created_at, r.updated_at,
               COALESCE(rep.estado, '') as report_estado
        FROM incident_resources r
        LEFT JOIN reports rep ON r.report_id = rep.report_id
        ORDER BY r.created_at DESC
    """)
    return [
        {
            "report_id": r[0], "tipo_recurso": r[1], "cantidad": r[2],
            "unidad": r[3], "estado": r[4], "created_at": r[5],
            "updated_at": r[6], "report_estado": r[7],
        }
        for r in rows or []
    ]


@router.get("/external-reports")
def grafana_external_reports():
    rows = query_pg_first("""
        SELECT source, nombre, region, comuna, provincia, superficie,
               causa, latitud, longitud, fh_inicio, fh_extinci, temporada
        FROM external_reports ORDER BY fh_inicio DESC LIMIT 500
    """)
    return [
        {
            "source": r[0], "nombre": r[1], "region": r[2],
            "comuna": r[3], "provincia": r[4], "superficie": r[5],
            "causa": r[6], "latitud": r[7], "longitud": r[8],
            "fh_inicio": r[9], "fh_extincion": r[10], "temporada": r[11],
        }
        for r in rows or []
    ]


@router.get("/alerts-recent")
def grafana_alerts_recent():
    rows = query_pg_first("""
        SELECT alert_type, message, report_id, latitud, longitud,
               source, read, created_at
        FROM alerts ORDER BY created_at DESC LIMIT 20
    """)
    return [
        {
            "alert_type": r[0], "message": r[1], "report_id": r[2],
            "latitud": r[3], "longitud": r[4], "source": r[5],
            "read": bool(r[6]), "created_at": r[7],
        }
        for r in rows or []
    ]
