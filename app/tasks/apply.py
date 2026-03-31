from app.models.job import Job, JobStatus
from app.services.database import update_job_status, save_application
from app.models.application import Application
from app.bot.telegram import send_message


async def trigger_application(job: Job):
    """
    Fill as much of the application as possible, then hand off to Pradeep.
    """
    await send_message(f"🤖 Working on *{job.title}* at *{job.company}*...")

    result = {}

    try:
        update_job_status(job.id, JobStatus.APPLYING)

        if job.source == "greenhouse":
            from app.services.applicators.greenhouse import apply_greenhouse
            result = await apply_greenhouse(job)
        elif job.source == "linkedin":
            from app.services.applicators.linkedin import apply_linkedin
            result = await apply_linkedin(job)
        else:
            from app.services.applicators.generic import apply_generic
            result = await apply_generic(job)

    except Exception as e:
        result = {
            "filled": 0,
            "skipped": [],
            "resume_uploaded": False,
            "current_url": job.url,
            "error": str(e)
        }

    filled = result.get("filled", 0)
    skipped = result.get("skipped", [])
    resume_uploaded = result.get("resume_uploaded", False)
    current_url = result.get("current_url", job.url)
    error = result.get("error", "")

    # Build summary message
    resume_line = "📄 Resume uploaded ✅" if resume_uploaded else "📄 Resume: manual upload needed"

    if skipped:
        skipped_line = f"⚠️ Needs your input: {', '.join(skipped[:5])}"
        if len(skipped) > 5:
            skipped_line += f" (+{len(skipped)-5} more)"
    else:
        skipped_line = ""

    if filled > 0:
        update_job_status(job.id, JobStatus.APPLIED)
        save_application(Application(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            status="partial" if skipped else "submitted"
        ))

        msg = (
            f"✅ *Filled {filled} fields!*\n\n"
            f"*{job.title}* at *{job.company}*\n\n"
            f"{resume_line}\n"
        )
        if skipped_line:
            msg += f"{skipped_line}\n"
        msg += f"\n👉 [Finish & Submit here]({current_url})"

    else:
        update_job_status(job.id, JobStatus.FAILED)
        reason = f"\n_Reason: {error}_" if error else ""
        msg = (
            f"❌ *Couldn't auto-fill*\n\n"
            f"*{job.title}* at *{job.company}*"
            f"{reason}\n\n"
            f"👉 [Apply manually here]({job.url})"
        )

    await send_message(msg)
