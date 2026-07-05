from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from dependencies import require_admin, get_user_repository
from database_pg import query_pg_first, get_pg_connection
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
    try:
        with get_pg_connection() as conn:
            if conn is None:
                return
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_log (action, admin_id, target_id, details, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (action, admin_id, target_id, details, datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
    except Exception as e:
        print(f"[audit] Error logging: {e}")


@router.get("/users")
def admin_list_users(payload: dict = Depends(require_admin), search: Optional[str] = None):
    pg_rows = query_pg_first("SELECT user_id, email, nombre, rol, created_at FROM users ORDER BY created_at DESC")
    if pg_rows is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    safe = [{"user_id": r[0], "email": r[1], "nombre": r[2] or "", "rol": r[3], "created_at": r[4] or ""} for r in pg_rows]
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
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                updates = []
                params = []
                if req.email is not None:
                    updates.append("email = %s")
                    params.append(req.email)
                if req.nombre is not None:
                    updates.append("nombre = %s")
                    params.append(req.nombre)
                if req.rol is not None:
                    updates.append("rol = %s")
                    params.append(req.rol)
                if updates:
                    params.append(user_id)
                    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s", params)
                    conn.commit()
                log_audit("update_user", payload["user_id"], user_id, f"Actualizó usuario {user_id}")
                return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[admin] update_user error: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")


@router.delete("/users/{user_id}")
def admin_delete_user(user_id: str, payload: dict = Depends(require_admin)):
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Usuario no encontrado")
                cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                conn.commit()
                log_audit("delete_user", payload["user_id"], user_id, f"Eliminó usuario {user_id}")
                return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[admin] delete_user error: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")


@router.get("/audit-log")
def admin_audit_log(payload: dict = Depends(require_admin), limit: int = 100):
    pg_rows = query_pg_first("SELECT action, admin_id, target_id, details, created_at FROM audit_log ORDER BY created_at DESC LIMIT %s", (limit,))
    if pg_rows is None:
        return []
    return [{"action": r[0], "admin_id": r[1], "target_id": r[2], "details": r[3], "created_at": r[4]} for r in pg_rows]


@router.get("/reports")
def admin_list_reports(payload: dict = Depends(require_admin)):
    pg_rows = query_pg_first("SELECT report_id, user_id, tipo, latitud, longitud, descripcion, foto_url, estado, created_at FROM reports ORDER BY created_at DESC")
    if pg_rows is None:
        return {"reports": [], "total": 0}
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


@router.put("/reports/{report_id}/status")
def admin_update_report_status(report_id: str, req: UpdateReportStatusRequest, payload: dict = Depends(require_admin)):
    valid_statuses = {"PENDIENTE", "ACTIVO", "CONTROLADO", "EXTINGUIDO"}
    estado_upper = req.estado.upper()
    if estado_upper not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Válidos: {', '.join(valid_statuses)}")
    try:
        with get_pg_connection() as conn:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database unavailable")
            with conn.cursor() as cur:
                cur.execute("SELECT report_id, estado FROM reports WHERE report_id = %s", (report_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Reporte no encontrado")
                estado_anterior = row[1] or ""
                cur.execute("UPDATE reports SET estado = %s WHERE report_id = %s", (estado_upper, report_id))
                conn.commit()
                log_audit("update_report_status", payload["user_id"], report_id, f"Cambió estado a {estado_upper}")
                notify_status_change(report_id, estado_upper, payload["user_id"], estado_anterior)
                return {"status": "updated", "report_id": report_id, "estado": estado_upper}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[admin] update_report_status error: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar estado")


@router.get("/notifications")
def admin_notifications(payload: dict = Depends(require_admin), limit: int = 100):
    pg_rows = query_pg_first("SELECT id, type, recipient_email, recipient_name, status, sns_message_id, created_at FROM notifications ORDER BY created_at DESC LIMIT %s", (limit,))
    if pg_rows is None:
        return []
    return [{"id": r[0], "type": r[1], "recipient_email": r[2], "recipient_name": r[3], "status": r[4], "sns_message_id": r[5], "created_at": r[6]} for r in pg_rows]
