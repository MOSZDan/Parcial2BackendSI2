from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.finanzas import PagoRequest, ComprobanteResponse
from app.crud.crud_finanzas import procesar_pago_y_comision
from app.api.deps import get_current_user
from app.models import Usuario

router = APIRouter(prefix="/finanzas", tags=["Pagos y Comisiones"])

@router.post("/pagar", response_model=ComprobanteResponse)
async def realizar_pago_servicio(
    data: PagoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    resultado = await procesar_pago_y_comision(db, data.incidente_id, data.monto_total, data.metodo_pago, data.token_pago)
    if not resultado:
        raise HTTPException(status_code=400, detail="El incidente no está en un estado válido para pagar o no existe.")
        
    nro_recibo, url_pdf, monto_taller, monto_comision = resultado
    
    return {
        "numero_recibo": nro_recibo,
        "url_pdf": url_pdf,
        "monto_taller": float(monto_taller),
        "comision_plataforma": float(monto_comision)
    }
