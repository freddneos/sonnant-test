from fastapi import APIRouter

from src.scheduling.reminders import check_and_send_reminders

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/check")
async def trigger_reminder_check():
    await check_and_send_reminders()
    return {"status": "ok", "message": "Reminder check completed"}
