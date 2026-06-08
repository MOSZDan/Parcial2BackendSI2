import asyncio
import httpx
from app.database import AsyncSessionLocal
from app.models import Usuario, Conductor
from app.core.security import create_access_token
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Conductor).filter(Conductor.id == "82586b35-324c-42e2-ae4f-4b5d0981bfa2"))
        conductor = res.scalars().first()
        res_u = await db.execute(select(Usuario).filter(Usuario.id == conductor.usuario_id))
        u = res_u.scalars().first()
        if not u:
            print("Conductor no encontrado")
            return
        token = create_access_token(u.id)

    async with httpx.AsyncClient() as client:
        # Mock payload para form-data
        data = {
            "vehiculo_id": "123e4567-e89b-12d3-a456-426614174000",
            "tipo_problema": "Problema Mecánico",
            "latitud": -17.78,
            "longitud": -63.18,
            "prioridad": "Media",
            "creado_offline": "false"
        }
        
        # Simular un archivo vacio
        files = {
            "archivos": ("foto_evidencia.jpg", b"123", "image/jpeg")
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.post("http://localhost:8000/incidentes/", data=data, files=files, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
