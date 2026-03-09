from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.database import get_db
from app.models import (
    EmailThread, ThreadStatus, Classification, ReplyCategory,
    FollowUp, FollowUpStatus, Email, EmailDirection,
)
from app.schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(EmailThread).count()

    awaiting = db.query(EmailThread).filter(
        EmailThread.status.in_([
            ThreadStatus.SENT, ThreadStatus.AWAITING_REPLY,
            ThreadStatus.FOLLOW_UP_1, ThreadStatus.FOLLOW_UP_2, ThreadStatus.FOLLOW_UP_3,
        ])
    ).count()

    replied = db.query(EmailThread).filter(EmailThread.status == ThreadStatus.REPLIED).count()

    positive = db.query(Classification).filter(Classification.category == ReplyCategory.POSITIVE).count()
    negative = db.query(Classification).filter(Classification.category == ReplyCategory.NEGATIVE).count()

    pending_fups = db.query(FollowUp).filter(
        FollowUp.status.in_([FollowUpStatus.SCHEDULED, FollowUpStatus.DRAFT_READY])
    ).count()

    drafts_review = db.query(FollowUp).filter(FollowUp.status == FollowUpStatus.DRAFT_READY).count()

    reply_rate = (replied / total * 100) if total > 0 else 0.0

    # Average reply time
    avg_reply_time = None
    replied_threads = (
        db.query(EmailThread)
        .options(selectinload(EmailThread.emails))
        .filter(EmailThread.status == ThreadStatus.REPLIED)
        .all()
    )
    if replied_threads:
        total_hours = 0
        count = 0
        for t in replied_threads:
            outbound = next((e for e in t.emails if e.direction == EmailDirection.OUTBOUND), None)
            inbound = next((e for e in t.emails if e.direction == EmailDirection.INBOUND), None)
            if outbound and inbound and outbound.sent_at and inbound.sent_at:
                delta = (inbound.sent_at - outbound.sent_at).total_seconds() / 3600
                total_hours += delta
                count += 1
        if count > 0:
            avg_reply_time = round(total_hours / count, 1)

    return DashboardStats(
        total_threads=total,
        awaiting_reply=awaiting,
        replied=replied,
        positive_replies=positive,
        negative_replies=negative,
        pending_follow_ups=pending_fups,
        drafts_for_review=drafts_review,
        reply_rate=round(reply_rate, 1),
        avg_reply_time_hours=avg_reply_time,
    )
