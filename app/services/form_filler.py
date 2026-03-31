import json
import os
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RESUME_PATH = "profile/Pradeep_Yellapu_UX-Research_Product-Design_2026.pdf"


def load_profile() -> dict:
    with open(settings.PROFILE_PATH) as f:
        return json.load(f)


async def fill_form_with_ai(page, job) -> dict:
    """
    Fill as many form fields as possible.
    Returns {
        "filled": int,
        "skipped": list[str],  # fields we couldn't fill
        "resume_uploaded": bool,
        "current_url": str,
        "page_title": str
    }
    """
    profile = load_profile()

    fields = await page.evaluate("""
        () => {
            const inputs = document.querySelectorAll('input, textarea, select');
            return Array.from(inputs).map(el => ({
                type: el.type || el.tagName.toLowerCase(),
                name: el.name || el.id || el.placeholder || '',
                label: (() => {
                    if (el.id) {
                        const lbl = document.querySelector(`label[for="${el.id}"]`);
                        if (lbl) return lbl.innerText.trim();
                    }
                    const parent = el.closest('label') || el.parentElement;
                    return parent ? parent.innerText.trim().split('\\n')[0] : '';
                })(),
                placeholder: el.placeholder || '',
                required: el.required,
                visible: el.offsetParent !== null,
                options: el.tagName === 'SELECT' ?
                    Array.from(el.options).map(o => o.text) : []
            })).filter(f => f.visible && f.type !== 'hidden');
        }
    """)

    if not fields:
        return {
            "filled": 0,
            "skipped": [],
            "resume_uploaded": False,
            "current_url": page.url,
            "page_title": await page.title()
        }

    prompt = f"""You are a job application assistant. Fill as many fields as possible for this candidate.

CANDIDATE:
Name: {profile['name']}
Email: {profile['email']}
Phone: {profile['phone']}
Location: {profile['location']}
LinkedIn: {profile.get('linkedin', '')}
GitHub: {profile.get('github', '')}
Portfolio: {profile.get('portfolio', '')}
Experience: {profile['experience_years']} years in Product Design & UX Research
Current Role: {profile['experience'][0]['title']} at {profile['experience'][0]['company']}
Education: {profile['education'][0]['degree']} from {profile['education'][0]['school']} (GPA: {profile['education'][0]['gpa']})
Summary: Product Designer & UX Researcher with 5+ years shipping user-centered products.

JOB: {job.title} at {job.company}

FORM FIELDS:
{json.dumps(fields, indent=2)}

Return JSON with two keys:
{{
  "fill": {{"field_name": "value"}},
  "skip": ["field_name1", "field_name2"]
}}

"fill" = fields you can confidently fill from candidate info above.
"skip" = fields you cannot fill (passwords, custom essays, security questions, employer-specific IDs, etc).
For cover letter / "why do you want to work here" fields, write a SHORT 2-3 sentence answer using candidate info.
Skip file upload fields in both lists."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=1500
    )

    result = json.loads(response.choices[0].message.content)
    fill_data = result.get("fill", {})
    skip_list = result.get("skip", [])

    # Fill fields
    filled = 0
    for field_key, value in fill_data.items():
        try:
            selector = f'[name="{field_key}"], [id="{field_key}"]'
            el = await page.query_selector(selector)
            if not el:
                # Try by placeholder
                el = await page.query_selector(f'[placeholder="{field_key}"]')
            if el:
                is_visible = await el.is_visible()
                if not is_visible:
                    continue
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                field_type = await el.get_attribute("type") or ""
                if tag == "select":
                    try:
                        await el.select_option(label=value)
                    except Exception:
                        await el.select_option(index=1)
                elif field_type == "checkbox":
                    if str(value).lower() in ["true", "yes", "1"]:
                        await el.check()
                elif field_type == "radio":
                    await el.check()
                else:
                    await el.click()
                    await el.fill(str(value))
                filled += 1
        except Exception:
            continue

    # Upload resume
    resume_uploaded = False
    try:
        file_input = await page.query_selector('input[type="file"]')
        if file_input and os.path.exists(RESUME_PATH):
            await file_input.set_input_files(RESUME_PATH)
            resume_uploaded = True
    except Exception:
        pass

    return {
        "filled": filled,
        "skipped": skip_list,
        "resume_uploaded": resume_uploaded,
        "current_url": page.url,
        "page_title": await page.title()
    }
