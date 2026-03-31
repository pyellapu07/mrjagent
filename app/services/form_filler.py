import json
import os
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RESUME_PATH = "profile/Pradeep_Yellapu_UX-Research_Product-Design_2026.pdf"

# Confirmation indicators — if any of these appear after submit, it worked
SUCCESS_INDICATORS = [
    "thank you", "thanks for applying", "application received",
    "application submitted", "you've applied", "successfully submitted",
    "we'll be in touch", "application complete", "good luck"
]

# Error indicators — if these appear, submission failed
ERROR_INDICATORS = [
    "error", "required", "invalid", "please fill", "missing",
    "captcha", "verification required"
]


def load_profile() -> dict:
    with open(settings.PROFILE_PATH) as f:
        return json.load(f)


async def fill_form_with_ai(page, job) -> tuple[bool, str]:
    """
    Fill and submit a job application form.
    Returns (success: bool, message: str)
    """
    profile = load_profile()

    # Get all form fields on page
    fields = await page.evaluate("""
        () => {
            const inputs = document.querySelectorAll('input, textarea, select');
            return Array.from(inputs).map(el => ({
                type: el.type || el.tagName.toLowerCase(),
                name: el.name || el.id || el.placeholder || '',
                label: document.querySelector(`label[for="${el.id}"]`)?.innerText || '',
                placeholder: el.placeholder || '',
                required: el.required,
                options: el.tagName === 'SELECT' ?
                    Array.from(el.options).map(o => o.text) : []
            }));
        }
    """)

    if not fields:
        return False, "No form fields found on page"

    prompt = f"""You are filling out a job application for this candidate:

Name: {profile['name']}
Email: {profile['email']}
Phone: {profile['phone']}
Location: {profile['location']}
LinkedIn: {profile.get('linkedin', '')}
GitHub: {profile.get('github', '')}
Portfolio: {profile.get('portfolio', '')}
Experience: {profile['experience_years']} years
Current Role: {profile['experience'][0]['title']} at {profile['experience'][0]['company']}
Education: {profile['education'][0]['degree']} from {profile['education'][0]['school']}

Job: {job.title} at {job.company}

Form fields detected:
{json.dumps(fields, indent=2)}

For each field with a non-empty name, provide the value to fill in.
Return JSON only with field name as key and value to fill as value.
Only include fields you can confidently fill. Skip file upload fields."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=1000
    )

    fill_data = json.loads(response.choices[0].message.content)

    # Fill in the form fields
    filled = 0
    for field_key, value in fill_data.items():
        try:
            selector = f'[name="{field_key}"], [id="{field_key}"], [placeholder="{field_key}"]'
            el = await page.query_selector(selector)
            if el:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    await el.select_option(label=value)
                else:
                    await el.fill(str(value))
                filled += 1
        except Exception:
            continue

    if filled == 0:
        return False, "Could not fill any form fields"

    # Upload resume if file input exists
    try:
        file_input = await page.query_selector('input[type="file"]')
        if file_input:
            await file_input.set_input_files(RESUME_PATH)
    except Exception:
        pass

    # Click submit button
    url_before = page.url
    clicked = False
    for selector in [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit Application")',
        'button:has-text("Submit")',
        'button:has-text("Apply Now")',
        'button:has-text("Apply")',
        'button:has-text("Send Application")',
    ]:
        try:
            btn = await page.query_selector(selector)
            if btn:
                is_visible = await btn.is_visible()
                is_enabled = await btn.is_enabled()
                if is_visible and is_enabled:
                    await btn.click()
                    await page.wait_for_timeout(4000)
                    clicked = True
                    break
        except Exception:
            continue

    if not clicked:
        return False, "Could not find or click submit button"

    # Verify success by checking page content after submit
    url_after = page.url
    page_text = (await page.inner_text("body")).lower()

    # URL changed = likely navigated to confirmation page
    url_changed = url_after != url_before

    # Check for success/error keywords
    has_success = any(indicator in page_text for indicator in SUCCESS_INDICATORS)
    has_error = any(indicator in page_text for indicator in ERROR_INDICATORS)

    if has_success and not has_error:
        return True, "Confirmation page detected"
    elif url_changed and not has_error:
        return True, f"Redirected to {url_after}"
    elif has_error:
        # Capture what went wrong
        error_snippet = next(
            (ind for ind in ERROR_INDICATORS if ind in page_text), "unknown error"
        )
        return False, f"Form error detected: '{error_snippet}'"
    else:
        # Ambiguous — clicked submit but can't confirm
        return False, "Submitted but could not verify confirmation"
