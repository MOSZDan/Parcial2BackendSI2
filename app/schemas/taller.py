from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID

class EspecialidadResponse(BaseModel):
    id: UUID
    nombre_servicio: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

class TallerEspecialidadAdd(BaseModel):
    especialidad_ids: List[UUID]

class TecnicoCreate(BaseModel):
    nombre_completo: str
    correo: EmailStr
    contrasena: str
    telefono: Optional[str] = None
    estado_disponible: Optional[bool] = True

class TecnicoUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    estado_disponible: Optional[bool] = None

class TecnicoResponse(BaseModel):
    id: UUID
    nombre_completo: str
    telefono: str
    estado_disponible: bool
    usuario_id: UUID
    taller_id: UUID

    class Config:
        from_attributes = True

class DisponibilidadUpdate(BaseModel):
    estado_disponible: bool
