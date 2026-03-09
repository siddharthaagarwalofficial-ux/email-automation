from sqlalchemy.orm import Session

from app.connectors.base import EmailConnector, RawThread
from app.models import (
    EmailThread, Email, EmailDirection, EmailType, ThreadStatus,
)


async def sync_threads(connector: EmailConnector, db: Session) -> dict:
    """Pull threads from the email connector and upsert into the database."""
    raw_threads = await connector.get_threads()
    created = 0
    updated = 0

    for raw in raw_threads:
        existing = db.query(EmailThread).filter(
            EmailThread.gmail_thread_id == raw.thread_id
        ).first()

        if existing:
            updated += _update_thread(existing, raw, db)
        else:
            _create_thread(raw, db)
            created += 1

    db.commit()
    return {"created": created, "updated": updated}


def _create_thread(raw: RawThread, db: Session) -> EmailThread:
    outbound = raw.messages[0]

    # Determine initial status based on whether there's a reply
    has_reply = any(m.sender != outbound.sender for m in raw.messages)

    thread = EmailThread(
        gmail_thread_id=raw.thread_id,
        recipient_email=outbound.recipient,
        recipient_name=_extract_name(outbound.recipient),
        subject=raw.subject,
        status=ThreadStatus.REPLIED if has_reply else ThreadStatus.AWAITING_REPLY,
    )
    db.add(thread)
    db.flush()

    for msg in raw.messages:
        is_outbound = msg.sender == outbound.sender
        email = Email(
            thread_id=thread.id,
            gmail_message_id=msg.message_id,
            direction=EmailDirection.OUTBOUND if is_outbound else EmailDirection.INBOUND,
            email_type=_infer_email_type(msg, raw.messages, is_outbound),
            sender=msg.sender,
            recipient=msg.recipient,
            subject=msg.subject,
            body=msg.body,
            sent_at=msg.date,
        )
        db.add(email)

    return thread


def _update_thread(thread: EmailThread, raw: RawThread, db: Session) -> int:
    existing_msg_ids = {
        e.gmail_message_id for e in thread.emails if e.gmail_message_id
    }

    new_messages = [m for m in raw.messages if m.message_id not in existing_msg_ids]
    if not new_messages:
        return 0

    outbound_sender = raw.messages[0].sender

    for msg in new_messages:
        is_outbound = msg.sender == outbound_sender
        email = Email(
            thread_id=thread.id,
            gmail_message_id=msg.message_id,
            direction=EmailDirection.OUTBOUND if is_outbound else EmailDirection.INBOUND,
            email_type=_infer_email_type(msg, raw.messages, is_outbound),
            sender=msg.sender,
            recipient=msg.recipient,
            subject=msg.subject,
            body=msg.body,
            sent_at=msg.date,
        )
        db.add(email)

        if not is_outbound and thread.status != ThreadStatus.REPLIED:
            thread.status = ThreadStatus.REPLIED

    return 1


def _infer_email_type(msg, all_messages, is_outbound) -> EmailType:
    if not is_outbound:
        return EmailType.REPLY

    outbound_messages = [m for m in all_messages if m.sender == all_messages[0].sender]
    idx = next((i for i, m in enumerate(outbound_messages) if m.message_id == msg.message_id), 0)

    if idx == 0:
        return EmailType.ORIGINAL
    elif idx == 1:
        return EmailType.FOLLOW_UP_1
    elif idx == 2:
        return EmailType.FOLLOW_UP_2
    else:
        return EmailType.FOLLOW_UP_3


def _extract_name(email_addr: str) -> str:
    """Extract a display name from an email address or 'Name <email>' format."""
    # Handle "Display Name <email@domain.com>" format
    if "<" in email_addr and ">" in email_addr:
        name_part = email_addr.split("<")[0].strip().strip('"').strip("'")
        if name_part:
            return name_part

    # Fall back to parsing the local part of the email
    addr = email_addr.strip().rstrip(">").split("<")[-1] if "<" in email_addr else email_addr
    local = addr.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").replace("-", " ").split()
    return " ".join(p.capitalize() for p in parts)
