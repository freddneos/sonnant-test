from datetime import datetime, timedelta

from sqlalchemy import select

from src.db.database import async_session_maker
from src.db.models import Appointment, Barber


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
