import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Barber, Appointment
from src.scheduling.reminders import check_and_send_reminders


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        barber = Barber(name="Carlos", specialties="fades", working_days="mon,tue,wed,thu,fri,sat")
        session.add(barber)
        await session.commit()
        barber_id = barber.id

    yield engine, async_session, barber_id

    await engine.dispose()


@pytest.mark.asyncio
async def test_reminder_for_old_appointment(test_db):
    engine, async_session, barber_id = test_db

    old_date = datetime.utcnow() - timedelta(days=95)
    async with async_session() as session:
        appointment = Appointment(
            barber_id=barber_id,
            customer_phone="+1234567890",
            start_time=old_date,
            reminder_sent="false",
            status="confirmed",
        )
        session.add(appointment)
        await session.commit()
        appt_id = appointment.id

    from src.scheduling import reminders
    original_session = reminders.async_session_maker
    reminders.async_session_maker = async_session

    try:
        with patch("src.scheduling.reminders.settings") as mock_settings:
            mock_settings.REMINDER_DAYS = 90
            mock_settings.TWILIO_ACCOUNT_SID = None
            mock_settings.TWILIO_PHONE_NUMBER = None

            await check_and_send_reminders()

        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Appointment).where(Appointment.id == appt_id))
            updated_appt = result.scalars().first()
            assert updated_appt.reminder_sent == "true"
    finally:
        reminders.async_session_maker = original_session


@pytest.mark.asyncio
async def test_no_reminder_for_recent_appointment(test_db):
    engine, async_session, barber_id = test_db

    recent_date = datetime.utcnow() - timedelta(days=30)
    async with async_session() as session:
        appointment = Appointment(
            barber_id=barber_id,
            customer_phone="+1234567890",
            start_time=recent_date,
            reminder_sent="false",
            status="confirmed",
        )
        session.add(appointment)
        await session.commit()
        appt_id = appointment.id

    from src.scheduling import reminders
    original_session = reminders.async_session_maker
    reminders.async_session_maker = async_session

    try:
        with patch("src.scheduling.reminders.settings") as mock_settings:
            mock_settings.REMINDER_DAYS = 90
            mock_settings.TWILIO_ACCOUNT_SID = None

            await check_and_send_reminders()

        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Appointment).where(Appointment.id == appt_id))
            updated_appt = result.scalars().first()
            assert updated_appt.reminder_sent == "false"
    finally:
        reminders.async_session_maker = original_session


@pytest.mark.asyncio
async def test_skip_already_reminded(test_db):
    engine, async_session, barber_id = test_db

    old_date = datetime.utcnow() - timedelta(days=95)
    async with async_session() as session:
        appointment = Appointment(
            barber_id=barber_id,
            customer_phone="+1234567890",
            start_time=old_date,
            reminder_sent="true",
            status="confirmed",
        )
        session.add(appointment)
        await session.commit()

    from src.scheduling import reminders
    original_session = reminders.async_session_maker
    reminders.async_session_maker = async_session

    try:
        with patch("src.scheduling.reminders.settings") as mock_settings:
            mock_settings.REMINDER_DAYS = 90
            mock_settings.TWILIO_ACCOUNT_SID = None

            await check_and_send_reminders()
    finally:
        reminders.async_session_maker = original_session
