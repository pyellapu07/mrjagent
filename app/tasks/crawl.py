import asyncio
from app.services.scrapers.jobright import scrape_jobright
from app.services.scrapers.greenhouse import scrape_greenhouse
from app.services.matcher import score_job
from app.services.database import save_job, job_already_seen
from app.bot.telegram import send_job_approval, send_message
from app.config import settings
import json


def load_profile():
    with open(settings.PROFILE_PATH) as f:
        return json.load(f)


async def run_crawl():
    """Main crawl job - runs on schedule to find and score new jobs."""
    profile = load_profile()
    target_roles = profile["target_roles"]

    await send_message("🔍 Starting job search crawl...")

    all_jobs = []

    # Scrape all sources
    try:
        jobright_jobs = await scrape_jobright(target_roles)
        all_jobs.extend(jobright_jobs)
    except Exception as e:
        await send_message(f"⚠️ Jobright scrape failed: {e}")

    try:
        greenhouse_jobs = await scrape_greenhouse(target_roles)
        all_jobs.extend(greenhouse_jobs)
    except Exception as e:
        await send_message(f"⚠️ Greenhouse scrape failed: {e}")

    new_jobs = [j for j in all_jobs if not job_already_seen(j.url)]
    await send_message(f"📋 Found {len(new_jobs)} new jobs. Scoring...")

    sent = 0
    for job in new_jobs:
        score, reasons = score_job(job)
        job.match_score = score
        job.match_reasons = reasons

        if score >= settings.MIN_MATCH_SCORE:
            saved_job = save_job(job)
            message_id = await send_job_approval(saved_job)
            from app.services.database import update_job_status
            from app.models.job import JobStatus
            update_job_status(saved_job.id, JobStatus.PENDING_APPROVAL,
                            telegram_message_id=message_id)
            sent += 1
            await asyncio.sleep(1)  # Rate limit

    await send_message(f"✅ Crawl done. Sent {sent} job matches for your approval.")
