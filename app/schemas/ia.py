from pydantic import BaseModel
from uuid import UUID

class AnalisisIARequest(BaseModel):
    incidente_id: UUID
    texto_audio: str
    url_imagen: str

class AnalisisIAResponse(BaseModel):
    msg: str
    diagnostico: dict
