import asyncio
from app.database import AsyncSessionLocal
from app.models import Incidente, Conductor, Usuario
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Usuario).filter(Usuario.correo == "conductor@resq.com"))
        u = res.scalars().first()
        if not u:
            print("Usuario no encontrado")
            return
            
        res_cond = await db.execute(select(Conductor).filter(Conductor.usuario_id == u.id))
        cond = res_cond.scalars().first()
        
        res_inc = await db.execute(select(Incidente).filter(
            Incidente.conductor_id == cond.id,
            Incidente.estado_actual.notin_(['Finalizado', 'Cancelado'])
        ))
        incidentes_activos = res_inc.scalars().all()
        
        print(f"Borrando/Cancelando {len(incidentes_activos)} incidentes fantasma...")
        for inc in incidentes_activos:
            inc.estado_actual = "Cancelado"
            print(f"- Cancelado: {inc.id}")
            
        await db.commit()
        print("¡Limpieza completada!")

if __name__ == "__main__":
    asyncio.run(main())
