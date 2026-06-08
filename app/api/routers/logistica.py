from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.logistica import AsignarTallerRequest, TallerCercanoResponse, AceptarAlertaRequest, ActualizarEstadoRequest, CancelarRequest
from app.crud import crud_logistica
from app.api.deps import get_current_user
from app.models import Usuario, Taller, Tecnico, Conductor, Incidente
from sqlalchemy import select
import asyncio
from uuid import UUID

router = APIRouter(prefix="/logistica", tags=["Logística y Asignación"])

async def timeout_reasignacion(incidente_id: UUID, db: AsyncSession):
    # Demora simulada de unos segundos (En prod: ~5 min)
    await asyncio.sleep(15)
    try:
        inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
        incidente = inc_res.scalars().first()
        if incidente and incidente.estado_actual == "Reportado":
            incidente.estado_actual = "Reasignando"
            await db.commit()
            print(f"\n[ALERTA ROJA] Incidente {incidente_id} ignorado por el taller. Reasignando automáticamente... (CU-17)\n")
    except Exception as e:
        print(f"Error en temporizador de demora: {e}")

@router.post("/asignar-taller", response_model=TallerCercanoResponse)
async def asignar_taller_cercano(
    data: AsignarTallerRequest,
    bg_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    resultado = await crud_logistica.buscar_taller_cercano(db, data.incidente_id, data.especialidad_id)
    if not resultado or not resultado[0]:
        raise HTTPException(status_code=404, detail="No se encontraron talleres cercanos con la especialidad requerida.")
    
    taller, distancia = resultado
    
    # Temporizador de reasignación (Background Task)
    bg_tasks.add_task(timeout_reasignacion, data.incidente_id, db)

    return {"taller_id": taller.id, "nombre_comercial": taller.nombre_comercial, "distancia_km": distancia}

@router.post("/alerta/aceptar")
async def aceptar_alerta(
    data: AceptarAlertaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    if not taller:
        raise HTTPException(status_code=403, detail="Usuario no autorizado o no cuenta con perfil de Administrador de Taller.")

    await crud_logistica.aceptar_alerta(db, data.incidente_id, data.tecnico_id, taller.id, current_user.id)
    return {"msg": "Alerta aceptada con éxito. Rescate asegurado."}

@router.patch("/estado")
async def actualizar_estado(
    data: ActualizarEstadoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tec_res = await db.execute(select(Tecnico).filter(Tecnico.usuario_id == current_user.id))
    tecnico = tec_res.scalars().first()
    if not tecnico:
        raise HTTPException(status_code=403, detail="Perfil técnico requerido.")
    
    await crud_logistica.actualizar_estado_rescate(db, data.incidente_id, tecnico.id, data.nuevo_estado, current_user.id, data.costo_final)
    return {"msg": f"El estado del incidente cambió exitosamente a '{data.nuevo_estado}'"}

@router.post("/cancelar")
async def cancelar_solicitud(
    data: CancelarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    con_res = await db.execute(select(Conductor).filter(Conductor.usuario_id == current_user.id))
    conductor = con_res.scalars().first()
    if not conductor:
        raise HTTPException(status_code=403, detail="Solo el conductor original puede cancelar la solicitud.")
        
    await crud_logistica.cancelar_solicitud(db, data.incidente_id, conductor.id, data.motivo)
    return {"msg": "Rescate cancelado y técnico liberado."}
