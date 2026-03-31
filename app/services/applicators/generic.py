from playwright.async_api import async_playwright
from app.models.job import Job
from app.services.form_filler import fill_form_with_ai
from app.browser import BROWSER_ARGS


async def apply_generic(job: Job) -> tuple[bool, str]:
    """Generic application handler for company career pages."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(job.url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            for selector in [
                "a:has-text('Apply Now')", "button:has-text('Apply Now')",
                "a:has-text('Apply')", "button:has-text('Apply')",
            ]:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await page.wait_for_load_state("networkidle")
                    break

            form = await page.query_selector("form")
            if not form:
                return False, f"No application form found at {page.url}"

            return await fill_form_with_ai(page, job)

        except Exception as e:
            return False, str(e)
        finally:
            await browser.close()
