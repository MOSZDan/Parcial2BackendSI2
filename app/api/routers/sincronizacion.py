from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.api.deps import get_current_user
from app.models import Usuario, Conductor, Incidente
from app.schemas.incidente import IncidenteCreate
from app.crud.crud_incidente import create_incidente_con_evidencias
from sqlalchemy import select

router = APIRouter(prefix="/sincronizacion", tags=["sincronizacion"])

@router.post("/bulk", response_model=dict)
async def sincronizar_offline_bulk(
    incidentes_offline: List[IncidenteCreate],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Recibe una lista de incidentes que fueron creados en la aplicación móvil 
    mientras no había conexión a internet y los impacta en la base de datos de una sola vez.
    """
    conductor_res = await db.execute(select(Conductor).filter(Conductor.usuario_id == current_user.id))
    conductor = conductor_res.scalars().first()
    
    if not conductor:
        raise HTTPException(status_code=403, detail="Solo los conductores pueden sincronizar incidentes offline")

    exitosos = 0
    fallidos = 0
    ids_creados = []

    for incidente_data in incidentes_offline:
        # Forzar bandera offline para trazabilidad
        incidente_data.creado_offline = True
        
        try:
            nuevo_incidente = await create_incidente_con_evidencias(
                db=db,
                incidente=incidente_data,
                conductor_id=conductor.id,
                tenant_id=current_user.tenant_id,
                urls_archivos=[], # Se pueden subir luego o manejar una cola paralela de S3
                tipo_archivos=[]
            )
            
            if nuevo_incidente:
                exitosos += 1
                ids_creados.append(str(nuevo_incidente.id))
                # Las alertas logísticas pueden ser iniciadas por otro worker
                pass
            else:
                fallidos += 1
                
        except Exception as e:
            fallidos += 1
            # Logging del error para revisión, pero continuamos con el bulk
            print(f"Error sincronizando incidente offline: {str(e)}")

    return {
        "mensaje": "Sincronización completada",
        "resumen": {
            "exitosos": exitosos,
            "fallidos": fallidos,
            "incidentes_ids": ids_creados
        }
    }
