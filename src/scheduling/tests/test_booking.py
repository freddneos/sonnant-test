import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Barber, Appointment
from src.scheduling.tools import book_appointment


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        barber = Barber(
            name="Carlos",
            specialties="fades",
            working_days="mon,tue,wed,thu,fri,sat",
            start_hour=9,
            end_hour=18,
            slot_duration_minutes=30,
        )
        session.add(barber)
        await session.commit()
        barber_id = barber.id

    yield engine, async_session, barber_id

    await engine.dispose()


@pytest.mark.asyncio
async def test_book_appointment_success(test_db):
    engine, async_session, barber_id = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
        result = await book_appointment(
            barber_name="Carlos",
            date_str=next_monday.strftime("%Y-%m-%d"),
            time_str="10:00",
            customer_phone="+1234567890",
            cut_type="fade",
        )
        assert "You're booked" in result or "Carlos" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_book_appointment_double_booking(test_db):
    engine, async_session, barber_id = test_db

    next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
    slot_time = next_monday.replace(hour=10, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        appointment = Appointment(
            barber_id=barber_id,
            customer_phone="+1111111111",
            start_time=slot_time,
        )
        session.add(appointment)
        await session.commit()

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        result = await book_appointment(
            barber_name="Carlos",
            date_str=next_monday.strftime("%Y-%m-%d"),
            time_str="10:00",
            customer_phone="+1234567890",
        )
        assert "already taken" in result or "Sorry" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_book_appointment_non_working_day(test_db):
    engine, async_session, barber_id = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        next_sunday = datetime.now() + timedelta(days=(6 - datetime.now().weekday() + 7) % 7)
        if next_sunday.weekday() != 6:
            next_sunday = datetime.now() + timedelta(days=(13 - datetime.now().weekday()))

        result = await book_appointment(
            barber_name="Carlos",
            date_str=next_sunday.strftime("%Y-%m-%d"),
            time_str="10:00",
            customer_phone="+1234567890",
        )
        assert "doesn't work" in result or "not found" in result or "Sorry" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_book_appointment_outside_hours(test_db):
    engine, async_session, barber_id = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
        result = await book_appointment(
            barber_name="Carlos",
            date_str=next_monday.strftime("%Y-%m-%d"),
            time_str="20:00",
            customer_phone="+1234567890",
        )
        assert "only works from" in result
    finally:
        tools.async_session_maker = original_session
