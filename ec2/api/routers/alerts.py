from fastapi import APIRouter, HTTPException
from typing import Optional
from database_pg import query_pg_first, get_pg_connection

router = APIRouter(tags=["alerts"])


@router.get("/alerts")
def list_alerts(read: Optional[str] = None, limit: int = 50):
    if read:
        pg_rows = query_pg_first("SELECT * FROM alerts WHERE read = %s ORDER BY created_at DESC LIMIT %s", (int(read), limit))
    else:
        pg_rows = query_pg_first("SELECT * FROM alerts ORDER BY created_at DESC LIMIT %s", (limit,))
    if pg_rows is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return [{
        "id": r[0], "alert_type": r[1], "message": r[2],
        "report_id": r[3], "latitud": r[4], "longitud": r[5],
        "source": r[6], "read": bool(r[7]), "created_at": r[8],
    } for r in pg_rows]


@router.post("/alerts")
def create_alert(alert_type: str = "INFO", message: str = "", report_id: str = "", latitud: float = 0, longitud: float = 0):
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO alerts (alert_type, message, report_id, latitud, longitud, source)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (alert_type, message, report_id, latitud, longitud, "api"))
                row = cur.fetchone()
                conn.commit()
                return {"status": "created", "id": row[0] if row else None}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[alerts] Create error: {e}")
        raise HTTPException(status_code=500, detail="Error creating alert")


@router.put("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int):
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("UPDATE alerts SET read = 1 WHERE id = %s", (alert_id,))
                conn.commit()
                return {"status": "updated"}
    except Exception as e:
        print(f"[alerts] Update error: {e}")
        raise HTTPException(status_code=500, detail="Error updating alert")
