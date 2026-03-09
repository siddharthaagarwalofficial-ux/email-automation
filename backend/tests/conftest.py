"""Shared fixtures for the test suite."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    EmailThread, Email, Classification, FollowUp,
    ThreadStatus, EmailDirection, EmailType, ReplyCategory, FollowUpStatus,
)
from datetime import datetime, timedelta


@pytest.fixture
def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_thread(db):
    """Create a basic outbound thread with an original email."""
    thread = EmailThread(
        recipient_email="creator@example.com",
        recipient_name="Jane Creator",
        subject="Wellness collab opportunity",
        status=ThreadStatus.AWAITING_REPLY,
        created_at=datetime.utcnow() - timedelta(days=10),
        updated_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(thread)
    db.flush()

    email = Email(
        thread_id=thread.id,
        direction=EmailDirection.OUTBOUND,
        email_type=EmailType.ORIGINAL,
        sender="outreach@rootlabs.in",
        recipient="creator@example.com",
        subject="Wellness collab opportunity",
        body="Hi Jane, we love your content and would love to explore a partnership...",
        sent_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(email)
    db.commit()
    db.refresh(thread)
    return thread


@pytest.fixture
def replied_thread(db, sample_thread):
    """Create a thread that has received a reply."""
    sample_thread.status = ThreadStatus.REPLIED

    reply = Email(
        thread_id=sample_thread.id,
        direction=EmailDirection.INBOUND,
        email_type=EmailType.REPLY,
        sender="creator@example.com",
        recipient="outreach@rootlabs.in",
        subject="Re: Wellness collab opportunity",
        body="Hi! This sounds great, I'd love to learn more. Can we schedule a call next week?",
        sent_at=datetime.utcnow() - timedelta(days=8),
    )
    db.add(reply)
    db.commit()
    db.refresh(sample_thread)
    return sample_thread
