from playwright.async_api import async_playwright
from app.models.job import Job
from app.services.form_filler import fill_form_with_ai
from app.browser import BROWSER_ARGS


async def apply_greenhouse(job: Job) -> tuple[bool, str]:
    """Apply to a Greenhouse-hosted job application."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(job.url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Look for Apply button to get to the actual form
            apply_btn = await page.query_selector(
                "a[href*='/applications/new'], "
                "a:has-text('Apply for this Job'), "
                "a:has-text('Apply Now'), "
                "button:has-text('Apply')"
            )
            if apply_btn:
                await apply_btn.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)

            # Must have a form to proceed
            form = await page.query_selector("form")
            if not form:
                return False, f"No application form found at {page.url}"

            return await fill_form_with_ai(page, job)

        except Exception as e:
            return False, str(e)
        finally:
            await browser.close()
