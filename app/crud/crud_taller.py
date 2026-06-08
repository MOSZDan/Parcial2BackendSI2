from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Especialidad, taller_especialidad, Tecnico, Usuario, Bitacora, Rol, Taller
from app.schemas.taller import TecnicoCreate
from app.core.security import get_password_hash
from datetime import datetime
import uuid

async def get_todas_especialidades(db: AsyncSession):
    result = await db.execute(select(Especialidad))
    return result.scalars().all()

async def agregar_especialidades_taller(db: AsyncSession, especialidad_ids: list[uuid.UUID], taller_id: uuid.UUID, tenant_id: uuid.UUID):
    for esp_id in especialidad_ids:
        # Check si ya existe para no duplicar
        stmt = select(taller_especialidad).where(
            taller_especialidad.c.taller_id == taller_id,
            taller_especialidad.c.especialidad_id == esp_id
        )
        existe = await db.execute(stmt)
        if not existe.first():
            insert_stmt = taller_especialidad.insert().values(
                taller_id=taller_id,
                especialidad_id=esp_id,
                tenant_id=tenant_id
            )
            await db.execute(insert_stmt)
    await db.commit()
    return True

async def create_tecnico(db: AsyncSession, tecnico: TecnicoCreate, admin_id: uuid.UUID):
    # Buscar el taller del admin
    taller_result = await db.execute(select(Taller).filter(Taller.usuario_id == admin_id))
    taller = taller_result.scalars().first()
    if not taller:
        return None

    # Rol Tecnico
    rol_res = await db.execute(select(Rol).filter(Rol.nombre == "Tecnico"))
    rol = rol_res.scalars().first()
    if not rol:
        rol = Rol(nombre="Tecnico")
        db.add(rol)
        await db.flush()
    
    # Crear usuario
    db_user = Usuario(
        correo=tecnico.correo,
        contrasena=get_password_hash("temporal123"), # Contraseña temporal por defecto
        rol_id=rol.id,
        organizacion_id=taller.organizacion_id,
        tenant_id=taller.tenant_id
    )
    db.add(db_user)
    await db.flush()
    
    db_tecnico = Tecnico(
        nombre_completo=tecnico.nombre_completo,
        telefono=tecnico.telefono,
        estado_disponible=True,
        usuario_id=db_user.id,
        taller_id=taller.id,
        tenant_id=taller.tenant_id
    )
    db.add(db_tecnico)
    await db.commit()
    await db.refresh(db_tecnico)
    return db_tecnico

async def update_disponibilidad(db: AsyncSession, usuario_id: uuid.UUID, estado: bool):
    stmt = update(Tecnico).where(Tecnico.usuario_id == usuario_id).values(
        estado_disponible=estado,
        updated_at=datetime.utcnow()
    ).returning(Tecnico)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()

async def get_bitacora(db: AsyncSession, tenant_id: uuid.UUID):
    result = await db.execute(select(Bitacora).filter(Bitacora.tenant_id == tenant_id).order_by(Bitacora.fecha.desc()))
    return result.scalars().all()

async def update_tecnico(db: AsyncSession, tecnico_id: uuid.UUID, datos_update: dict):
    if not datos_update:
        return None
    datos_update["updated_at"] = datetime.utcnow()
    stmt = update(Tecnico).where(Tecnico.id == tecnico_id).values(**datos_update).returning(Tecnico)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()

async def delete_tecnico(db: AsyncSession, tecnico_id: uuid.UUID):
    # Validar si el técnico tiene incidentes activos o asignados
    from app.models import Incidente
    incidentes_res = await db.execute(
        select(Incidente).filter(
            Incidente.tecnico_id == tecnico_id,
            Incidente.estado_actual.in_(["Asignado", "En Progreso", "Pendiente"])
        )
    )
    if incidentes_res.scalars().first():
        return False # No se puede borrar, está ocupado
    
    # Borrado lógico o desactivación
    # En este caso, simplemente ponemos estado_disponible en False y desvinculamos o eliminamos
    # Por seguridad, lo desactivamos y lo quitamos del taller, o lo borramos físicamente
    # Borrado físico:
    from sqlalchemy import delete
    # Opcionalmente borrar también el usuario asociado para no dejar huérfanos
    t_res = await db.execute(select(Tecnico).filter(Tecnico.id == tecnico_id))
    tecnico = t_res.scalars().first()
    if tecnico:
        user_id = tecnico.usuario_id
        await db.execute(delete(Tecnico).where(Tecnico.id == tecnico_id))
        await db.execute(delete(Usuario).where(Usuario.id == user_id))
        await db.commit()
        return True
    return False
