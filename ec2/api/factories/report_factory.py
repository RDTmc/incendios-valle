from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Report(ABC):
    def __init__(self, tipo: str):
        self.report_id = ''
        self.tipo = tipo
        self.user_id = 'ANONIMO'
        self.device_id = ''
        self.latitud = 0.0
        self.longitud = 0.0
        self.descripcion = ''
        self.foto_url = ''
        self.estado = 'PENDIENTE'
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at

    @abstractmethod
    def get_priority(self) -> int:
        pass

    @abstractmethod
    def get_default_estado(self) -> str:
        pass

    def to_item(self) -> dict:
        return {
            'tipo': self.tipo,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'descripcion': self.descripcion,
            'foto_url': self.foto_url,
            'estado': self.estado,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class ForestalReport(Report):
    def __init__(self):
        super().__init__('FORESTAL')

    def get_priority(self) -> int:
        return 1

    def get_default_estado(self) -> str:
        return 'PENDIENTE'


class UrbanoReport(Report):
    def __init__(self):
        super().__init__('URBANO')

    def get_priority(self) -> int:
        return 2

    def get_default_estado(self) -> str:
        return 'PENDIENTE'


class ReportFactory:
    @staticmethod
    def create_report(tipo: str) -> Report:
        if tipo == 'FORESTAL':
            return ForestalReport()
        elif tipo == 'URBANO':
            return UrbanoReport()
        else:
            raise ValueError(f"Tipo de reporte no soportado: {tipo}")
