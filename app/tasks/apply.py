from app.models.job import Job, JobStatus
from app.services.database import update_job_status, save_application
from app.models.application import Application
from app.bot.telegram import send_message


async def trigger_application(job: Job):
    """Orchestrate the application process for an approved job."""
    await send_message(f"🤖 Starting application for *{job.title}* at *{job.company}*...")

    success = False
    error_msg = ""

    try:
        update_job_status(job.id, JobStatus.APPLYING)

        if job.source == "greenhouse":
            from app.services.applicators.greenhouse import apply_greenhouse
            success = await apply_greenhouse(job)
        elif job.source == "linkedin":
            from app.services.applicators.linkedin import apply_linkedin
            success = await apply_linkedin(job)
        else:
            from app.services.applicators.generic import apply_generic
            success = await apply_generic(job)

    except Exception as e:
        error_msg = str(e)
        success = False

    if success:
        update_job_status(job.id, JobStatus.APPLIED)
        save_application(Application(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            status="submitted"
        ))
        await send_message(
            f"✅ *Submitted!*\n\n"
            f"*{job.title}* at *{job.company}*\n"
            f"Watch your inbox at `pyellapu@umd.edu` for confirmation."
        )
    else:
        update_job_status(job.id, JobStatus.FAILED)
        reason = f"\n_Error: {error_msg}_" if error_msg else ""
        await send_message(
            f"❌ *Could not auto-apply*\n\n"
            f"*{job.title}* at *{job.company}*\n"
            f"[Apply manually here]({job.url}){reason}"
        )
