from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import (
    EmailThread, Email, Classification, FollowUp,
    ThreadStatus, ReplyCategory, EmailDirection, FollowUpStatus,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/classification-breakdown")
def classification_breakdown(db: Session = Depends(get_db)):
    """Distribution of reply classifications."""
    results = (
        db.query(Classification.category, func.count(Classification.id))
        .group_by(Classification.category)
        .all()
    )
    return [{"category": r[0].value if r[0] else "unknown", "count": r[1]} for r in results]


@router.get("/status-breakdown")
def status_breakdown(db: Session = Depends(get_db)):
    """Distribution of thread statuses."""
    results = (
        db.query(EmailThread.status, func.count(EmailThread.id))
        .group_by(EmailThread.status)
        .all()
    )
    return [{"status": r[0].value, "count": r[1]} for r in results]


@router.get("/reply-timeline")
def reply_timeline(db: Session = Depends(get_db)):
    """Reply times in hours for each replied thread."""
    threads = (
        db.query(EmailThread)
        .options(selectinload(EmailThread.emails))
        .filter(EmailThread.status == ThreadStatus.REPLIED)
        .all()
    )

    data = []
    for t in threads:
        outbound = next((e for e in t.emails if e.direction == EmailDirection.OUTBOUND), None)
        inbound = next((e for e in t.emails if e.direction == EmailDirection.INBOUND), None)
        if outbound and inbound and outbound.sent_at and inbound.sent_at:
            hours = round((inbound.sent_at - outbound.sent_at).total_seconds() / 3600, 1)
            data.append({
                "thread_id": t.id,
                "recipient": t.recipient_name or t.recipient_email,
                "subject": t.subject,
                "reply_time_hours": hours,
                "sent_at": outbound.sent_at.isoformat(),
            })

    return sorted(data, key=lambda x: x["reply_time_hours"])


@router.get("/follow-up-effectiveness")
def follow_up_effectiveness(db: Session = Depends(get_db)):
    """How many follow-ups led to replies, by sequence number."""
    total_by_seq = (
        db.query(FollowUp.sequence_number, func.count(FollowUp.id))
        .filter(FollowUp.status == FollowUpStatus.SENT)
        .group_by(FollowUp.sequence_number)
        .all()
    )

    replied_after = (
        db.query(FollowUp.sequence_number, func.count(FollowUp.id))
        .join(EmailThread)
        .filter(
            FollowUp.status == FollowUpStatus.SENT,
            EmailThread.status == ThreadStatus.REPLIED,
        )
        .group_by(FollowUp.sequence_number)
        .all()
    )

    total_map = {r[0]: r[1] for r in total_by_seq}
    replied_map = {r[0]: r[1] for r in replied_after}

    return [
        {
            "sequence": seq,
            "sent": total_map.get(seq, 0),
            "replied": replied_map.get(seq, 0),
        }
        for seq in [1, 2, 3]
    ]


@router.get("/meeting-intents")
def meeting_intents(db: Session = Depends(get_db)):
    """Threads where meeting intent was detected — action items."""
    classifications = (
        db.query(Classification)
        .options(
            joinedload(Classification.thread).selectinload(EmailThread.emails),
        )
        .filter(Classification.has_meeting_intent == True)
        .all()
    )

    items = []
    for c in classifications:
        thread = c.thread
        reply = next((e for e in thread.emails if e.direction == EmailDirection.INBOUND), None)
        items.append({
            "thread_id": thread.id,
            "recipient": thread.recipient_name or thread.recipient_email,
            "recipient_email": thread.recipient_email,
            "subject": thread.subject,
            "reply_snippet": reply.body[:200] if reply else "",
            "classified_at": c.classified_at.isoformat() if c.classified_at else None,
        })

    return items
