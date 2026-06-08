import asyncio
import httpx
from app.database import AsyncSessionLocal
from app.models import Usuario
from app.core.security import create_access_token
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Usuario).filter(Usuario.correo == "conductor@resqauto.com")) # O el correo que use
        u = res.scalars().first()
        if not u:
            print("No conductor user found")
            return
        token = create_access_token(u.id)
        
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8000/incidentes/activo", headers={"Authorization": f"Bearer {token}"})
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
