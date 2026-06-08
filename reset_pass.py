import asyncio
from app.database import AsyncSessionLocal
from app.models import Usuario
from sqlalchemy import select, update
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def main():
    correo_admin = "admin_b995dd16@taller.com"
    nueva_clave = "123"
    
    hashed = pwd_context.hash(nueva_clave)
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Usuario).filter(Usuario.correo == correo_admin))
        usuario = res.scalars().first()
        
        if usuario:
            usuario.contrasena = hashed
            await db.commit()
            print(f"Contraseña de {correo_admin} actualizada a '{nueva_clave}' con éxito.")
        else:
            print("No se encontró al usuario")

if __name__ == "__main__":
    asyncio.run(main())
