from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.ia import AnalisisIARequest, AnalisisIAResponse
from app.core.ia_service import analizar_incidente_ia
from app.crud.crud_ia import guardar_diagnostico_ia
from app.api.deps import get_current_user
from app.models import Usuario

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])

async def procesar_ia_background(data: AnalisisIARequest, tenant_id):
    from app.database import AsyncSessionLocal
    try:
        diagnostico_json = await analizar_incidente_ia(texto_audio=data.texto_audio, url_imagen=data.url_imagen)
        async with AsyncSessionLocal() as new_db:
            await guardar_diagnostico_ia(new_db, data.incidente_id, diagnostico_json, tenant_id)
            await new_db.commit()
        print(f"\n[INFO IA] Diagnóstico completado para {data.incidente_id}!\n")
    except Exception as e:
        print(f"[ERROR IA] Fallo en el análisis: {e}")

@router.post("/analizar", response_model=AnalisisIAResponse)
async def iniciar_analisis(
    data: AnalisisIARequest,
    bg_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Se añade como tarea en segundo plano para no bloquear al usuario (CU-20)
    bg_tasks.add_task(procesar_ia_background, data, db, current_user.tenant_id)
    return {"msg": "El motor de IA está procesando las evidencias en segundo plano", "diagnostico": {}}
