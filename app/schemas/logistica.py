from pydantic import BaseModel
from uuid import UUID

class AsignarTallerRequest(BaseModel):
    incidente_id: UUID
    especialidad_id: UUID

class TallerCercanoResponse(BaseModel):
    taller_id: UUID
    nombre_comercial: str
    distancia_km: float

class AceptarAlertaRequest(BaseModel):
    incidente_id: UUID
    tecnico_id: UUID
    
class ActualizarEstadoRequest(BaseModel):
    incidente_id: UUID
    nuevo_estado: str # Ej: "Llegada", "Evaluando", "Finalizado"
    costo_final: float | None = None

class CancelarRequest(BaseModel):
    incidente_id: UUID
    motivo: str
