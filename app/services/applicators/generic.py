from playwright.async_api import async_playwright
from app.models.job import Job
from app.services.form_filler import fill_form_with_ai
from app.browser import BROWSER_ARGS


async def apply_generic(job: Job) -> bool:
    """Generic application handler for company career pages."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(job.url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            for selector in ["a:has-text('Apply')", "button:has-text('Apply')",
                             "a:has-text('Apply Now')", "button:has-text('Apply Now')"]:
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await page.wait_for_load_state("networkidle")
                    break

            success = await fill_form_with_ai(page, job)
            return success

        except Exception as e:
            print(f"Generic application error: {e}")
            return False
        finally:
            await browser.close()
