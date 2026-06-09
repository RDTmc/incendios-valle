from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Annotated
from dependencies import get_report_repository, verify_token, verify_token_optional, sync_to_sqlite
from models import ReportRequest
from factories import ReportFactory
from datetime import datetime, timezone

router = APIRouter(tags=["reports"])


@router.post("/reports", responses={
    400: {"description": "device_id requerido para reportes anónimos"},
    500: {"description": "Create report error"},
})
def create_report(req: ReportRequest, payload: Annotated[Optional[dict], Depends(verify_token_optional)]):
    try:
        if not payload:
            if not req.device_id:
                raise HTTPException(status_code=400, detail="device_id requerido para reportes anónimos")
            user_id = "ANONIMO"
        else:
            user_id = req.user_id or payload.get('user_id', 'ANONIMO')

        typed_report = ReportFactory.create_report(req.tipo)
        typed_report.user_id = user_id
        typed_report.device_id = req.device_id or ''
        typed_report.latitud = req.latitud
        typed_report.longitud = req.longitud
        typed_report.descripcion = req.descripcion
        typed_report.foto_url = req.foto_url
        typed_report.estado = typed_report.get_default_estado()

        repo = get_report_repository()
        item = repo.create({
            **typed_report.to_item(),
            'user_id': user_id,
            'device_id': req.device_id or '',
        })

        report_id = item.get('reports_id', '')
        sync_to_sqlite('reports', 'INSERT', item)

        return {
            "report_id": report_id,
            "estado": item['estado'],
            "created_at": item['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[reports] Create error: {e}")
        raise HTTPException(status_code=500, detail="Create report error")


@router.post("/api/reportar", responses={
    400: {"description": "device_id requerido para reportes anónimos"},
    500: {"description": "Create report error"},
})
@router.post("/reportar", responses={
    400: {"description": "device_id requerido para reportes anónimos"},
    500: {"description": "Create report error"},
})
def reportar_anonimo(req: ReportRequest, payload: Annotated[Optional[dict], Depends(verify_token_optional)]):
    return create_report(req, payload)


@router.get("/reports", responses={
    500: {"description": "List reports error"},
})
def list_reports(payload: Annotated[dict, Depends(verify_token)], estado: Optional[str] = None, user_id: Optional[str] = None):
    try:
        repo = get_report_repository()
        if user_id:
            items = repo.find_by_user(user_id, estado)
        else:
            items = repo.find_all(estado)
        return items
    except Exception as e:
        print(f"[reports] List error: {e}")
        raise HTTPException(status_code=500, detail="List reports error")


@router.get("/reports/{report_id}", responses={
    404: {"description": "Report not found"},
    500: {"description": "Get report error"},
})
def get_report(report_id: str, payload: Annotated[dict, Depends(verify_token)]):
    try:
        repo = get_report_repository()
        item = repo.find_by_id(report_id)
        if not item:
            raise HTTPException(status_code=404, detail="Report not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        print(f"[reports] Get error: {e}")
        raise HTTPException(status_code=500, detail="Get report error")


@router.put("/reports/{report_id}", responses={
    500: {"description": "Update report error"},
})
def update_report(report_id: str, payload: Annotated[dict, Depends(verify_token)], estado: Optional[str] = None, descripcion: Optional[str] = None):
    try:
        repo = get_report_repository()
        item = repo.update(report_id, estado, descripcion)
        return item
    except Exception as e:
        print(f"[reports] Update error: {e}")
        raise HTTPException(status_code=500, detail="Update report error")
