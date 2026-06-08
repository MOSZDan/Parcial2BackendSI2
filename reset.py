import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def reset_alembic():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Eliminando alembic_version...")
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await engine.dispose()

asyncio.run(reset_alembic())
