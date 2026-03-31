from supabase import create_client, Client
from app.config import settings
from app.models.job import Job, JobStatus
from app.models.application import Application
from datetime import datetime
from typing import Optional
import uuid

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def save_job(job: Job) -> Job:
    job.id = str(uuid.uuid4())
    job.created_at = datetime.utcnow()
    data = job.model_dump(mode="json")
    supabase.table("jobs").insert(data).execute()
    return job


def update_job_status(job_id: str, status: JobStatus, **kwargs):
    update_data = {"status": status, **kwargs}
    supabase.table("jobs").update(update_data).eq("id", job_id).execute()


def get_job_by_telegram_message(message_id: int) -> Optional[Job]:
    result = supabase.table("jobs").select("*").eq("telegram_message_id", message_id).execute()
    if result.data:
        return Job(**result.data[0])
    return None


def get_job_by_id(job_id: str) -> Optional[Job]:
    result = supabase.table("jobs").select("*").eq("id", job_id).execute()
    if result.data:
        return Job(**result.data[0])
    return None


def job_already_seen(url: str) -> bool:
    result = supabase.table("jobs").select("id").eq("url", url).execute()
    return len(result.data) > 0


def save_application(app: Application) -> Application:
    app.id = str(uuid.uuid4())
    app.applied_at = datetime.utcnow()
    data = app.model_dump(mode="json")
    supabase.table("applications").insert(data).execute()
    return app


def get_all_applications() -> list[Application]:
    result = supabase.table("applications").select("*").order("applied_at", desc=True).execute()
    return [Application(**row) for row in result.data]
