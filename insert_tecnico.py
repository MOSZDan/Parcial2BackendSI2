import asyncio
from app.database import async_session_maker
from app.models import Rol
from sqlalchemy import select
import uuid

async def main():
    async with async_session_maker() as session:
        # Verificar si existe el rol Tecnico
        stmt = select(Rol).filter(Rol.nombre == "Tecnico")
        result = await session.execute(stmt)
        rol = result.scalars().first()
        
        if not rol:
            nuevo_rol = Rol(
                id=uuid.uuid4(),
                nombre="Tecnico",
                descripcion="Técnico/Mecánico encargado de atender auxilios en terreno.",
                activo=True
            )
            session.add(nuevo_rol)
            await session.commit()
            print("Rol 'Tecnico' insertado correctamente.")
        else:
            print("El rol 'Tecnico' ya existe en la base de datos.")

if __name__ == "__main__":
    asyncio.run(main())
