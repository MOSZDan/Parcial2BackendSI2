import asyncio
import math
import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Taller, OportunidadIncidente

def calcular_distancia(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 999999
    R = 6371.0
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def main():
    async with AsyncSessionLocal() as db:
        print("Buscando talleres...")
        todas_los_talleres = await db.execute(select(Taller).filter(Taller.activo == True))
        talleres = todas_los_talleres.scalars().all()
        print(f"Talleres encontrados: {len(talleres)}")
        
        for t in talleres:
            try:
                dist = calcular_distancia(-17.78, -63.18, t.latitud, t.longitud)
                print(f"Distancia a taller {t.id}: {dist}")
            except Exception as e:
                print(f"Error con taller {t.id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
