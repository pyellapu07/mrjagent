import json
import anthropic
from app.config import settings
from app.models.job import Job

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def load_profile() -> dict:
    with open(settings.PROFILE_PATH) as f:
        return json.load(f)


def score_job(job: Job) -> tuple[int, list[str]]:
    """Use Claude to score a job against Pradeep's profile. Returns (score 0-100, reasons)."""
    profile = load_profile()

    prompt = f"""You are a job matching assistant. Score how well this job matches the candidate profile.

CANDIDATE PROFILE:
- Name: {profile['name']}
- Target roles: {', '.join(profile['target_roles'])}
- Experience: {profile['experience_years']} years
- Skills (Design): {', '.join(profile['skills']['design'])}
- Skills (Research): {', '.join(profile['skills']['research'])}
- Skills (Tools): {', '.join(profile['skills']['tools'])}
- Education: {profile['education'][0]['degree']} from {profile['education'][0]['school']}

JOB POSTING:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Description: {job.description or 'Not provided'}

Score this job match from 0 to 100. Return JSON only:
{{
  "score": <number>,
  "reasons": ["reason1", "reason2", "reason3"]
}}

Score 80-100: Excellent fit. 60-79: Good fit. 40-59: Partial fit. Below 40: Poor fit."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    text = response.content[0].text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        result = json.loads(match.group())
        return result.get("score", 0), result.get("reasons", [])
    return 0, []
