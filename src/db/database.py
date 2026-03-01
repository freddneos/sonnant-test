from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base

DATABASE_URL = "sqlite+aiosqlite:///barbershop.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from src.db.seed import seed_barbers

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_barbers()
