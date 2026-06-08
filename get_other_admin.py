import asyncio
from app.database import AsyncSessionLocal
from app.models import Usuario, Taller
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Taller))
        talleres = res.scalars().all()
        
        for t in talleres:
            if t.usuario_id:
                res_u = await db.execute(select(Usuario).filter(Usuario.id == t.usuario_id))
                u = res_u.scalars().first()
                if u and u.correo != "superadmin@resq.com":
                    print(f"Otro Admin Encontrado:")
                    print(f"Taller: {t.nombre_comercial}")
                    print(f"Correo: {u.correo}")
                    print(f"ID: {u.id}")
                    break

if __name__ == "__main__":
    asyncio.run(main())
