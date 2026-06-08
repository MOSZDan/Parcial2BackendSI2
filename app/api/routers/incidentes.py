import math
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.incidente import IncidenteCreate, IncidenteResponse
from app.crud.crud_incidente import create_incidente_con_evidencias
from app.api.deps import get_current_user
from app.models import Usuario, Conductor, Incidente, OportunidadIncidente, Taller
from sqlalchemy import select
from typing import List, Optional
from app.core.storage import upload_file_to_s3
from uuid import UUID
import datetime
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/incidentes", tags=["Incidentes y Emergencias"])

def calcular_distancia(lat1, lon1, lat2, lon2):
    # Fórmula de Haversine para distancia en KM
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999
    R = 6371.0
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("/", response_model=list[IncidenteResponse])
async def listar_incidentes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from sqlalchemy import or_
    from app.models import Taller
    
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    
    if taller:
        stmt = select(Incidente).outerjoin(
            OportunidadIncidente, 
            (OportunidadIncidente.incidente_id == Incidente.id) & (OportunidadIncidente.taller_id == taller.id)
        ).filter(
            or_(
                Incidente.taller_id == taller.id,
                (Incidente.estado_actual == 'Reportado') & (OportunidadIncidente.id != None)
            )
        ).distinct().order_by(Incidente.created_at.desc())
    else:
        # Fallback (ej. admin global)
        stmt = select(Incidente).order_by(Incidente.created_at.desc())
        
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/activo", response_model=Optional[IncidenteResponse])
async def get_incidente_activo(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Ver si es conductor
    res_cond = await db.execute(select(Conductor).filter(Conductor.usuario_id == current_user.id))
    conductor = res_cond.scalars().first()
    
    if conductor:
        res_inc = await db.execute(select(Incidente).filter(
            Incidente.conductor_id == conductor.id, 
            Incidente.estado_actual.notin_(['Finalizado', 'Cancelado'])
        ).order_by(Incidente.created_at.desc()))
        return res_inc.scalars().first()
        
    # Ver si es tecnico
    from app.models import Tecnico
    res_tec = await db.execute(select(Tecnico).filter(Tecnico.usuario_id == current_user.id))
    tecnico = res_tec.scalars().first()
    
    if tecnico:
        res_inc = await db.execute(select(Incidente).filter(
            Incidente.tecnico_id == tecnico.id,
            Incidente.estado_actual.notin_(['Finalizado', 'Cancelado'])
        ))
        return res_inc.scalars().first()
        
    raise HTTPException(status_code=403, detail="No es un conductor ni un técnico válido")

@router.post("/{incidente_id}/cancelar")
async def cancelar_incidente(
    incidente_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    res_inc = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = res_inc.scalars().first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    incidente.estado_actual = 'Cancelado'
    incidente.updated_at = datetime.datetime.utcnow()
    
    # También cancelar las oportunidades
    res_ops = await db.execute(select(OportunidadIncidente).filter(OportunidadIncidente.incidente_id == incidente_id))
    for op in res_ops.scalars().all():
        op.estado = 'Cancelada'
        
    await db.commit()
    return {"msg": "Rescate cancelado"}

@router.post("/", response_model=IncidenteResponse)
async def solicitar_auxilio(
    vehiculo_id: UUID = Form(...),
    tipo_problema: str = Form(...),
    descripcion: Optional[str] = Form(None),
    latitud: float = Form(...),
    longitud: float = Form(...),
    direccion_referencia: Optional[str] = Form(None),
    prioridad: str = Form("Media"),
    creado_offline: bool = Form(False),
    archivos: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        # Validar que es conductor
        res = await db.execute(select(Conductor).filter(Conductor.usuario_id == current_user.id))
        conductor = res.scalars().first()
        if not conductor:
            raise HTTPException(status_code=403, detail="Solo los conductores pueden crear incidentes de auxilio.")

        # [NUEVO] Validación Anti-Duplicados
        res_activo = await db.execute(select(Incidente).filter(
            Incidente.conductor_id == conductor.id, 
            Incidente.estado_actual.notin_(['Finalizado', 'Cancelado'])
        ))
        if res_activo.scalars().first():
            raise HTTPException(status_code=400, detail="Ya tienes un rescate en curso. Cancélalo antes de solicitar otro.")

        incidente_data = IncidenteCreate(
            vehiculo_id=vehiculo_id,
            tipo_problema=tipo_problema,
            descripcion=descripcion,
            latitud=latitud,
            longitud=longitud,
            direccion_referencia=direccion_referencia,
            prioridad=prioridad,
            creado_offline=creado_offline
        )

        urls = []
        tipos = []
        
        # Subida Asíncrona de archivos a S3
        for file in archivos:
            tipo = "Imagen" if "image" in file.content_type else "Audio"
            try:
                url = await upload_file_to_s3(file)
                urls.append(url)
                tipos.append(tipo)
            except Exception as e:
                print(f"Error subiendo a S3: {e}")
                url = f"https://storage.resqauto.com/mock/{file.filename}"
                urls.append(url)
                tipos.append(tipo)

        nuevo_incidente = await create_incidente_con_evidencias(
            db, incidente_data, conductor.id, current_user.tenant_id, urls, tipos
        )
        
        if not nuevo_incidente:
            raise HTTPException(status_code=400, detail="Error en el registro del incidente. Verifique los datos.")
            
        # [NUEVO FLUJO: BROADCAST OPORTUNIDADES POR RADIO GPS]
        todas_los_talleres = await db.execute(select(Taller).filter(Taller.activo == True))
        talleres = todas_los_talleres.scalars().all()
        
        for t in talleres:
            if t.latitud is None or t.longitud is None:
                distancia = 0.0 # Fallback temporal para que siempre reciban la oportunidad si no configuraron GPS
            else:
                distancia = calcular_distancia(latitud, longitud, t.latitud, t.longitud)
                
            if distancia <= 20.0:  # Radio de 20 KM
                import math
                eta_calc = math.ceil(distancia / 0.5) if distancia > 0 else 1
                precio_calc = 50.0 + (distancia * 5.0)
                
                op = OportunidadIncidente(
                    estado='Pendiente',
                    expira_en=datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
                    precio_estimado=precio_calc,
                    eta_minutos=eta_calc,
                    incidente_id=nuevo_incidente.id,
                    taller_id=t.id,
                    tenant_id=t.tenant_id  # Usa el tenant_id del Taller para que puedan verlo en la web
                )
                db.add(op)
                
        await db.commit()
        await db.refresh(nuevo_incidente)

        # IA EN SEGUNDO PLANO
        from app.api.routers.ia import procesar_ia_background
        from app.schemas.ia import AnalisisIARequest
        
        url_audio = next((u for u, t in zip(urls, tipos) if t == "Audio"), "")
        url_img = next((u for u, t in zip(urls, tipos) if t == "Imagen"), "")
        
        import asyncio
        req_ia = AnalisisIARequest(incidente_id=nuevo_incidente.id, texto_audio=url_audio, url_imagen=url_img)
        asyncio.create_task(procesar_ia_background(req_ia, current_user.tenant_id))
        
        return nuevo_incidente
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_str = traceback.format_exc()
        raise HTTPException(status_code=400, detail=f"EXCEPCION INTERNA: {err_str}")

@router.get("/{incidente_id}/postulaciones")
async def ver_postulaciones(
    incidente_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    res_cond = await db.execute(select(Conductor).filter(Conductor.usuario_id == current_user.id))
    conductor = res_cond.scalars().first()
    if not conductor:
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    stmt = select(OportunidadIncidente, Taller).join(Taller, OportunidadIncidente.taller_id == Taller.id).filter(
        OportunidadIncidente.incidente_id == incidente_id,
        OportunidadIncidente.estado == 'Postulado'
    )
    res = await db.execute(stmt)
    
    resultados = []
    for op, taller in res.all():
        resultados.append({
            "id": op.id,
            "taller_id": taller.id,
            "nombre_taller": taller.nombre_comercial,
            "tecnico_id": op.tecnico_id,
            "telefono": taller.telefono,
            "latitud": taller.latitud,
            "longitud": taller.longitud
        })
    return resultados

@router.post("/{incidente_id}/confirmar-taller")
async def confirmar_taller(
    incidente_id: UUID,
    taller_id: UUID = Form(...),
    tecnico_id: UUID = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    res_cond = await db.execute(select(Conductor).filter(Conductor.usuario_id == current_user.id))
    conductor = res_cond.scalars().first()
    if not conductor:
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    inc_res = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = inc_res.scalars().first()
    
    if not incidente or incidente.conductor_id != conductor.id:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    if incidente.estado_actual != "Reportado":
        raise HTTPException(status_code=400, detail="Este incidente ya fue procesado.")
        
    incidente.estado_actual = "En Camino"
    incidente.taller_id = taller_id
    incidente.tecnico_id = tecnico_id
    incidente.asignado_en = datetime.datetime.utcnow()
    
    ops_res = await db.execute(select(OportunidadIncidente).filter(OportunidadIncidente.incidente_id == incidente_id))
    for op in ops_res.scalars().all():
        op.estado = 'Aceptada' if op.taller_id == taller_id else 'Rechazada'
        
    import uuid
    from app.models import HistorialIncidente
    db_historial = HistorialIncidente(
        id=uuid.uuid4(),
        estado_anterior="Reportado",
        estado_nuevo="En Camino",
        observaciones="El conductor seleccionó un taller postulante.",
        incidente_id=incidente_id,
        cambiado_por_usuario_id=current_user.id,
        tenant_id=incidente.tenant_id
    )
    db.add(db_historial)
    
    await db.commit()
    return {"msg": "Taller confirmado con éxito. ¡Rescate en Camino!"}

@router.get("/{incidente_id}/detalles-servicio")
async def detalles_servicio(
    incidente_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models import Taller, Tecnico
    
    # Obtener el incidente
    res_inc = await db.execute(select(Incidente).filter(Incidente.id == incidente_id))
    incidente = res_inc.scalars().first()
    
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    res_op = await db.execute(select(OportunidadIncidente).filter(
        OportunidadIncidente.incidente_id == incidente_id,
        OportunidadIncidente.estado == 'Aceptada'
    ))
    op = res_op.scalars().first()
    
    precio = op.precio_estimado if op else 0
    eta = op.eta_minutos if op else 0
    
    res_taller = await db.execute(select(Taller).filter(Taller.id == incidente.taller_id))
    taller = res_taller.scalars().first()
    
    res_tecnico = await db.execute(select(Tecnico).filter(Tecnico.id == incidente.tecnico_id))
    tecnico = res_tecnico.scalars().first()
    
    if not taller or not tecnico:
        raise HTTPException(status_code=404, detail="Datos del servicio incompletos")
        
    return {
        "nombre_taller": taller.nombre_comercial,
        "latitud_taller": taller.latitud,
        "longitud_taller": taller.longitud,
        "telefono_taller": taller.telefono,
        "nombre_tecnico": tecnico.nombre_completo,
        "telefono_tecnico": tecnico.telefono,
        "precio_estimado": precio,
        "eta_minutos": eta
    }
