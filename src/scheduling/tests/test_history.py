import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.scheduling.tools import save_message, get_conversation_history


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield engine, async_session

    await engine.dispose()


@pytest.mark.asyncio
async def test_save_and_retrieve_messages(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        await save_message("+1234567890", "user", "Hello")
        await save_message("+1234567890", "assistant", "Hi there!")

        history = await get_conversation_history("+1234567890")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_history_limit(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        for i in range(15):
            await save_message("+1234567890", "user", f"Message {i}")

        history = await get_conversation_history("+1234567890", limit=5)
        assert len(history) == 5
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_history_ordering(test_db):
    engine, async_session = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        await save_message("+1234567890", "user", "First")
        await save_message("+1234567890", "assistant", "Second")
        await save_message("+1234567890", "user", "Third")

        history = await get_conversation_history("+1234567890")
        assert history[0]["content"] == "First"
        assert history[1]["content"] == "Second"
        assert history[2]["content"] == "Third"
    finally:
        tools.async_session_maker = original_session
