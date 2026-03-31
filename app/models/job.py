from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SKIPPED = "skipped"
    APPLYING = "applying"
    APPLIED = "applied"
    FAILED = "failed"


class Job(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    job_type: Optional[str] = None  # remote/hybrid/onsite
    description: Optional[str] = None
    url: str
    source: str  # jobright / linkedin / greenhouse / company
    match_score: Optional[int] = None
    match_reasons: Optional[list[str]] = None
    status: JobStatus = JobStatus.PENDING_APPROVAL
    telegram_message_id: Optional[int] = None
    created_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
