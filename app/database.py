# app/database.py

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app import config
import os

DATABASE_URL = config.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# check if config.DB_LOCATION exists, if not create it
if not os.path.exists(config.DB_LOCATION):
    os.makedirs(config.DB_LOCATION)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency to get an async database session."""
    async with async_session_maker() as session:
        yield session