import httpx
from app.config import settings
from app.models.job import Job
from app.services.scrapers.greenhouse import days_ago

TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


async def send_job_approval(job: Job) -> int:
    """Send a job card to Pradeep on Telegram for approval. Returns message_id."""
    salary_text = f"💰 {job.salary}" if job.salary else "💰 Salary not listed"
    location_text = f"📍 {job.location}"
    source_emoji = {"jobright": "🎯", "linkedin": "💼", "greenhouse": "🌿"}.get(job.source, "🔗")
    posted_text = f"🗓 Posted: {days_ago(job.posted_at)}" if job.posted_at else ""

    reasons_text = "\n".join([f"  ✓ {r}" for r in (job.match_reasons or [])[:3]])

    message = f"""{source_emoji} *New Job Match* — {job.match_score}% fit

*{job.title}*
🏢 {job.company}
{location_text}
{salary_text}
{posted_text}

*Why it matches:*
{reasons_text}

[👉 View & Apply]({job.url})""".strip()

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Apply", "callback_data": f"apply:{job.id}"},
            {"text": "⏭ Skip", "callback_data": f"skip:{job.id}"},
            {"text": "📌 Save", "callback_data": f"save:{job.id}"}
        ]]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
            "reply_markup": keyboard
        })
        data = response.json()
        return data["result"]["message_id"]


async def send_apply_handoff(job: Job):
    """
    Send a clean handoff message after tapping Apply —
    just the direct link, no false positives.
    """
    message = f"""📋 *Ready to apply!*

*{job.title}* at *{job.company}*
🗓 Posted: {days_ago(job.posted_at) if job.posted_at else 'Unknown'}

👉 [Open Application]({job.url})

_Tap the link → the form is waiting for you._"""

    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        })


async def send_message(text: str):
    """Send a plain message to Pradeep."""
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })


async def answer_callback(callback_query_id: str, text: str = ""):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/answerCallbackQuery", json={
            "callback_query_id": callback_query_id,
            "text": text
        })
