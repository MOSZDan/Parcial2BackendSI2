from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud.crud_analitica import obtener_historial_vehiculo, obtener_dashboard_taller
from app.api.deps import get_current_user
from app.models import Usuario, Taller
from sqlalchemy import select
from uuid import UUID

router = APIRouter(prefix="/analitica", tags=["Reportes y Analítica"])

@router.get("/vehiculo/{vehiculo_id}/historial")
async def historial_clinico(
    vehiculo_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # CU-25
    return await obtener_historial_vehiculo(db, vehiculo_id)

@router.get("/taller/dashboard")
async def dashboard_metricas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # CU-26
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    if not taller:
        raise HTTPException(status_code=403, detail="No tienes acceso de administrador de taller.")
        
    return await obtener_dashboard_taller(db, taller.id)
