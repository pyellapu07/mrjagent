from playwright.async_api import async_playwright
from app.models.job import Job
import asyncio


async def scrape_jobright(target_roles: list[str]) -> list[Job]:
    """Scrape job listings from Jobright AI."""
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        for role in target_roles[:3]:  # Limit roles per crawl
            try:
                search_url = f"https://jobright.ai/jobs?q={role.replace(' ', '+')}&f=Design%2CResearch"
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(3000)

                # Extract job cards
                job_cards = await page.query_selector_all("[class*='job-card'], [class*='JobCard'], article")

                for card in job_cards[:10]:  # Max 10 per role
                    try:
                        title_el = await card.query_selector("h2, h3, [class*='title']")
                        company_el = await card.query_selector("[class*='company'], [class*='employer']")
                        location_el = await card.query_selector("[class*='location']")
                        link_el = await card.query_selector("a")

                        title = await title_el.inner_text() if title_el else ""
                        company = await company_el.inner_text() if company_el else ""
                        location = await location_el.inner_text() if location_el else ""
                        url = await link_el.get_attribute("href") if link_el else ""

                        if not url:
                            continue
                        if not url.startswith("http"):
                            url = "https://jobright.ai" + url

                        if title and company:
                            jobs.append(Job(
                                title=title.strip(),
                                company=company.strip(),
                                location=location.strip() or "USA",
                                url=url,
                                source="jobright"
                            ))
                    except Exception:
                        continue

            except Exception as e:
                print(f"Jobright scrape error for {role}: {e}")
                continue

        await browser.close()

    return jobs
