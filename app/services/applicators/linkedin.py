from app.models.job import Job


async def apply_linkedin(job: Job) -> dict:
    """LinkedIn - send direct link for now."""
    return {
        "filled": 0,
        "skipped": [],
        "resume_uploaded": False,
        "current_url": job.url,
        "error": "LinkedIn auto-fill not yet supported"
    }
