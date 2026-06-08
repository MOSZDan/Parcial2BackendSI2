import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Incidente, Conductor

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Incidente).order_by(Incidente.created_at.desc()).limit(5))
        incidentes = res.scalars().all()
        for i in incidentes:
            print(f"[{i.id}] {i.estado_actual} - Conductor: {i.conductor_id}")

if __name__ == "__main__":
    asyncio.run(main())
