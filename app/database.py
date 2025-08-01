# app/database.py

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.engine import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from app import config

# Update DATABASE_URL to be compatible with aiosqlite
DATABASE_URL = config.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
engine = create_async_engine(DATABASE_URL, echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session