from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/bff", tags=["bff"])


def _get_db():
    from main import get_db_connection
    return get_db_connection()


def _get_report_repo():
    from main import get_report_repository
    return get_report_repository()


@router.get("/dashboard")
def bff_dashboard():
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
        weather = {
            "temperature": weather_row[0] if weather_row else None,
            "humidity": weather_row[1] if weather_row else None,
            "wind_speed": weather_row[2] if weather_row else None,
            "description": weather_row[3] if weather_row else None,
            "region": weather_row[4] if weather_row else None,
            "fetched_at": weather_row[5] if weather_row else None,
        } if weather_row else {}

        cursor.execute("SELECT COUNT(*) FROM firms_hotspots WHERE fetched_at = (SELECT MAX(fetched_at) FROM firms_hotspots)")
        hotspots_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM external_reports")
        ciren_total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reports WHERE estado IN ('ACTIVO', 'PENDIENTE')")
        active_reports = cursor.fetchone()[0]

        conn.close()

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
        raise HTTPException(status_code=500, detail=f"BFF dashboard error: {str(e)}")
