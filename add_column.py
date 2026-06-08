import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(text("ALTER TABLE oportunidad_incidente ADD COLUMN tecnico_id UUID REFERENCES tecnico(id);"))
            await db.commit()
            print("Columna tecnico_id añadida exitosamente.")
        except Exception as e:
            print(f"La columna probablemente ya existe o hubo un error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
