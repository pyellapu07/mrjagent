from playwright.async_api import async_playwright
from app.models.job import Job
from app.services.form_filler import fill_form_with_ai
from app.browser import BROWSER_ARGS


async def apply_greenhouse(job: Job) -> dict:
    """
    Navigate to Greenhouse job, fill all possible fields, return handoff info.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(job.url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Click Apply button to get to the actual form
            for selector in [
                "a[href*='/applications/new']",
                "a:has-text('Apply for this Job')",
                "a:has-text('Apply Now')",
                "button:has-text('Apply Now')",
                "a:has-text('Apply')",
            ]:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                    break

            form = await page.query_selector("form")
            if not form:
                return {
                    "filled": 0,
                    "skipped": [],
                    "resume_uploaded": False,
                    "current_url": job.url,
                    "page_title": job.title,
                    "error": "No application form found"
                }

            result = await fill_form_with_ai(page, job)
            return result

        except Exception as e:
            return {
                "filled": 0,
                "skipped": [],
                "resume_uploaded": False,
                "current_url": job.url,
                "page_title": job.title,
                "error": str(e)
            }
        finally:
            await browser.close()
