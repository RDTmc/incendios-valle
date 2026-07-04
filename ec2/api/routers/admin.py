from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from dependencies import get_db_connection, require_admin, get_user_repository
from database_pg import query_pg_first
from notification_service import notify_new_user, notify_status_change
from datetime import datetime, timezone
from models import UpdateReportStatusRequest

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminCreateUserRequest(BaseModel):
    email: str
    password: str
    nombre: str = ""
    rol: str = "VECINO"

class AdminUpdateUserRequest(BaseModel):
    email: Optional[str] = None
    nombre: Optional[str] = None
    rol: Optional[str] = None

class AuditEntry(BaseModel):
    action: str
    admin_id: str
    target_id: str
    details: str
    created_at: str


def log_audit(action: str, admin_id: str, target_id: str, details: str = ""):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (action, admin_id, target_id, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (action, admin_id, target_id, details, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
    except Exception as e:
        print(f"[audit] Error logging: {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/users")
def admin_list_users(payload: dict = Depends(require_admin), search: Optional[str] = None):
    pg_rows = query_pg_first("SELECT user_id, email, nombre, rol, created_at FROM users ORDER BY created_at DESC")
    if pg_rows is not None:
        safe = [{"user_id": r[0], "email": r[1], "nombre": r[2] or "", "rol": r[3], "created_at": r[4] or ""} for r in pg_rows]
        if search:
            search_lower = search.lower()
            safe = [u for u in safe if search_lower in u["email"].lower() or search_lower in u["nombre"].lower()]
        return {"users": safe, "total": len(safe)}
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, email, nombre, rol, created_at FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        safe = [{"user_id": r[0], "email": r[1], "nombre": r[2] or "", "rol": r[3], "created_at": r[4] or ""} for r in rows]
        if search:
            search_lower = search.lower()
            safe = [u for u in safe if search_lower in u["email"].lower() or search_lower in u["nombre"].lower()]
        return {"users": safe, "total": len(safe)}
    finally:
        conn.close()


@router.post("/users")
def admin_create_user(req: AdminCreateUserRequest, payload: dict = Depends(require_admin)):
    repo = get_user_repository()
    existing = repo.find_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    try:
        user = repo.create(email=req.email, password=req.password, nombre=req.nombre, rol=req.rol)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al crear usuario: No se pudo escribir en DynamoDB")
    log_audit("create_user", payload["user_id"], user["user_id"], f"Creó usuario {req.email} con rol {req.rol}")

    notify_new_user(
        email=user['email'],
        nombre=user['nombre'],
        rol=user['rol'],
    )

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "nombre": user["nombre"],
        "rol": user["rol"],
    }


@router.put("/users/{user_id}")
def admin_update_user(user_id: str, req: AdminUpdateUserRequest, payload: dict = Depends(require_admin)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        updates = []
        params = []
        if req.email is not None:
            updates.append("email = ?")
            params.append(req.email)
        if req.nombre is not None:
            updates.append("nombre = ?")
            params.append(req.nombre)
        if req.rol is not None:
            updates.append("rol = ?")
            params.append(req.rol)
        if updates:
            params.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", params)
            conn.commit()
        log_audit("update_user", payload["user_id"], user_id, f"Actualizó usuario {user_id}")
        return {"status": "updated"}
    finally:
        conn.close()


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: str, payload: dict = Depends(require_admin)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        log_audit("delete_user", payload["user_id"], user_id, f"Eliminó usuario {user_id}")
        return {"status": "deleted"}
    finally:
        conn.close()


@router.get("/audit-log")
def admin_audit_log(payload: dict = Depends(require_admin), limit: int = 100):
    pg_rows = query_pg_first("SELECT action, admin_id, target_id, details, created_at FROM audit_log ORDER BY created_at DESC LIMIT %s", (limit,))
    if pg_rows is not None:
        return [{"action": r[0], "admin_id": r[1], "target_id": r[2], "details": r[3], "created_at": r[4]} for r in pg_rows]
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT action, admin_id, target_id, details, created_at FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [{"action": r[0], "admin_id": r[1], "target_id": r[2], "details": r[3], "created_at": r[4]} for r in rows]
    except Exception as e:
        print(f"[admin] audit_log error: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


@router.get("/reports")
def admin_list_reports(payload: dict = Depends(require_admin)):
    pg_rows = query_pg_first("SELECT report_id, user_id, tipo, latitud, longitud, descripcion, foto_url, estado, created_at FROM reports ORDER BY created_at DESC")
    if pg_rows is not None:
        reports = []
        for r in pg_rows:
            rid = r[0]
            if not rid:
                continue
            reports.append({
                "report_id": rid,
                "user_id": r[1] or "",
                "tipo": r[2],
                "latitud": r[3],
                "longitud": r[4],
                "descripcion": r[5] or "",
                "foto_url": r[6] or "",
                "estado": r[7],
                "created_at": r[8],
            })
        return {"reports": reports, "total": len(reports)}
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT report_id, user_id, tipo, latitud, longitud, descripcion, foto_url, estado, created_at FROM reports ORDER BY created_at DESC")
        rows = cursor.fetchall()
        reports = []
        for r in rows:
            rid = r[0]
            if not rid:
                continue
            reports.append({
                "report_id": rid,
                "user_id": r[1] or "",
                "tipo": r[2],
                "latitud": r[3],
                "longitud": r[4],
                "descripcion": r[5] or "",
                "foto_url": r[6] or "",
                "estado": r[7],
                "created_at": r[8],
            })
        return {"reports": reports, "total": len(reports)}
    except Exception as e:
        print(f"[admin] list_reports error: {e}")
        return {"reports": [], "total": 0}
    finally:
        if conn is not None:
            conn.close()


@router.put("/reports/{report_id}/status")
def admin_update_report_status(report_id: str, req: UpdateReportStatusRequest, payload: dict = Depends(require_admin)):
    valid_statuses = {"PENDIENTE", "ACTIVO", "CONTROLADO", "EXTINGUIDO"}
    estado_upper = req.estado.upper()
    if estado_upper not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Válidos: {', '.join(valid_statuses)}")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT report_id, estado FROM reports WHERE report_id = ?", (report_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        estado_anterior = row[1] or ""
        cursor.execute("UPDATE reports SET estado = ? WHERE report_id = ?", (estado_upper, report_id))
        conn.commit()
        log_audit("update_report_status", payload["user_id"], report_id, f"Cambió estado a {estado_upper}")
        notify_status_change(report_id, estado_upper, payload["user_id"], estado_anterior)
        return {"status": "updated", "report_id": report_id, "estado": estado_upper}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[admin] update_report_status error: {e}\n{tb}")
        raise HTTPException(status_code=500, detail="Error al actualizar estado")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@router.get("/notifications")
def admin_notifications(payload: dict = Depends(require_admin), limit: int = 100):
    pg_rows = query_pg_first("SELECT id, type, recipient_email, recipient_name, status, sns_message_id, created_at FROM notifications ORDER BY created_at DESC LIMIT %s", (limit,))
    if pg_rows is not None:
        return [{"id": r[0], "type": r[1], "recipient_email": r[2], "recipient_name": r[3], "status": r[4], "sns_message_id": r[5], "created_at": r[6]} for r in pg_rows]
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, recipient_email, recipient_name, status, sns_message_id, created_at FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [{"id": r[0], "type": r[1], "recipient_email": r[2], "recipient_name": r[3], "status": r[4], "sns_message_id": r[5], "created_at": r[6]} for r in rows]
    except Exception as e:
        print(f"[admin] notifications error: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()
