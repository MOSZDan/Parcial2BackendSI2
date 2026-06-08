import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.security import get_password_hash
from app.models import Usuario, Rol, Taller, Organizacion, Conductor, Tecnico
import uuid
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        # 1. Crear Organización
        org = await db.execute(select(Organizacion).limit(1))
        org = org.scalars().first()
        if not org:
            org = Organizacion(nombre_comercial="Org Default", nit="123", email="a@a.com")
            db.add(org)
            await db.commit()
            await db.refresh(org)
            
        # 2. Crear Roles
        rol_cond = await db.execute(select(Rol).filter_by(nombre="Conductor"))
        rol_cond = rol_cond.scalars().first()
        if not rol_cond:
            rol_cond = Rol(nombre="Conductor", descripcion="C")
            db.add(rol_cond)
            
        rol_tecn = await db.execute(select(Rol).filter_by(nombre="Tecnico"))
        rol_tecn = rol_tecn.scalars().first()
        if not rol_tecn:
            rol_tecn = Rol(nombre="Tecnico", descripcion="T")
            db.add(rol_tecn)
            
        await db.commit()
        await db.refresh(rol_cond)
        await db.refresh(rol_tecn)

        # 3. Crear Usuarios
        pwd = get_password_hash('123')
        
        u_cond = await db.execute(select(Usuario).filter_by(correo="conductor@resq.com"))
        u_cond = u_cond.scalars().first()
        if not u_cond:
            u_cond = Usuario(correo="conductor@resq.com", contrasena=pwd, rol_id=rol_cond.id, organizacion_id=org.id, tenant_id=org.id)
            db.add(u_cond)
            
        u_tecn = await db.execute(select(Usuario).filter_by(correo="tecnico@resq.com"))
        u_tecn = u_tecn.scalars().first()
        if not u_tecn:
            u_tecn = Usuario(correo="tecnico@resq.com", contrasena=pwd, rol_id=rol_tecn.id, organizacion_id=org.id, tenant_id=org.id)
            db.add(u_tecn)
            
        await db.commit()
        await db.refresh(u_cond)
        await db.refresh(u_tecn)
        
        # 4. Crear Perfiles Específicos
        cond_prof = await db.execute(select(Conductor).filter_by(usuario_id=u_cond.id))
        cond_prof = cond_prof.scalars().first()
        if not cond_prof:
            cond_prof = Conductor(nombre_completo="Juan Conductor", telefono="123", usuario_id=u_cond.id, tenant_id=org.id)
            db.add(cond_prof)
            
        taller = await db.execute(select(Taller).limit(1))
        taller = taller.scalars().first()
        if not taller:
            taller = Taller(nombre_comercial="Taller Default", nit="123", direccion="Dir", telefono="123", usuario_id=u_cond.id, organizacion_id=org.id, tenant_id=org.id)
            db.add(taller)
            await db.commit()
            await db.refresh(taller)
            
        tecn_prof = await db.execute(select(Tecnico).filter_by(usuario_id=u_tecn.id))
        tecn_prof = tecn_prof.scalars().first()
        if not tecn_prof:
            tecn_prof = Tecnico(nombre_completo="Mecanico Experto", telefono="123", usuario_id=u_tecn.id, taller_id=taller.id, tenant_id=org.id)
            db.add(tecn_prof)
            
        await db.commit()
        print("Usuarios creados con éxito con ORM!")

asyncio.run(seed())
