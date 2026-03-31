from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Application(BaseModel):
    id: Optional[str] = None
    job_id: str
    job_title: str
    company: str
    applied_at: Optional[datetime] = None
    confirmation_email: Optional[str] = None
    status: str = "submitted"  # submitted / confirmed / rejected / interview
    notes: Optional[str] = None
