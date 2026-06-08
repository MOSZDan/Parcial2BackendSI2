import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models import Taller, Usuario

async def main():
    async with AsyncSessionLocal() as db:
        res_u = await db.execute(select(Usuario).filter(Usuario.correo == "superadmin@resqauto.com"))
        u = res_u.scalars().first()
        
        if not u:
            print("No existe superadmin@resqauto.com")
            return
            
        res_t = await db.execute(select(Taller))
        taller = res_t.scalars().first()
        
        if not taller:
            print("No hay talleres en DB")
            return
            
        print(f"Asignando Taller {taller.nombre_comercial} al usuario {u.correo}")
        
        # Sincronizamos tenant_id y asignamos el usuario al taller
        stmt1 = update(Usuario).where(Usuario.id == u.id).values(
            tenant_id=taller.tenant_id, 
            organizacion_id=taller.organizacion_id
        )
        stmt2 = update(Taller).where(Taller.id == taller.id).values(usuario_id=u.id)
        
        await db.execute(stmt1)
        await db.execute(stmt2)
        await db.commit()
        print("Hecho!")

if __name__ == "__main__":
    asyncio.run(main())
