import asyncio
import random
from app.database import AsyncSessionLocal
from app.models import Taller
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Taller))
        talleres = res.scalars().all()
        
        # Coordenadas base (Centro de Santa Cruz)
        base_lat = -17.78
        base_lng = -63.18
        
        print(f"Actualizando {len(talleres)} talleres...")
        for t in talleres:
            # Añadir un pequeño offset aleatorio para que estén dispersos en Santa Cruz
            offset_lat = random.uniform(-0.02, 0.02)
            offset_lng = random.uniform(-0.02, 0.02)
            
            t.latitud = base_lat + offset_lat
            t.longitud = base_lng + offset_lng
            
            print(f"- Taller {t.nombre_comercial} actualizado a: {t.latitud}, {t.longitud}")
            
        await db.commit()
        print("¡Todos los talleres han sido actualizados exitosamente!")

if __name__ == "__main__":
    asyncio.run(main())
