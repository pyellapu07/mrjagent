from app.models.job import Job, JobStatus
from app.services.database import update_job_status, save_application
from app.models.application import Application
from app.bot.telegram import send_message
import asyncio


async def trigger_application(job: Job):
    """Orchestrate the application process for an approved job."""
    await send_message(f"🤖 Starting application for *{job.title}* at *{job.company}*...")

    try:
        update_job_status(job.id, JobStatus.APPLYING)

        # Route to correct application handler based on source
        if job.source == "greenhouse":
            from app.services.applicators.greenhouse import apply_greenhouse
            success = await apply_greenhouse(job)
        elif job.source == "linkedin":
            from app.services.applicators.linkedin import apply_linkedin
            success = await apply_linkedin(job)
        else:
            from app.services.applicators.generic import apply_generic
            success = await apply_generic(job)

        if success:
            update_job_status(job.id, JobStatus.APPLIED)
            application = Application(
                job_id=job.id,
                job_title=job.title,
                company=job.company,
                status="submitted"
            )
            save_application(application)
            await send_message(
                f"✅ *Applied!*\n\n"
                f"*{job.title}* at *{job.company}*\n"
                f"Check your email for confirmation."
            )
        else:
            update_job_status(job.id, JobStatus.FAILED)
            await send_message(
                f"❌ *Application failed*\n\n"
                f"*{job.title}* at *{job.company}*\n"
                f"[Apply manually]({job.url})"
            )

    except Exception as e:
        update_job_status(job.id, JobStatus.FAILED)
        await send_message(f"❌ Error applying to *{job.title}*: {str(e)}")
