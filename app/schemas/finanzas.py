from pydantic import BaseModel
from uuid import UUID

class PagoRequest(BaseModel):
    incidente_id: UUID
    monto_total: float
    metodo_pago: str # Ej: "QR", "Tarjeta", "Efectivo"
    token_pago: str = "tok_test_dummy"

class ComprobanteResponse(BaseModel):
    numero_recibo: str
    url_pdf: str
    monto_taller: float
    comision_plataforma: float
