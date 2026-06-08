from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.database import get_db
from app.schemas.user import UsuarioCreate, UsuarioResponse, Token, PasswordRecovery
from app.crud.crud_user import create_user, get_user_by_email
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user
from app.models import Usuario, Sesion
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/register", response_model=UsuarioResponse)
async def register(user: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=user.correo)
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    new_user = await create_user(db, user)
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    
    # Guardar sesión en base de datos (CU-01)
    db_sesion = Sesion(
        token=access_token,
        usuario_id=user.id,
        tenant_id=user.tenant_id
    )
    db.add(db_sesion)
    await db.commit()

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/recover")
async def recover_password(data: PasswordRecovery, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email=data.correo)
    if not user:
        raise HTTPException(status_code=404, detail="El correo no figura en la base de datos")
    
    # Simulación visual en consola del CU-03
    recovery_token = create_access_token(subject=user.id)
    print(f"\n=========================================")
    print(f"SIMULACIÓN DE CORREO: Recuperación de Contraseña")
    print(f"Para: {user.correo}")
    print(f"Enlace de recuperación: http://tudominio.com/reset-password?token={recovery_token}")
    print(f"=========================================\n")
    
    return {"msg": "Correo de recuperación enviado (ver consola)"}

@router.post("/logout")
async def logout(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db), token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login"))):
    from sqlalchemy import select
    result = await db.execute(select(Sesion).filter(Sesion.token == token))
    sesion = result.scalars().first()
    if sesion:
        sesion.fecha_fin = datetime.utcnow()
        await db.commit()
    
    return {"mensaje": "Sesión cerrada correctamente"}

@router.get("/me")
async def get_me(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import Rol
    res_rol = await db.execute(select(Rol).filter(Rol.id == current_user.rol_id))
    rol = res_rol.scalars().first()
    
    return {
        "id": current_user.id,
        "correo": current_user.correo,
        "estado": current_user.estado,
        "tenant_id": current_user.tenant_id,
        "tipo_usuario": rol.nombre if rol else "Desconocido"
    }
