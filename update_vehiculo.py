import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

from dotenv import load_dotenv
load_dotenv()

async def fix():
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE vehiculo SET id = '77777777-7777-7777-7777-777777777777'"))
        print("Vehículo actualizado al ID 77777777-7777-7777-7777-777777777777")

asyncio.run(fix())
