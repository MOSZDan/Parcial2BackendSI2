from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine
from app.api.routers import auth, vehiculos, talleres, incidentes, logistica, finanzas, ia, tracking, sincronizacion, analitica

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(
    title="ResQ Auto API",
    description="Backend Multi-tenant SaaS para la plataforma inteligente de atención de emergencias vehiculares.",
    version="5.0.0",
    lifespan=lifespan
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(vehiculos.router)
app.include_router(talleres.router)
app.include_router(incidentes.router)
app.include_router(logistica.router)
app.include_router(finanzas.router)
app.include_router(ia.router)
app.include_router(tracking.router)
app.include_router(sincronizacion.router)
app.include_router(analitica.router)

@app.get("/")
async def root():
    return {"message": "ResQ Auto API: Ciclos 1 al 5 desplegados y operativos!"}
