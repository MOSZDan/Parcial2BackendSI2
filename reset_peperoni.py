import asyncio
from app.database import AsyncSessionLocal
from app.models import Usuario, Tecnico
from sqlalchemy import select, update
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    async with AsyncSessionLocal() as db:
        res_tec = await db.execute(select(Tecnico).filter(Tecnico.telefono == "78645721"))
        tec = res_tec.scalars().first()
        if tec:
            res_u = await db.execute(select(Usuario).filter(Usuario.id == tec.usuario_id))
            u = res_u.scalars().first()
            if u:
                u.contrasena = pwd_context.hash("123")
                await db.commit()
                print(f"Contraseña de {u.correo} ({tec.nombre_completo}) reseteada a '123'")
            else:
                print("Usuario de Peperoni no encontrado.")
        else:
            print("Técnico con teléfono 78645721 no encontrado.")

if __name__ == "__main__":
    asyncio.run(main())
