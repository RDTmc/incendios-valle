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
    active = query_pg_first(
        "SELECT COUNT(*) FROM reports WHERE estado IN ('ACTIVO','PENDIENTE')", fetch='one'
    )
    if active:
        rows.insert(0, {"metric": "focos_activos", "value": active[0]})
    return rows if rows else [{"metric": "no_data", "value": 0}]


@router.get("/report-geo")
def grafana_report_geo():
    rows = query_pg_first("""
        SELECT report_id, CAST(latitud AS REAL), CAST(longitud AS REAL),
               estado, tipo, descripcion, created_at
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
        estado = r[3] or ""
        intensidad = 3 if estado == "ACTIVO" else 2 if estado == "PENDIENTE" else 1 if estado == "CONTROLADO" else 0
        result.append({
            "report_id": r[0], "lat": lat, "lng": lng,
            "estado": estado, "tipo": r[4] or "",
            "descripcion": r[5] or "", "created_at": r[6] or "",
            "intensidad": intensidad, "id_corto": str(r[0])[:8],
        })
    return result


@router.get("/weather-latest")
def grafana_weather_latest():
    rows = query_pg_first("""
        SELECT DISTINCT ON (region) region, temperature, humidity, wind_speed,
          wind_direction, weather_desc, pressure, fetched_at
        FROM weather_readings ORDER BY region, fetched_at DESC
    """)
    result = []
    for r in rows or []:
        temp = r[1] or 0
        hum = r[2] or 0
        wind = (r[3] or 0) * 3.6
        riesgo = 2 if (temp > 30 and hum < 30 and wind > 30) else 1 if (temp > 25 or hum < 40 or wind > 25) else 0
        result.append({
            "region": r[0], "temperature": temp, "humidity": hum,
            "wind_speed": wind, "wind_direction": r[4],
            "weather_desc": r[5] or "", "pressure": r[6],
            "fetched_at": r[7] or "", "riesgo": riesgo,
        })
    return result or [{"region": "sin_datos", "temperature": 0}]


@router.get("/hotspots")
def grafana_hotspots():
    rows = query_pg_first("""
        SELECT latitude, longitude, ROUND(frp::numeric, 1), confidence,
               satellite, acq_date, acq_time, daynight, source
        FROM firms_hotspots
        WHERE acq_date >= (NOW() - INTERVAL '3 days')::date
        ORDER BY acq_date DESC, acq_time DESC
    """)
    return [
        {
            "lat": r[0], "lng": r[1], "frp": r[2],
            "confidence": r[3], "satellite": r[4],
            "acq_date": r[5], "acq_time": r[6],
            "daynight": r[7], "source": r[8],
        }
        for r in rows or []
    ]


@router.get("/resources")
def grafana_resources():
    rows = query_pg_first("""
        SELECT r.report_id, r.tipo_recurso, r.cantidad, r.unidad,
               r.estado, r.created_at, r.updated_at,
               COALESCE(rep.estado, '') as report_estado,
               rep.tipo, COALESCE(rep.descripcion, '')
        FROM incident_resources r
        LEFT JOIN reports rep ON r.report_id = rep.report_id
        ORDER BY r.created_at DESC
    """)
    return [
        {
            "report_id": r[0], "tipo_recurso": r[1], "cantidad": r[2],
            "unidad": r[3], "estado": r[4], "created_at": r[5],
            "updated_at": r[6], "report_estado": r[7],
            "report_tipo": r[8], "report_descripcion": r[9],
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
            "causa": r[6], "lat": r[7], "lng": r[8],
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


@router.get("/reports-recent")
def grafana_reports_recent():
    rows = query_pg_first("""
        SELECT report_id, foto_url, descripcion, tipo, estado, created_at
        FROM reports ORDER BY created_at DESC LIMIT 10
    """)
    return [
        {
            "ID": str(r[0])[:8], "Imagen": r[1] or "",
            "Descripcion": r[2] or "", "Tipo": r[3] or "",
            "Estado": r[4] or "", "Fecha": r[5] or "",
        }
        for r in rows or []
    ]


@router.get("/report-resources-summary")
def grafana_report_resources_summary():
    rows = query_pg_first("""
        SELECT SUBSTR(r.report_id, 1, 8), r.estado, r.tipo,
               CASE WHEN COUNT(ir.id) = 0 THEN 'Pendiente' ELSE 'Asignado' END,
               COUNT(ir.id),
               COALESCE(STRING_AGG(DISTINCT ir.estado, ', '), '')
        FROM reports r
        LEFT JOIN incident_resources ir ON r.report_id = ir.report_id
        GROUP BY r.report_id, r.estado, r.tipo
        ORDER BY r.created_at DESC
    """)
    return [
        {
            "Reporte": r[0], "Incendio": r[1] or "",
            "Tipo": r[2] or "", "Evaluacion": r[3],
            "Recursos": r[4], "Estados": r[5],
        }
        for r in rows or []
    ]


@router.get("/resources-status")
def grafana_resources_status():
    rows = query_pg_first("""
        SELECT estado, COUNT(*)
        FROM incident_resources GROUP BY estado ORDER BY COUNT(*) DESC
    """)
    return [
        {"Estado": r[0] or "SIN ESTADO", "Cantidad": r[1]}
        for r in rows or []
    ]
