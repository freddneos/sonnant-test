from sqlalchemy import select

from src.db.database import async_session_maker
from src.db.models import Barber


async def seed_barbers():
    async with async_session_maker() as session:
        result = await session.execute(select(Barber))
        existing = result.scalars().all()

        if not existing:
            barbers = [
                Barber(
                    name="Carlos",
                    specialties="fades, buzz cuts, classic cuts",
                    working_days="mon,tue,wed,thu,fri,sat",
                    start_hour=9,
                    end_hour=18,
                    slot_duration_minutes=30,
                ),
                Barber(
                    name="Miguel",
                    specialties="beard trims, scissor cuts, styling",
                    working_days="mon,tue,wed,thu,fri",
                    start_hour=9,
                    end_hour=18,
                    slot_duration_minutes=30,
                ),
                Barber(
                    name="Ana",
                    specialties="coloring, modern cuts, kids cuts",
                    working_days="tue,wed,thu,fri,sat",
                    start_hour=9,
                    end_hour=18,
                    slot_duration_minutes=30,
                ),
            ]
            session.add_all(barbers)
            await session.commit()
