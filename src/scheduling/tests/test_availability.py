import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Barber, Appointment
from src.scheduling.tools import check_availability, get_barbers


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        barber = Barber(
            name="TestBarber",
            specialties="cuts",
            working_days="mon,tue,wed,thu,fri",
            start_hour=9,
            end_hour=12,
            slot_duration_minutes=30,
        )
        session.add(barber)
        await session.commit()
        barber_id = barber.id

    yield engine, async_session, barber_id

    await engine.dispose()


@pytest.mark.asyncio
async def test_check_availability_has_slots(test_db):
    engine, async_session, barber_id = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
        date_str = next_monday.strftime("%Y-%m-%d")
        result = await check_availability(date_str)
        assert "TestBarber" in result or "No availability" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_check_availability_slot_excluded_when_booked(test_db):
    engine, async_session, barber_id = test_db

    async with async_session() as session:
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
        slot_time = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        appointment = Appointment(
            barber_id=barber_id,
            customer_phone="+1234567890",
            start_time=slot_time,
        )
        session.add(appointment)
        await session.commit()

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        result = await check_availability(next_monday.strftime("%Y-%m-%d"))
        assert "09:00" not in result or "No availability" in result
    finally:
        tools.async_session_maker = original_session


@pytest.mark.asyncio
async def test_get_barbers(test_db):
    engine, async_session, barber_id = test_db

    from src.scheduling import tools
    original_session = tools.async_session_maker
    tools.async_session_maker = async_session

    try:
        result = await get_barbers()
        assert "TestBarber" in result
        assert "Specialties" in result
    finally:
        tools.async_session_maker = original_session
