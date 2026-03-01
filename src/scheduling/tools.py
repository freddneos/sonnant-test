from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError

from src.db.database import async_session_maker
from src.db.models import Appointment, Barber, CustomerPreference


async def check_availability(date_str: str) -> str:
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return f"Invalid date format. Please use ISO format like '2024-03-15'."

    day_name = target_date.strftime("%a").lower()

    async with async_session_maker() as session:
        result = await session.execute(select(Barber))
        barbers = result.scalars().all()

        available_slots_text = []

        for barber in barbers:
            if day_name not in barber.working_days:
                continue

            start_dt = datetime.combine(target_date, datetime.min.time()).replace(hour=barber.start_hour)
            end_dt = datetime.combine(target_date, datetime.min.time()).replace(hour=barber.end_hour)

            all_slots = []
            current = start_dt
            while current < end_dt:
                all_slots.append(current)
                current += timedelta(minutes=barber.slot_duration_minutes)

            booked_result = await session.execute(
                select(Appointment.start_time).where(
                    Appointment.barber_id == barber.id,
                    Appointment.start_time >= start_dt,
                    Appointment.start_time < end_dt,
                )
            )
            booked_times = {row[0] for row in booked_result.fetchall()}

            open_slots = [slot for slot in all_slots if slot not in booked_times]

            if open_slots:
                slots_str = ", ".join([s.strftime("%H:%M") for s in open_slots])
                available_slots_text.append(f"{barber.name}: {slots_str}")

        if not available_slots_text:
            return f"No availability on {target_date.strftime('%Y-%m-%d')}."

        return f"Available slots on {target_date.strftime('%Y-%m-%d')}:\n" + "\n".join(available_slots_text)


async def get_barbers() -> str:
    async with async_session_maker() as session:
        result = await session.execute(select(Barber))
        barbers = result.scalars().all()

        if not barbers:
            return "No barbers available."

        barbers_text = []
        for barber in barbers:
            barbers_text.append(f"{barber.name} - Specialties: {barber.specialties}")

        return "Our barbers:\n" + "\n".join(barbers_text)


async def book_appointment(
    barber_name: str, date_str: str, time_str: str, customer_phone: str, cut_type: str = None
) -> str:
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return "Invalid date format. Please use ISO format like '2024-03-15'."

    try:
        time_parts = time_str.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=hour, minute=minute)
    except (ValueError, IndexError):
        return "Invalid time format. Please use format like '10:00' or '14:30'."

    async with async_session_maker() as session:
        result = await session.execute(select(Barber).where(Barber.name.ilike(barber_name)))
        barber = result.scalars().first()

        if not barber:
            return f"Barber '{barber_name}' not found."

        day_name = target_date.strftime("%a").lower()
        if day_name not in barber.working_days:
            return f"{barber.name} doesn't work on {target_date.strftime('%A')}s."

        if start_time.hour < barber.start_hour or start_time.hour >= barber.end_hour:
            return f"{barber.name} only works from {barber.start_hour}:00 to {barber.end_hour}:00."

        existing = await session.execute(
            select(Appointment).where(
                and_(Appointment.barber_id == barber.id, Appointment.start_time == start_time)
            )
        )
        if existing.scalars().first():
            return f"Sorry, that slot with {barber.name} is already taken."

        appointment = Appointment(
            barber_id=barber.id,
            customer_phone=customer_phone,
            start_time=start_time,
            cut_type=cut_type,
            status="confirmed",
        )
        session.add(appointment)

        try:
            await session.commit()
            return f"You're booked with {barber.name} on {target_date.strftime('%A, %B %d')} at {start_time.strftime('%I:%M %p')}!"
        except IntegrityError:
            await session.rollback()
            return f"Sorry, that slot with {barber.name} is already taken."


async def save_customer_preference(phone_number: str, preferred_cut: str) -> str:
    async with async_session_maker() as session:
        result = await session.execute(select(CustomerPreference).where(CustomerPreference.phone_number == phone_number))
        existing = result.scalars().first()

        if existing:
            existing.preferred_cut = preferred_cut
            existing.updated_at = datetime.utcnow()
        else:
            preference = CustomerPreference(phone_number=phone_number, preferred_cut=preferred_cut)
            session.add(preference)

        await session.commit()
        return f"Got it! I'll remember you prefer a {preferred_cut}."


async def get_customer_preference(phone_number: str) -> str:
    async with async_session_maker() as session:
        result = await session.execute(select(CustomerPreference).where(CustomerPreference.phone_number == phone_number))
        preference = result.scalars().first()

        if preference:
            return f"You prefer: {preference.preferred_cut}"
        return "No preference on file."
