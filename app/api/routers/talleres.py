from fastapi import APIRouter, Depends, HTTPException, status
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.taller import EspecialidadResponse, TallerEspecialidadAdd, TecnicoCreate, TecnicoResponse, DisponibilidadUpdate, TecnicoUpdate
from app.schemas.incidente import BitacoraResponse
from app.crud import crud_taller
from app.api.deps import get_current_user
from app.models import Usuario

router = APIRouter(prefix="/talleres", tags=["Talleres y Personal"])

@router.get("/especialidades", response_model=list[EspecialidadResponse])
async def listar_especialidades(db: AsyncSession = Depends(get_db)):
    return await crud_taller.get_todas_especialidades(db)

@router.post("/especialidades")
async def asociar_especialidades(
    data: TallerEspecialidadAdd,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models import Taller
    from sqlalchemy import select
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    if not taller:
        raise HTTPException(status_code=403, detail="Solo el admin del taller puede configurar especialidades")

    await crud_taller.agregar_especialidades_taller(db, data.especialidad_ids, taller.id, current_user.tenant_id)
    return {"msg": "Especialidades asignadas correctamente al taller"}

@router.get("/tecnicos", response_model=list[TecnicoResponse])
async def listar_tecnicos(db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    from app.models import Taller, Tecnico
    from sqlalchemy import select
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    
    if not taller:
        raise HTTPException(status_code=403, detail="Debe ser administrador de taller")
        
    tecnicos_res = await db.execute(select(Tecnico).filter(Tecnico.taller_id == taller.id))
    tecnicos = tecnicos_res.scalars().all()
    return tecnicos

@router.post("/tecnicos", response_model=TecnicoResponse)
async def registrar_tecnico(
    tecnico: TecnicoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    nuevo_tecnico = await crud_taller.create_tecnico(db, tecnico, current_user.id)
    if not nuevo_tecnico:
        raise HTTPException(status_code=400, detail="Error al crear técnico. Valide sus permisos de administrador de taller.")
    return nuevo_tecnico

@router.patch("/tecnicos/disponibilidad", response_model=TecnicoResponse)
async def cambiar_disponibilidad(
    data: DisponibilidadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tecnico = await crud_taller.update_disponibilidad(db, current_user.id, data.estado_disponible)
    if not tecnico:
        raise HTTPException(status_code=403, detail="No posees un perfil técnico activo para cambiar de estado.")
    return tecnico

@router.put("/tecnicos/{tecnico_id}", response_model=TecnicoResponse)
async def editar_tecnico(
    tecnico_id: uuid.UUID,
    datos: TecnicoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models import Taller, Tecnico
    from sqlalchemy import select
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    if not taller:
        raise HTTPException(status_code=403, detail="Debe ser administrador de taller")
        
    tecnico_res = await db.execute(select(Tecnico).filter(Tecnico.id == tecnico_id, Tecnico.taller_id == taller.id))
    tecnico = tecnico_res.scalars().first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    update_data = datos.dict(exclude_unset=True)
    updated = await crud_taller.update_tecnico(db, tecnico_id, update_data)
    return updated

@router.delete("/tecnicos/{tecnico_id}")
async def eliminar_tecnico(
    tecnico_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.models import Taller, Tecnico
    from sqlalchemy import select
    t_res = await db.execute(select(Taller).filter(Taller.usuario_id == current_user.id))
    taller = t_res.scalars().first()
    if not taller:
        raise HTTPException(status_code=403, detail="Debe ser administrador de taller")
        
    tecnico_res = await db.execute(select(Tecnico).filter(Tecnico.id == tecnico_id, Tecnico.taller_id == taller.id))
    tecnico = tecnico_res.scalars().first()
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado")
        
    exito = await crud_taller.delete_tecnico(db, tecnico_id)
    if not exito:
        raise HTTPException(status_code=400, detail="No se puede eliminar el técnico. Tiene rescates activos o pendientes.")
    return {"msg": "Técnico eliminado exitosamente"}

@router.get("/bitacora", response_model=list[BitacoraResponse])
async def obtener_bitacora(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return await crud_taller.get_bitacora(db, current_user.tenant_id)
