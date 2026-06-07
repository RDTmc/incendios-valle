from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str = ""
    rol: str = "VECINO"


class ReportRequest(BaseModel):
    user_id: Optional[str] = None
    tipo: str = "FORESTAL"
    latitud: float
    longitud: float
    descripcion: str = ""
    foto_url: str = ""
    device_id: Optional[str] = None


class SyncRequest(BaseModel):
    table: str
    operation: str
    data: dict


class ExternalReportRequest(BaseModel):
    source: str = "CIREN"
    nombre: Optional[str] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    provincia: Optional[str] = None
    superficie: Optional[float] = None
    causa: Optional[str] = None
    latitud: float
    longitud: float
    fh_inicio: Optional[str] = None
    fh_extinci: Optional[str] = None
    temporada: Optional[str] = None
