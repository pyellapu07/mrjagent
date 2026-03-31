import httpx
from app.models.job import Job
from datetime import datetime, timezone

# Top companies using Greenhouse with relevant design/UX roles
GREENHOUSE_COMPANIES = [
    "anthropic", "figma", "notion", "linear", "vercel",
    "stripe", "airbnb", "dropbox", "hubspot", "intercom",
    "canva", "miro", "airtable", "amplitude", "brex"
]

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"


def parse_gh_date(date_str: str) -> datetime | None:
    """Parse Greenhouse date string like '2026-03-28T12:00:00.000Z'"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


def days_ago(dt: datetime | None) -> str:
    if not dt:
        return "Unknown"
    now = datetime.now(timezone.utc)
    diff = now - dt
    if diff.days == 0:
        return "Today"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days <= 7:
        return f"{diff.days}d ago"
    elif diff.days <= 30:
        return f"{diff.days // 7}w ago"
    else:
        return f"{diff.days // 30}mo ago"


async def scrape_greenhouse(target_roles: list[str]) -> list[Job]:
    """Use Greenhouse public API to find UX/Design jobs."""
    jobs = []
    keywords = [r.lower() for r in target_roles]

    async with httpx.AsyncClient(timeout=15) as client:
        for company in GREENHOUSE_COMPANIES:
            try:
                response = await client.get(
                    GREENHOUSE_API.format(company=company),
                    params={"content": "true"}
                )
                if response.status_code != 200:
                    continue

                data = response.json()
                for job_data in data.get("jobs", []):
                    title = job_data.get("title", "").lower()

                    if not any(kw in title for kw in keywords):
                        continue

                    location = "Remote"
                    if job_data.get("offices"):
                        location = job_data["offices"][0].get("name", "Remote")

                    posted_at = parse_gh_date(job_data.get("updated_at") or job_data.get("created_at"))

                    jobs.append(Job(
                        title=job_data["title"],
                        company=company.capitalize(),
                        location=location,
                        url=job_data["absolute_url"],
                        source="greenhouse",
                        posted_at=posted_at
                    ))

            except Exception as e:
                print(f"Greenhouse error for {company}: {e}")
                continue

    return jobs
