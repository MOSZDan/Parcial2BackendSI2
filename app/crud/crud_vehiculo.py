from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Vehiculo, Conductor
from app.schemas.vehiculo import VehiculoCreate
import uuid

async def create_vehiculo(db: AsyncSession, vehiculo: VehiculoCreate, conductor_id: uuid.UUID, tenant_id: uuid.UUID):
    # Validar si placa ya existe
    result = await db.execute(select(Vehiculo).filter(Vehiculo.placa == vehiculo.placa))
    if result.scalars().first():
        return None

    db_vehiculo = Vehiculo(
        placa=vehiculo.placa,
        marca=vehiculo.marca,
        modelo=vehiculo.modelo,
        ano=vehiculo.ano,
        color=vehiculo.color,
        conductor_id=conductor_id,
        tenant_id=tenant_id
    )
    db.add(db_vehiculo)
    await db.commit()
    await db.refresh(db_vehiculo)
    return db_vehiculo

async def get_conductor_by_usuario_id(db: AsyncSession, usuario_id: uuid.UUID):
    result = await db.execute(select(Conductor).filter(Conductor.usuario_id == usuario_id))
    return result.scalars().first()

async def get_vehiculos_by_conductor(db: AsyncSession, conductor_id: uuid.UUID):
    result = await db.execute(select(Vehiculo).filter(Vehiculo.conductor_id == conductor_id))
    return result.scalars().all()
