from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class IncidenteCreate(BaseModel):
    vehiculo_id: UUID
    tipo_problema: str
    descripcion: Optional[str] = None
    latitud: float
    longitud: float
    direccion_referencia: Optional[str] = None
    prioridad: str = "Media"
    creado_offline: bool = False

class IncidenteResponse(BaseModel):
    id: UUID
    codigo: str
    estado_actual: str
    tipo_problema: str
    prioridad: str
    latitud: float
    longitud: float
    created_at: datetime
    creado_offline: bool
    tecnico_id: Optional[UUID] = None
    taller_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class BitacoraResponse(BaseModel):
    id: UUID
    accion: str
    tabla_afectada: Optional[str] = None
    fecha: datetime
    usuario_id: UUID

    class Config:
        from_attributes = True
