import json
import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

RESUME_PATH = "profile/Pradeep_Yellapu_UX-Research_Product-Design_2026.pdf"


def load_profile() -> dict:
    with open(settings.PROFILE_PATH) as f:
        return json.load(f)


async def fill_form_with_claude(page, job) -> bool:
    """Use Claude to intelligently fill any job application form."""
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
        return False

    # Ask Claude what to fill in each field
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

For each field with a non-empty name, provide the value to fill in. Return JSON:
{{
  "field_name_or_id": "value_to_fill",
  ...
}}

Only include fields you can confidently fill. Skip file upload fields."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    text = response.content[0].text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return False

    fill_data = json.loads(match.group())

    # Fill in the form
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

    # Upload resume if there's a file input
    try:
        file_input = await page.query_selector('input[type="file"]')
        if file_input:
            await file_input.set_input_files(RESUME_PATH)
    except Exception:
        pass

    return filled > 0
