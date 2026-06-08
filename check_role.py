import asyncio
from app.database import AsyncSessionLocal
from app.models import Usuario, Rol
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Usuario).filter(Usuario.correo == "superadmin@resqauto.com"))
        u = res.scalars().first()
        if u:
            res_r = await db.execute(select(Rol).filter(Rol.id == u.rol_id))
            rol = res_r.scalars().first()
            print(f"Role de usuario: {rol.nombre if rol else 'None'} ({u.rol_id})")
        else:
            print("Usuario no encontrado")

if __name__ == "__main__":
    asyncio.run(main())
