import httpx
from app.models.job import Job
# Note: Greenhouse uses public API (no browser needed)

# Top companies using Greenhouse with relevant design/UX roles
GREENHOUSE_COMPANIES = [
    "anthropic", "figma", "notion", "linear", "vercel",
    "stripe", "airbnb", "dropbox", "hubspot", "intercom",
    "canva", "miro", "airtable", "amplitude", "brex"
]

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"


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

                    # Filter by target roles
                    if not any(kw in title for kw in keywords):
                        continue

                    location = "Remote"
                    if job_data.get("offices"):
                        location = job_data["offices"][0].get("name", "Remote")

                    jobs.append(Job(
                        title=job_data["title"],
                        company=company.capitalize(),
                        location=location,
                        url=job_data["absolute_url"],
                        source="greenhouse"
                    ))

            except Exception as e:
                print(f"Greenhouse error for {company}: {e}")
                continue

    return jobs
