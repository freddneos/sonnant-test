import pytest
from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.main import app


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from src.db import database
    original_session = database.async_session_maker
    database.async_session_maker = async_session

    from src.scheduling import tools
    tools.async_session_maker = async_session

    from src.scheduling import reminders
    reminders.async_session_maker = async_session

    from src.db.seed import seed_barbers
    await seed_barbers()

    yield

    database.async_session_maker = original_session
    tools.async_session_maker = original_session
    reminders.async_session_maker = original_session
    await engine.dispose()


def test_happy_path_booking_flow(test_db):
    client = TestClient(app)

    next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
    date_str = next_monday.strftime("%Y-%m-%d")

    with patch("src.sms.api.agent.run", new=AsyncMock(return_value=AsyncMock(data="Checked availability"))) as mock_run:
        with patch("src.core.config.settings.TWILIO_WEBHOOKS_VALIDATION_ENABLED", False):
            response = client.post(
                "/sms/reply",
                data={"From": "+1234567890", "Body": f"Can I get a haircut on {date_str}?"},
            )

    assert response.status_code == HTTPStatus.OK
    assert "text/xml" in response.headers["content-type"]


def test_double_booking_prevention(test_db):
    from src.scheduling.tools import book_appointment
    import asyncio

    next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
    date_str = next_monday.strftime("%Y-%m-%d")

    result1 = asyncio.run(book_appointment("Carlos", date_str, "10:00", "+1111111111", "fade"))
    assert "booked" in result1.lower() or "You're" in result1

    result2 = asyncio.run(book_appointment("Carlos", date_str, "10:00", "+1222222222", "buzz"))
    assert "taken" in result2.lower() or "Sorry" in result2


def test_invalid_date_handling(test_db):
    from src.scheduling.tools import book_appointment
    import asyncio

    result = asyncio.run(book_appointment("Carlos", "invalid-date", "10:00", "+1234567890"))
    assert "Invalid" in result


def test_non_existent_barber(test_db):
    from src.scheduling.tools import book_appointment
    import asyncio

    next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
    date_str = next_monday.strftime("%Y-%m-%d")

    result = asyncio.run(book_appointment("NonExistent", date_str, "10:00", "+1234567890"))
    assert "not found" in result.lower()


def test_empty_body_handling(test_db):
    client = TestClient(app)

    with patch("src.sms.api.agent.run", new=AsyncMock(return_value=AsyncMock(data="Please send a message"))):
        with patch("src.core.config.settings.TWILIO_WEBHOOKS_VALIDATION_ENABLED", False):
            response = client.post(
                "/sms/reply",
                data={"From": "+1234567890", "Body": ""},
            )

    assert response.status_code == HTTPStatus.OK


def test_conversation_history_persistence(test_db):
    from src.scheduling.tools import save_message, get_conversation_history
    import asyncio

    asyncio.run(save_message("+1234567890", "user", "Hello"))
    asyncio.run(save_message("+1234567890", "assistant", "Hi!"))

    history = asyncio.run(get_conversation_history("+1234567890"))
    assert len(history) == 2
    assert history[0]["content"] == "Hello"
    assert history[1]["content"] == "Hi!"


def test_customer_preference_recall(test_db):
    from src.scheduling.tools import save_customer_preference, get_customer_preference
    import asyncio

    asyncio.run(save_customer_preference("+1234567890", "fade"))
    result = asyncio.run(get_customer_preference("+1234567890"))
    assert "fade" in result.lower()
