from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import DiagnosticoIA, Incidente
from datetime import datetime
import uuid

async def guardar_diagnostico_ia(db: AsyncSession, incidente_id: uuid.UUID, diagnostico_json: dict, tenant_id: uuid.UUID):
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    if not incidente:
        return None
        
    db_ia = DiagnosticoIA(
        id=uuid.uuid4(),
        proveedor=diagnostico_json.get("proveedor", "Groq LLaMA3"),
        resultado_analisis=diagnostico_json.get("resultado_analisis", "No se pudo extraer"),
        probabilidad_falla=diagnostico_json.get("probabilidad_falla", 0.0),
        recomendacion=diagnostico_json.get("recomendacion", ""),
        analizado_en=datetime.utcnow(),
        incidente_id=incidente.id,
        tenant_id=tenant_id
    )
    db.add(db_ia)
    await db.commit()
    await db.refresh(db_ia)
    return db_ia
