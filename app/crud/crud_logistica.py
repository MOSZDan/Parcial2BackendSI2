from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Incidente, HistorialIncidente, Taller, taller_especialidad, Tecnico, OportunidadIncidente
from fastapi import HTTPException
from datetime import datetime
import uuid
import math

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371.0 # radio de la tierra en km
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = math.sin(dlat / 2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def buscar_taller_cercano(db: AsyncSession, incidente_id: uuid.UUID, especialidad_id: uuid.UUID):
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    if not incidente:
        return None

    # Filtrar talleres por la especialidad requerida
    stmt = select(Taller).join(taller_especialidad, Taller.id == taller_especialidad.c.taller_id)\
                         .filter(taller_especialidad.c.especialidad_id == especialidad_id)
    talleres_res = await db.execute(stmt)
    talleres = talleres_res.scalars().all()

    mejor_taller = None
    menor_distancia = float('inf')

    for t in talleres:
        if t.latitud and t.longitud:
            dist = calcular_distancia(float(incidente.latitud), float(incidente.longitud), float(t.latitud), float(t.longitud))
            if dist < menor_distancia:
                menor_distancia = dist
                mejor_taller = t

    return mejor_taller, menor_distancia

async def aceptar_alerta(db: AsyncSession, incidente_id: uuid.UUID, tecnico_id: uuid.UUID, taller_id: uuid.UUID, current_user_id: uuid.UUID):
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    if incidente.estado_actual != "Reportado":
        raise HTTPException(status_code=400, detail="Este incidente ya fue tomado o no está disponible.")

    # Buscar la oportunidad específica de este taller
    op_res = await db.execute(select(OportunidadIncidente).filter(
        OportunidadIncidente.incidente_id == incidente_id,
        OportunidadIncidente.taller_id == taller_id
    ))
    op = op_res.scalars().first()
    
    if not op:
        raise HTTPException(status_code=404, detail="No tienes una oportunidad válida para este incidente.")
        
    if op.estado != "Pendiente":
        raise HTTPException(status_code=400, detail="Ya te postulaste o la oportunidad expiró.")
        
    # El taller acepta, pero NO se asigna el incidente todavía. Pasa a Postulado.
    op.estado = "Postulado"
    op.tecnico_id = tecnico_id
    
    # Historial para saber que se postuló
    db_historial = HistorialIncidente(
        id=uuid.uuid4(),
        estado_anterior=incidente.estado_actual,
        estado_nuevo="Reportado (Postulado)",
        observaciones=f"El taller se postuló con un técnico. Esperando selección del conductor.",
        incidente_id=incidente_id,
        cambiado_por_usuario_id=current_user_id,
        tenant_id=incidente.tenant_id
    )
    db.add(db_historial)
    
    await db.commit()
    return True

async def actualizar_estado_rescate(db: AsyncSession, incidente_id: uuid.UUID, tecnico_id: uuid.UUID, nuevo_estado: str, usuario_id: uuid.UUID, costo_final: float | None = None):
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    
    if not incidente or incidente.tecnico_id != tecnico_id:
        raise HTTPException(status_code=403, detail="No autorizado para modificar este rescate. Asegurese de estar asignado.")

    estado_anterior = incidente.estado_actual
    incidente.estado_actual = nuevo_estado
    
    if nuevo_estado == "Finalizado":
        incidente.finalizado_en = datetime.utcnow()
        await db.execute(update(Tecnico).where(Tecnico.id == tecnico_id).values(estado_disponible=True))
        if costo_final is not None:
            op_res = await db.execute(select(OportunidadIncidente).filter(
                OportunidadIncidente.incidente_id == incidente_id,
                OportunidadIncidente.estado == 'Aceptada'
            ))
            op = op_res.scalars().first()
            if op:
                op.precio_estimado = costo_final

    incidente.updated_at = datetime.utcnow()

    db_historial = HistorialIncidente(
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        observaciones=f"Actualización operativa a: {nuevo_estado}",
        incidente_id=incidente.id,
        cambiado_por_usuario_id=usuario_id,
        tenant_id=incidente.tenant_id
    )
    db.add(db_historial)
    await db.commit()
    await db.refresh(incidente)
    return incidente

async def cancelar_solicitud(db: AsyncSession, incidente_id: uuid.UUID, conductor_id: uuid.UUID, motivo: str):
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    
    if not incidente or incidente.conductor_id != conductor_id:
        raise HTTPException(status_code=403, detail="No autorizado para cancelar este rescate")

    estado_anterior = incidente.estado_actual
    incidente.estado_actual = "Cancelado"
    incidente.updated_at = datetime.utcnow()
    incidente.finalizado_en = datetime.utcnow()

    if incidente.tecnico_id:
        await db.execute(update(Tecnico).where(Tecnico.id == incidente.tecnico_id).values(estado_disponible=True))

    db_historial = HistorialIncidente(
        estado_anterior=estado_anterior,
        estado_nuevo="Cancelado",
        observaciones=f"Motivo de cancelación: {motivo}",
        incidente_id=incidente.id,
        cambiado_por_usuario_id=None,
        tenant_id=incidente.tenant_id
    )
    db.add(db_historial)
    await db.commit()
    return incidente
