import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.scheduling.tools import save_customer_preference, get_customer_preference


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield engine, async_session

    await engine.dispose()


@pytest.mark.asyncio
async def test_save_new_preference(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        result = await save_customer_preference("+1234567890", "fade")
        assert "remember" in result or "Got it" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_update_existing_preference(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        await save_customer_preference("+1234567890", "fade")
        result = await save_customer_preference("+1234567890", "buzz cut")
        assert "buzz cut" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_get_preference(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        await save_customer_preference("+1234567890", "fade")
        result = await get_customer_preference("+1234567890")
        assert "fade" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_get_preference_not_found(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        result = await get_customer_preference("+9999999999")
        assert "No preference" in result
    finally:
        tools.async_session_maker = original_session
