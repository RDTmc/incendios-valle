from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from dependencies import get_db_connection, get_report_repository

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/dashboard-stats")
def public_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT estado, COUNT(*) FROM reports GROUP BY estado")
        by_estado = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT tipo, COUNT(*) FROM reports GROUP BY tipo")
        by_tipo = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {
            "focos_activos": by_estado.get("ACTIVO", 0) + by_estado.get("PENDIENTE", 0),
            "estado_pendiente": by_estado.get("PENDIENTE", 0),
            "estado_activo": by_estado.get("ACTIVO", 0),
            "estado_controlado": by_estado.get("CONTROLADO", 0),
            "estado_extinguido": by_estado.get("EXTINGUIDO", 0),
            "tipo_forestal": by_tipo.get("FORESTAL", 0),
            "tipo_urbano": by_tipo.get("URBANO", 0)
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/map-coordinates")
def public_map_coordinates():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT latitud, longitud, tipo, estado FROM reports")
        rows = cursor.fetchall()
        conn.close()
        peso = {"ACTIVO": 3, "PENDIENTE": 2, "CONTROLADO": 1, "EXTINGUIDO": 0}
        return [{
            "lat": float(r[0]) if r[0] else 0.0,
            "lng": float(r[1]) if r[1] else 0.0,
            "tipo": r[2],
            "estado": r[3],
            "intensidad": peso.get(r[3], 1)
        } for r in rows if r[0] and r[1]]
    except Exception as e:
        return {"error": str(e)}


@router.get("/external-reports")
def public_external_reports(source: Optional[str] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if source:
            cursor.execute("SELECT * FROM external_reports WHERE source = ? ORDER BY fh_inicio DESC LIMIT 100", (source,))
        else:
            cursor.execute("SELECT * FROM external_reports ORDER BY fh_inicio DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": r[0], "source": r[1], "nombre": r[2], "region": r[3],
            "comuna": r[4], "provincia": r[5], "superficie": r[6],
            "causa": r[7], "latitud": r[8], "longitud": r[9],
            "fh_inicio": r[10], "fh_extinci": r[11], "temporada": r[12],
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/cluster-stats")
def public_cluster_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        from datetime import datetime, timezone, timedelta
        corte = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        cursor.execute(
            "SELECT report_id, latitud, longitud FROM reports WHERE created_at >= ?",
            (corte,)
        )
        rows = cursor.fetchall()
        conn.close()
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
    except Exception as e:
        return {"clusters": 0, "pares": [], "error": str(e)}


@router.get("/stale-pendientes")
def public_stale_pendientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT report_id, created_at,
                   ROUND((julianday('now') - julianday(created_at)) * 1440) AS minutos
            FROM reports
            WHERE estado = 'PENDIENTE'
              AND (julianday('now') - julianday(created_at)) * 1440 > 30
            ORDER BY minutos DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [{"report_id": r[0], "created_at": r[1], "minutos": int(r[2])} for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/external-reports/sources")
def public_external_reports_sources():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT source, COUNT(*) AS total FROM external_reports GROUP BY source ORDER BY total DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"source": r[0], "total": r[1]} for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/weather/latest")
def public_weather_latest():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w1.region, w1.temperature, w1.humidity, w1.wind_speed,
                   w1.wind_direction, w1.weather_desc, w1.pressure, w1.fetched_at
            FROM weather_readings w1
            WHERE w1.id IN (SELECT MAX(id) FROM weather_readings GROUP BY region)
            ORDER BY w1.region
        """)
        rows = cursor.fetchall()
        conn.close()
        columns = ["region", "temperature", "humidity", "wind_speed",
                   "wind_direction", "weather_desc", "pressure", "fetched_at"]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/weather/history")
def public_weather_history(limit: int = 50):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT region, temperature, humidity, wind_speed,
                   wind_direction, weather_desc, fetched_at
            FROM weather_readings
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        columns = ["region", "temperature", "humidity", "wind_speed",
                   "wind_direction", "weather_desc", "fetched_at"]
        return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/firms-hotspots")
def public_firms_hotspots():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM firms_hotspots ORDER BY acq_date DESC, acq_time DESC LIMIT 200")
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": r[0], "latitude": r[1], "longitude": r[2],
            "brightness": r[3], "frp": r[4], "confidence": r[5],
            "satellite": r[6], "acq_date": r[7], "acq_time": r[8],
            "daynight": r[9], "source": r[10],
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}


@router.get("/resources")
def public_resources():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.report_id, r.tipo, r.estado,
                   ir.tipo_recurso, ir.cantidad, ir.unidad
            FROM reports r
            LEFT JOIN incident_resources ir ON r.report_id = ir.report_id
            ORDER BY ir.created_at DESC LIMIT 20
        """)
        rows = cursor.fetchall()
        conn.close()
        return [{
            "report_id": r[0], "tipo": r[1], "estado": r[2],
            "recurso": r[3], "cantidad": r[4], "unidad": r[5]
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}
