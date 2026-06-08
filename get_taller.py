import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Taller, Usuario

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Taller))
        talleres = res.scalars().all()
        print("TALLERES:")
        for t in talleres:
            print(t.id, t.nombre_comercial, t.usuario_id)
            
        res_u = await db.execute(select(Usuario).filter(Usuario.correo == "superadmin@resqauto.com"))
        u = res_u.scalars().first()
        print("SUPERADMIN ID:", u.id if u else "NO FOUND")

if __name__ == "__main__":
    asyncio.run(main())
