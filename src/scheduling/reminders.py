import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select

from src.core.config import settings
from src.db.database import async_session_maker
from src.db.models import Appointment

logger = logging.getLogger("app")


async def check_and_send_reminders():
    logger.info("Checking for appointments needing 90-day reminders...")

    reminder_threshold = datetime.utcnow() - timedelta(days=settings.REMINDER_DAYS)

    async with async_session_maker() as session:
        result = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.start_time <= reminder_threshold,
                    Appointment.reminder_sent == "false",
                    Appointment.status == "confirmed",
                )
            )
        )
        appointments = result.scalars().all()

        for appointment in appointments:
            try:
                if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_PHONE_NUMBER:
                    from twilio.rest import Client

                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    client.messages.create(
                        body=f"It's been {settings.REMINDER_DAYS} days since your last visit! Ready for another cut? Reply to book.",
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=appointment.customer_phone,
                    )
                    logger.info(f"Sent reminder to {appointment.customer_phone}")
                else:
                    logger.debug(f"Twilio not configured, skipping reminder for {appointment.customer_phone}")

                appointment.reminder_sent = "true"
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}", exc_info=True)

        await session.commit()

    logger.info(f"Reminder check complete. Sent {len(appointments)} reminders.")


async def reminder_background_task():
    while True:
        try:
            await check_and_send_reminders()
        except Exception as e:
            logger.error(f"Error in reminder task: {e}", exc_info=True)
        await asyncio.sleep(3600)
