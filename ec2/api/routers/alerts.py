from fastapi import APIRouter, HTTPException
from typing import Optional
from dependencies import get_db_connection

router = APIRouter(tags=["alerts"])


@router.get("/alerts")
def list_alerts(read: Optional[str] = None, limit: int = 50):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if read:
            cursor.execute("SELECT * FROM alerts WHERE read = ? ORDER BY created_at DESC LIMIT ?", (int(read), limit))
        else:
            cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{
            "id": r[0], "alert_type": r[1], "message": r[2],
            "report_id": r[3], "latitud": r[4], "longitud": r[5],
            "source": r[6], "read": bool(r[7]), "created_at": r[8],
        } for r in rows]
    except Exception as e:
        print(f"[alerts] Fetch error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching alerts")


@router.post("/alerts")
def create_alert(alert_type: str = "INFO", message: str = "", report_id: str = "", latitud: float = 0, longitud: float = 0):
    try:
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (alert_type, message, report_id, latitud, longitud, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (alert_type, message, report_id, latitud, longitud, "api"))
        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()
        return {"status": "created", "id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[alerts] Create error: {e}")
        raise HTTPException(status_code=500, detail="Error creating alert")


@router.put("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET read = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
        return {"status": "updated"}
    except Exception as e:
        print(f"[alerts] Update error: {e}")
        raise HTTPException(status_code=500, detail="Error updating alert")
