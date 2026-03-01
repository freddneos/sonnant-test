import asyncio
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI

from src.core.config import settings
from src.db.database import init_db
from src.scheduling.api import router as reminders_router
from src.scheduling.reminders import reminder_background_task
from src.sms.api import router as sms_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(reminder_background_task())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


#
# Initialize application.
#
app = FastAPI(title=settings.APPLICATION_NAME, lifespan=lifespan)


#
# Healthcheck endpoint.
#
@app.get("/", tags=["healthcheck"])
async def health_check():
    """
    Healthcheck endpoint to ensure the application is running.
    """

    return {"status": HTTPStatus.OK, "message": f"{settings.APPLICATION_NAME} is running."}


#
# Include API routes.
#
app.include_router(router=sms_router)
app.include_router(router=reminders_router)
