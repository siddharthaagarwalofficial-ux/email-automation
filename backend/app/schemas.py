from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models import (
    ThreadStatus, ReplyCategory, EmailDirection, EmailType, FollowUpStatus
)


class EmailOut(BaseModel):
    id: int
    thread_id: int
    direction: EmailDirection
    email_type: EmailType
    sender: str
    recipient: str
    subject: str
    body: str
    sent_at: datetime

    class Config:
        from_attributes = True


class ClassificationOut(BaseModel):
    id: int
    thread_id: int
    category: ReplyCategory
    confidence: float
    reasoning: Optional[str]
    has_meeting_intent: bool
    classified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FollowUpOut(BaseModel):
    id: int
    thread_id: int
    sequence_number: int
    scheduled_for: datetime
    draft_subject: Optional[str]
    draft_body: Optional[str]
    status: FollowUpStatus
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class ThreadOut(BaseModel):
    id: int
    gmail_thread_id: Optional[str]
    recipient_email: str
    recipient_name: Optional[str]
    subject: str
    status: ThreadStatus
    created_at: datetime
    updated_at: datetime
    emails: list[EmailOut] = []
    classification: Optional[ClassificationOut] = None
    follow_ups: list[FollowUpOut] = []

    class Config:
        from_attributes = True


class ThreadSummary(BaseModel):
    id: int
    recipient_email: str
    recipient_name: Optional[str]
    subject: str
    status: ThreadStatus
    category: Optional[ReplyCategory] = None
    has_meeting_intent: bool = False
    pending_follow_ups: int = 0
    last_activity: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class FollowUpAction(BaseModel):
    action: str  # "approve", "reject", "edit"
    edited_subject: Optional[str] = None
    edited_body: Optional[str] = None


class DashboardStats(BaseModel):
    total_threads: int
    awaiting_reply: int
    replied: int
    positive_replies: int
    negative_replies: int
    pending_follow_ups: int
    drafts_for_review: int
    reply_rate: float
    avg_reply_time_hours: Optional[float]
