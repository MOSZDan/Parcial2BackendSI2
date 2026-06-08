from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class VehiculoCreate(BaseModel):
    placa: str
    marca: str
    modelo: str
    ano: int
    color: Optional[str] = None

class VehiculoResponse(VehiculoCreate):
    id: UUID
    conductor_id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True
