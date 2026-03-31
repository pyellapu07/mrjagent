from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routers import webhook
from app.tasks.crawl import run_crawl
import httpx
import os
import subprocess

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Install Chromium at startup (persists for this process lifetime)
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True, timeout=120)
        print("✅ Chromium installed successfully")
    except Exception as e:
        print(f"⚠️ Chromium install warning: {e}")

    # Register Telegram webhook
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    webhook_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if bot_token and webhook_url:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                json={"url": f"{webhook_url}/webhook/telegram"}
            )

    # Schedule crawl: every 6 hours
    scheduler.add_job(run_crawl, "interval", hours=6, id="job_crawl")
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(
    title="mrjagent",
    description="Autonomous Job Application Agent for Pradeep",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(webhook.router)


@app.get("/")
async def root():
    return {"message": "mrjagent is alive 🤖", "status": "running"}
