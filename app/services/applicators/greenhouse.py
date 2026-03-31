from playwright.async_api import async_playwright
from app.models.job import Job
from app.services.form_filler import fill_form_with_ai
from app.browser import BROWSER_ARGS


async def apply_greenhouse(job: Job) -> bool:
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

            # Try direct apply URL first (Greenhouse pattern)
            current_url = page.url
            if "/jobs/" in current_url and "/applications/" not in current_url:
                apply_url = current_url.rstrip("/") + "?gh_src=mrjagent"
                # Look for Apply Now button
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

            # Check we're on an actual application form (not just listing)
            form = await page.query_selector("form")
            if not form:
                print(f"No form found on {page.url}")
                return False

            success = await fill_form_with_ai(page, job)
            return success

        except Exception as e:
            print(f"Greenhouse application error: {e}")
            raise  # Re-raise so apply.py catches it properly
        finally:
            await browser.close()
