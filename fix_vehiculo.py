import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import Vehiculo, Conductor
import os

from dotenv import load_dotenv
load_dotenv()

async def create_vehiculo():
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        cond_res = await db.execute(select(Conductor).limit(1))
        conductor = cond_res.scalars().first()
        if conductor:
            veh_res = await db.execute(select(Vehiculo).filter_by(conductor_id=conductor.id))
            vehiculo = veh_res.scalars().first()
            if not vehiculo:
                import uuid
                vid = uuid.UUID('77777777-7777-7777-7777-777777777777')
                v = Vehiculo(id=vid, placa="1234-ABC", marca="Toyota", modelo="Corolla", ano=2022, conductor_id=conductor.id, tenant_id=conductor.tenant_id)
                db.add(v)
                await db.commit()
                print("Vehículo 77777777-7777-7777-7777-777777777777 creado.")
            else:
                print(f"Ya existe un vehículo con ID: {vehiculo.id}")

asyncio.run(create_vehiculo())
