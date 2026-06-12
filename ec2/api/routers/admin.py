from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from dependencies import get_db_connection, require_admin, get_user_repository
from notification_service import notify_new_user
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
            conn.close()


@router.get("/users")
def admin_list_users(payload: dict = Depends(require_admin), search: Optional[str] = None):
    repo = get_user_repository()
    users = repo.find_all()
    safe = []
    for u in users:
        safe.append({
            "user_id": u.get("user_id"),
            "email": u.get("email"),
            "nombre": u.get("nombre", ""),
            "rol": u.get("rol", "VECINO"),
            "created_at": u.get("created_at", ""),
        })
    if search:
        search_lower = search.lower()
        safe = [u for u in safe if search_lower in u["email"].lower() or search_lower in u["nombre"].lower()]
    return {"users": safe, "total": len(safe)}


@router.post("/users")
def admin_create_user(req: AdminCreateUserRequest, payload: dict = Depends(require_admin)):
    repo = get_user_repository()
    existing = repo.find_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    user = repo.create(email=req.email, password=req.password, nombre=req.nombre, rol=req.rol)
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
    repo = get_user_repository()
    repo.update(user_id, email=req.email, nombre=req.nombre, rol=req.rol)
    log_audit("update_user", payload["user_id"], user_id, f"Actualizó usuario {user_id}")
    return {"status": "updated"}


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: str, payload: dict = Depends(require_admin)):
    repo = get_user_repository()
    repo.delete(user_id)
    log_audit("delete_user", payload["user_id"], user_id, f"Eliminó usuario {user_id}")
    return {"status": "deleted"}


@router.get("/audit-log")
def admin_audit_log(payload: dict = Depends(require_admin), limit: int = 100):
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
        cursor.execute("SELECT report_id FROM reports WHERE report_id = ?", (report_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Reporte no encontrado")
        cursor.execute("UPDATE reports SET estado = ? WHERE report_id = ?", (estado_upper, report_id))
        conn.commit()
        log_audit("update_report_status", payload["user_id"], report_id, f"Cambió estado a {estado_upper}")
        return {"status": "updated", "report_id": report_id, "estado": estado_upper}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[admin] update_report_status error: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar estado")
    finally:
        if conn is not None:
            conn.close()


@router.get("/notifications")
def admin_notifications(payload: dict = Depends(require_admin), limit: int = 100):
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
