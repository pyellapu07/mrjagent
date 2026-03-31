from fastapi import APIRouter, Request, BackgroundTasks
from app.services.database import get_job_by_id, update_job_status
from app.models.job import JobStatus
from app.bot.telegram import answer_callback, send_message
from app.tasks.apply import trigger_application
from app.tasks.crawl import run_crawl

router = APIRouter()


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle incoming Telegram updates (button presses)."""
    data = await request.json()

    # Handle callback queries (button presses)
    if "callback_query" in data:
        cq = data["callback_query"]
        callback_id = cq["id"]
        callback_data = cq.get("data", "")

        if ":" not in callback_data:
            return {"ok": True}

        action, job_id = callback_data.split(":", 1)
        job = get_job_by_id(job_id)

        if not job:
            await answer_callback(callback_id, "Job not found.")
            return {"ok": True}

        if action == "apply":
            await answer_callback(callback_id, "✅ Got it! Applying now...")
            update_job_status(job_id, JobStatus.APPROVED)
            background_tasks.add_task(trigger_application, job)

        elif action == "skip":
            await answer_callback(callback_id, "⏭ Skipped.")
            update_job_status(job_id, JobStatus.SKIPPED)

        elif action == "save":
            await answer_callback(callback_id, "📌 Saved for later.")
            update_job_status(job_id, JobStatus.SKIPPED, notes="saved_for_later")

    return {"ok": True}


@router.get("/webhook/health")
async def health():
    return {"status": "mrjagent is running 🤖"}


@router.post("/crawl/trigger")
async def trigger_crawl(background_tasks: BackgroundTasks):
    """Manually trigger a job crawl."""
    background_tasks.add_task(run_crawl)
    return {"status": "Crawl started! Check your Telegram in a few minutes 🔍"}
