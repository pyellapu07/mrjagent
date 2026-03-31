import json
import os
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RESUME_PATH = "profile/Pradeep_Yellapu_UX-Research_Product-Design_2026.pdf"


def load_profile() -> dict:
    with open(settings.PROFILE_PATH) as f:
        return json.load(f)


async def fill_form_with_ai(page, job) -> bool:
    """Use GPT-4o to intelligently fill any job application form."""
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

    # Upload resume if file input exists
    try:
        file_input = await page.query_selector('input[type="file"]')
        if file_input:
            await file_input.set_input_files(RESUME_PATH)
    except Exception:
        pass

    return filled > 0
