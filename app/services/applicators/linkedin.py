from app.models.job import Job


async def apply_linkedin(job: Job) -> tuple[bool, str]:
    """LinkedIn Easy Apply handler - placeholder for now."""
    # LinkedIn has heavy bot detection - implementing carefully
    # TODO: Implement with session cookies or LinkedIn API
    print(f"LinkedIn application queued for: {job.title} at {job.company}")
    return False, "LinkedIn auto-apply not yet implemented"
