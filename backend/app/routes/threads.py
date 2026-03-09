from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional

from app.database import get_db
from app.models import (
    EmailThread, Email, Classification, ThreadStatus, ReplyCategory,
    FollowUp, FollowUpStatus, EmailDirection, EmailType,
)
from app.schemas import ThreadOut, ThreadSummary, FollowUpAction, FollowUpOut

router = APIRouter(prefix="/api/threads", tags=["threads"])


@router.get("/", response_model=list[ThreadSummary])
def list_threads(
    status: Optional[ThreadStatus] = None,
    category: Optional[ReplyCategory] = None,
    db: Session = Depends(get_db),
):
    query = db.query(EmailThread).options(
        joinedload(EmailThread.classification),
        selectinload(EmailThread.follow_ups),
        selectinload(EmailThread.emails),
    )

    if status:
        query = query.filter(EmailThread.status == status)

    # Filter by category at the SQL level via join
    if category:
        query = query.join(Classification).filter(Classification.category == category)

    threads = query.order_by(EmailThread.updated_at.desc()).all()

    summaries = []
    for t in threads:
        last_email = t.emails[-1] if t.emails else None
        pending = sum(1 for f in t.follow_ups if f.status in (FollowUpStatus.SCHEDULED, FollowUpStatus.DRAFT_READY))

        summary = ThreadSummary(
            id=t.id,
            recipient_email=t.recipient_email,
            recipient_name=t.recipient_name,
            subject=t.subject,
            status=t.status,
            category=t.classification.category if t.classification else None,
            has_meeting_intent=t.classification.has_meeting_intent if t.classification else False,
            pending_follow_ups=pending,
            last_activity=last_email.sent_at if last_email else t.created_at,
            created_at=t.created_at,
        )
        summaries.append(summary)

    return summaries


@router.get("/{thread_id}", response_model=ThreadOut)
def get_thread(thread_id: int, db: Session = Depends(get_db)):
    thread = db.query(EmailThread).options(
        selectinload(EmailThread.emails),
        joinedload(EmailThread.classification),
        selectinload(EmailThread.follow_ups),
    ).filter(EmailThread.id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return thread


@router.post("/{thread_id}/follow-ups/{follow_up_id}/action", response_model=FollowUpOut)
def handle_follow_up_action(
    thread_id: int,
    follow_up_id: int,
    action: FollowUpAction,
    db: Session = Depends(get_db),
):
    follow_up = db.query(FollowUp).filter(
        FollowUp.id == follow_up_id,
        FollowUp.thread_id == thread_id,
    ).first()

    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    if action.action == "approve":
        follow_up.status = FollowUpStatus.APPROVED
    elif action.action == "reject":
        follow_up.status = FollowUpStatus.CANCELLED
    elif action.action == "edit":
        if action.edited_subject:
            follow_up.draft_subject = action.edited_subject
        if action.edited_body:
            follow_up.draft_body = action.edited_body
        follow_up.status = FollowUpStatus.DRAFT_READY
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    db.commit()
    db.refresh(follow_up)
    return follow_up


@router.post("/{thread_id}/follow-ups/{follow_up_id}/send", response_model=FollowUpOut)
async def send_follow_up(
    thread_id: int,
    follow_up_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Send an approved follow-up email via the active connector."""
    follow_up = db.query(FollowUp).filter(
        FollowUp.id == follow_up_id,
        FollowUp.thread_id == thread_id,
    ).first()

    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    if follow_up.status != FollowUpStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Follow-up must be approved before sending")

    if not follow_up.draft_body:
        raise HTTPException(status_code=400, detail="Follow-up has no draft body")

    thread = db.query(EmailThread).filter(EmailThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    connector = request.app.state.connector

    msg_id = await connector.send_email(
        to=thread.recipient_email,
        subject=follow_up.draft_subject or f"Re: {thread.subject}",
        body=follow_up.draft_body,
        thread_id=thread.gmail_thread_id,
    )

    # Record sent email in the thread
    email = Email(
        thread_id=thread.id,
        gmail_message_id=msg_id,
        direction=EmailDirection.OUTBOUND,
        email_type=EmailType(f"follow_up_{follow_up.sequence_number}") if follow_up.sequence_number in (1,2,3) else EmailType.FOLLOW_UP_1,
        sender="outreach@rootlabs.in",
        recipient=thread.recipient_email,
        subject=follow_up.draft_subject or f"Re: {thread.subject}",
        body=follow_up.draft_body,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(email)

    follow_up.status = FollowUpStatus.SENT
    follow_up.sent_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(follow_up)
    return follow_up
