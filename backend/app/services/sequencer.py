import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import settings
from app.models import (
    EmailThread, Email, Classification, FollowUp,
    ThreadStatus, EmailDirection, EmailType, ReplyCategory, FollowUpStatus,
)
from app.services.classifier import classify_reply
from app.services.drafter import draft_follow_up, draft_auto_reply

logger = logging.getLogger(__name__)

FOLLOW_UP_DELAYS = {
    1: settings.followup_delay_1,
    2: settings.followup_delay_2,
    3: settings.followup_delay_3,
}


def run_classification(db: Session) -> dict:
    """Classify all replied threads that don't have a classification yet."""
    threads = (
        db.query(EmailThread)
        .options(selectinload(EmailThread.emails))
        .filter(
            EmailThread.status == ThreadStatus.REPLIED,
            ~EmailThread.id.in_(db.query(Classification.thread_id)),
        )
        .all()
    )

    classified = 0
    errors = 0
    for thread in threads:
        outbound = next(
            (e for e in thread.emails if e.direction == EmailDirection.OUTBOUND and e.email_type == EmailType.ORIGINAL),
            None,
        )
        inbound = next(
            (e for e in thread.emails if e.direction == EmailDirection.INBOUND),
            None,
        )

        if not outbound or not inbound:
            continue

        try:
            result = classify_reply(
                subject=outbound.subject,
                sender=outbound.sender,
                original_body=outbound.body,
                reply_sender=inbound.sender,
                reply_body=inbound.body,
            )
        except (json.JSONDecodeError, IndexError, Exception) as e:
            logger.warning(f"Classification failed for thread {thread.id}: {e}")
            errors += 1
            continue

        classification = Classification(
            thread_id=thread.id,
            category=ReplyCategory(result["category"]),
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            has_meeting_intent=result["has_meeting_intent"],
        )
        db.add(classification)
        classified += 1

    db.commit()
    return {"classified": classified, "errors": errors}


def run_sequencing(db: Session) -> dict:
    """Schedule follow-ups for threads with no reply and no pending follow-ups."""
    # Use naive UTC to match SQLite's naive datetime storage
    now = datetime.utcnow()

    threads = (
        db.query(EmailThread)
        .options(
            selectinload(EmailThread.emails),
            selectinload(EmailThread.follow_ups),
        )
        .filter(
            EmailThread.status.in_([
                ThreadStatus.AWAITING_REPLY,
                ThreadStatus.FOLLOW_UP_1,
                ThreadStatus.FOLLOW_UP_2,
            ])
        )
        .all()
    )

    scheduled = 0
    for thread in threads:
        # Check if there's already a pending/draft follow-up
        pending = [
            f for f in thread.follow_ups
            if f.status in (FollowUpStatus.SCHEDULED, FollowUpStatus.DRAFT_READY, FollowUpStatus.APPROVED)
        ]
        if pending:
            continue

        # Determine which follow-up number to schedule
        sent_followups = [f for f in thread.follow_ups if f.status == FollowUpStatus.SENT]
        next_seq = len(sent_followups) + 1

        if next_seq > 3:
            thread.status = ThreadStatus.CLOSED
            continue

        # Calculate when to send based on last outbound email
        last_outbound = max(
            (e for e in thread.emails if e.direction == EmailDirection.OUTBOUND),
            key=lambda e: e.sent_at,
            default=None,
        )
        if not last_outbound or not last_outbound.sent_at:
            continue

        delay_days = FOLLOW_UP_DELAYS.get(next_seq, 3)
        scheduled_for = last_outbound.sent_at + timedelta(days=delay_days)

        # Only schedule if the delay has passed
        if scheduled_for > now:
            continue

        follow_up = FollowUp(
            thread_id=thread.id,
            sequence_number=next_seq,
            scheduled_for=scheduled_for,
            status=FollowUpStatus.SCHEDULED,
        )
        db.add(follow_up)

        # Update thread status
        status_map = {1: ThreadStatus.FOLLOW_UP_1, 2: ThreadStatus.FOLLOW_UP_2, 3: ThreadStatus.FOLLOW_UP_3}
        thread.status = status_map.get(next_seq, ThreadStatus.FOLLOW_UP_3)

        scheduled += 1

    db.commit()
    return {"scheduled": scheduled}


def run_drafting(db: Session) -> dict:
    """Generate AI drafts for scheduled follow-ups that don't have drafts yet."""
    follow_ups = (
        db.query(FollowUp)
        .options(
            joinedload(FollowUp.thread).selectinload(EmailThread.emails),
            joinedload(FollowUp.thread).selectinload(EmailThread.follow_ups),
        )
        .filter(
            FollowUp.status == FollowUpStatus.SCHEDULED,
            FollowUp.draft_body.is_(None),
        )
        .all()
    )

    drafted = 0
    errors = 0
    for fu in follow_ups:
        thread = fu.thread
        original = next(
            (e for e in thread.emails if e.email_type == EmailType.ORIGINAL),
            None,
        )
        if not original:
            continue

        # Gather previous follow-ups for context
        prev = [
            {"sequence_number": f.sequence_number, "subject": f.draft_subject or "", "body": f.draft_body or ""}
            for f in thread.follow_ups
            if f.status == FollowUpStatus.SENT and f.draft_body
        ]

        try:
            result = draft_follow_up(
                recipient_name=thread.recipient_name or thread.recipient_email,
                recipient_email=thread.recipient_email,
                subject=original.subject,
                original_body=original.body,
                previous_followups=prev,
                sequence_number=fu.sequence_number,
            )
        except (json.JSONDecodeError, IndexError, Exception) as e:
            logger.warning(f"Drafting failed for follow-up {fu.id}: {e}")
            errors += 1
            continue

        fu.draft_subject = result["subject"]
        fu.draft_body = result["body"]
        fu.status = FollowUpStatus.DRAFT_READY
        drafted += 1

    db.commit()
    return {"drafted": drafted, "errors": errors}


def run_auto_replies(db: Session) -> dict:
    """Draft auto-replies for classified threads with actionable categories."""
    auto_reply_categories = {ReplyCategory.POSITIVE, ReplyCategory.MORE_INFO}

    threads = (
        db.query(EmailThread)
        .join(Classification)
        .options(
            selectinload(EmailThread.emails),
            selectinload(EmailThread.follow_ups),
            joinedload(EmailThread.classification),
        )
        .filter(
            Classification.category.in_(auto_reply_categories),
            EmailThread.status == ThreadStatus.REPLIED,
        )
        .all()
    )

    drafted = 0
    errors = 0
    for thread in threads:
        # Skip if we already have ANY auto-reply follow-up (including sent)
        has_auto = any(
            f for f in thread.follow_ups
            if f.sequence_number == 0
        )
        if has_auto:
            continue

        original = next((e for e in thread.emails if e.email_type == EmailType.ORIGINAL), None)
        reply = next((e for e in thread.emails if e.direction == EmailDirection.INBOUND), None)

        if not original or not reply or not thread.classification:
            continue

        try:
            result = draft_auto_reply(
                subject=original.subject,
                original_body=original.body,
                reply_body=reply.body,
                category=thread.classification.category.value,
            )
        except (json.JSONDecodeError, IndexError, Exception) as e:
            logger.warning(f"Auto-reply drafting failed for thread {thread.id}: {e}")
            errors += 1
            continue

        fu = FollowUp(
            thread_id=thread.id,
            sequence_number=0,  # 0 = auto-reply, not a follow-up sequence
            scheduled_for=datetime.now(timezone.utc),
            draft_subject=result["subject"],
            draft_body=result["body"],
            status=FollowUpStatus.DRAFT_READY,
        )
        db.add(fu)
        drafted += 1

    db.commit()
    return {"auto_replies_drafted": drafted, "errors": errors}


def pause_followups_for_replied(db: Session) -> dict:
    """Cancel any pending follow-ups for threads that have received a reply."""
    follow_ups = (
        db.query(FollowUp)
        .join(EmailThread)
        .filter(
            EmailThread.status == ThreadStatus.REPLIED,
            FollowUp.status.in_([FollowUpStatus.SCHEDULED, FollowUpStatus.DRAFT_READY]),
        )
        .all()
    )

    cancelled = 0
    for fu in follow_ups:
        fu.status = FollowUpStatus.CANCELLED
        cancelled += 1

    db.commit()
    return {"cancelled": cancelled}
