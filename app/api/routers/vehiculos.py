from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.vehiculo import VehiculoCreate, VehiculoResponse
from app.crud.crud_vehiculo import create_vehiculo, get_conductor_by_usuario_id
from app.api.deps import get_current_user
from app.models import Usuario

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

@router.post("/", response_model=VehiculoResponse)
async def registrar_vehiculo(
    vehiculo: VehiculoCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    conductor = await get_conductor_by_usuario_id(db, current_user.id)
    if not conductor:
        raise HTTPException(status_code=403, detail="El usuario actual no es un conductor registrado.")
    
    db_vehiculo = await create_vehiculo(db, vehiculo, conductor.id, current_user.tenant_id)
    if not db_vehiculo:
        raise HTTPException(status_code=400, detail="La placa del vehículo ya se encuentra registrada.")
        
    return db_vehiculo

from typing import List
@router.get("/mis_vehiculos", response_model=List[VehiculoResponse])
async def mis_vehiculos(
    db: AsyncSession = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    from app.crud.crud_vehiculo import get_vehiculos_by_conductor
    conductor = await get_conductor_by_usuario_id(db, current_user.id)
    if not conductor:
        raise HTTPException(status_code=403, detail="El usuario no es conductor.")
        
    vehiculos = await get_vehiculos_by_conductor(db, conductor.id)
    return vehiculos
