from playwright.async_api import async_playwright
from app.models.job import Job
from app.services.form_filler import fill_form_with_claude
import json


async def apply_greenhouse(job: Job) -> bool:
    """Apply to a Greenhouse-hosted job application."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(job.url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Check for Apply button
            apply_btn = await page.query_selector("a[href*='apply'], button:has-text('Apply')")
            if apply_btn:
                await apply_btn.click()
                await page.wait_for_load_state("networkidle")

            # Use Claude to fill the form
            success = await fill_form_with_claude(page, job)
            return success

        except Exception as e:
            print(f"Greenhouse application error: {e}")
            return False
        finally:
            await browser.close()
