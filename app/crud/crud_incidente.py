from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Incidente, HistorialIncidente, EvidenciaMultimedia, Vehiculo, Conductor
from app.schemas.incidente import IncidenteCreate
from datetime import datetime
import uuid

async def create_incidente_con_evidencias(db: AsyncSession, incidente: IncidenteCreate, conductor_id: uuid.UUID, tenant_id: uuid.UUID, urls_archivos: list[str], tipo_archivos: list[str]):
    # Verificar vehículo
    veh_res = await db.execute(select(Vehiculo).filter(Vehiculo.id == incidente.vehiculo_id))
    vehiculo = veh_res.scalars().first()
    if not vehiculo:
        return None
        
    cond_res = await db.execute(select(Conductor).filter(Conductor.id == conductor_id))
    conductor_obj = cond_res.scalars().first()
    
    # Generar codigo único
    codigo_generado = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    db_incidente = Incidente(
        id=uuid.uuid4(),
        codigo=codigo_generado,
        estado_actual="Reportado",
        tipo_problema=incidente.tipo_problema,
        descripcion=incidente.descripcion,
        prioridad=incidente.prioridad,
        latitud=incidente.latitud,
        longitud=incidente.longitud,
        direccion_referencia=incidente.direccion_referencia,
        conductor_id=conductor_id,
        vehiculo_id=incidente.vehiculo_id,
        organizacion_id=vehiculo.tenant_id,
        tenant_id=tenant_id,
        creado_offline=incidente.creado_offline
    )
    db.add(db_incidente)
    await db.flush()

    # Historial inicial
    db_historial = HistorialIncidente(
        id=uuid.uuid4(),
        estado_anterior=None,
        estado_nuevo="Reportado",
        observaciones="Incidente reportado por conductor",
        incidente_id=db_incidente.id,
        cambiado_por_usuario_id=conductor_obj.usuario_id if conductor_obj else conductor_id,
        tenant_id=tenant_id
    )
    db.add(db_historial)

    # Evidencias en S3
    for i, url in enumerate(urls_archivos):
        db_evidencia = EvidenciaMultimedia(
            tipo=tipo_archivos[i],
            url_archivo=url,
            descripcion="Evidencia cargada desde el celular",
            incidente_id=db_incidente.id,
            tenant_id=tenant_id
        )
        db.add(db_evidencia)

    await db.commit()
    await db.refresh(db_incidente)
    return db_incidente
