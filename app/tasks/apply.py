from app.models.job import Job, JobStatus
from app.services.database import update_job_status, save_application
from app.models.application import Application
from app.bot.telegram import send_apply_handoff


async def trigger_application(job: Job):
    """
    User tapped Apply — send them directly to the application link.
    No auto-submit. No false positives.
    """
    update_job_status(job.id, JobStatus.APPROVED)
    save_application(Application(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        status="sent_to_user"
    ))
    await send_apply_handoff(job)
