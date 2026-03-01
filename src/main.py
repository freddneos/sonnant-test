from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI

from src.core.config import settings
from src.db.database import init_db
from src.sms.api import router as sms_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


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
