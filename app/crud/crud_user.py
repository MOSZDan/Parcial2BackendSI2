from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Usuario, Rol, Organizacion, Conductor, Taller
from app.schemas.user import UsuarioCreate
from app.core.security import get_password_hash
import uuid

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(Usuario).filter(Usuario.correo == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UsuarioCreate):
    # Obtener el rol
    result_rol = await db.execute(select(Rol).filter(Rol.nombre == user.tipo_usuario))
    rol = result_rol.scalars().first()
    if not rol:
        # Fallback a un rol nuevo si no existe (solo para desarrollo local)
        rol = Rol(nombre=user.tipo_usuario)
        db.add(rol)
        await db.flush()

    tenant_id = uuid.uuid4()
    org = Organizacion(
        id=tenant_id,
        nombre_comercial=user.nombre_taller if user.tipo_usuario == "Administrador" else f"Org_{user.nombre_completo}",
        nit=user.nit_taller if user.tipo_usuario == "Administrador" else f"0-{tenant_id.hex[:8]}",
        email=user.correo
    )
    db.add(org)
    await db.flush()

    db_user = Usuario(
        correo=user.correo,
        contrasena=get_password_hash(user.contrasena),
        rol_id=rol.id,
        organizacion_id=org.id,
        tenant_id=tenant_id
    )
    db.add(db_user)
    await db.flush()

    if user.tipo_usuario == "Conductor":
        conductor = Conductor(
            nombre_completo=user.nombre_completo,
            telefono=user.telefono,
            licencia=user.licencia,
            usuario_id=db_user.id,
            tenant_id=tenant_id
        )
        db.add(conductor)
    elif user.tipo_usuario == "Administrador":
        taller = Taller(
            nombre_comercial=user.nombre_taller,
            nit=user.nit_taller,
            direccion=user.direccion_taller or "",
            telefono=user.telefono,
            email=user.correo,
            usuario_id=db_user.id,
            organizacion_id=org.id,
            tenant_id=tenant_id
        )
        db.add(taller)

    await db.commit()
    await db.refresh(db_user)
    return db_user
