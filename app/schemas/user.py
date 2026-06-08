from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None

class UsuarioLogin(BaseModel):
    correo: EmailStr
    contrasena: str

class UsuarioCreate(BaseModel):
    correo: EmailStr
    contrasena: str
    nombre_completo: str
    telefono: str
    tipo_usuario: str # "Conductor" o "Admin"
    # Campos opcionales
    licencia: Optional[str] = None
    nombre_taller: Optional[str] = None
    nit_taller: Optional[str] = None
    direccion_taller: Optional[str] = None

class UsuarioResponse(BaseModel):
    id: UUID
    correo: EmailStr
    estado: str
    rol_id: UUID
    organizacion_id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True

class PasswordRecovery(BaseModel):
    correo: EmailStr
