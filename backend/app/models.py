import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, Float, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


class ThreadStatus(str, enum.Enum):
    SENT = "sent"
    AWAITING_REPLY = "awaiting_reply"
    REPLIED = "replied"
    FOLLOW_UP_1 = "follow_up_1"
    FOLLOW_UP_2 = "follow_up_2"
    FOLLOW_UP_3 = "follow_up_3"
    CLOSED = "closed"
    PAUSED = "paused"


class ReplyCategory(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MORE_INFO = "more_info"
    OUT_OF_OFFICE = "out_of_office"
    WRONG_PERSON = "wrong_person"
    UNSUBSCRIBE = "unsubscribe"


class EmailDirection(str, enum.Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class EmailType(str, enum.Enum):
    ORIGINAL = "original"
    FOLLOW_UP_1 = "follow_up_1"
    FOLLOW_UP_2 = "follow_up_2"
    FOLLOW_UP_3 = "follow_up_3"
    REPLY = "reply"
    AUTO_REPLY = "auto_reply"


class FollowUpStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    DRAFT_READY = "draft_ready"
    APPROVED = "approved"
    SENT = "sent"
    CANCELLED = "cancelled"


def utcnow():
    return datetime.now(timezone.utc)


class EmailThread(Base):
    __tablename__ = "email_threads"

    id = Column(Integer, primary_key=True, index=True)
    gmail_thread_id = Column(String, unique=True, nullable=True, index=True)
    recipient_email = Column(String, nullable=False, index=True)
    recipient_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    status = Column(Enum(ThreadStatus), default=ThreadStatus.SENT, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    emails = relationship("Email", back_populates="thread", order_by="Email.sent_at")
    classification = relationship("Classification", back_populates="thread", uselist=False)
    follow_ups = relationship("FollowUp", back_populates="thread", order_by="FollowUp.sequence_number")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=False)
    gmail_message_id = Column(String, unique=True, nullable=True)
    direction = Column(Enum(EmailDirection), nullable=False)
    email_type = Column(Enum(EmailType), nullable=False)
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=utcnow)

    thread = relationship("EmailThread", back_populates="emails")


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), unique=True, nullable=False)
    category = Column(Enum(ReplyCategory), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    has_meeting_intent = Column(Boolean, default=False)
    classified_at = Column(DateTime, default=utcnow)

    thread = relationship("EmailThread", back_populates="classification")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)  # 1, 2, or 3
    scheduled_for = Column(DateTime, nullable=False)
    draft_subject = Column(String, nullable=True)
    draft_body = Column(Text, nullable=True)
    status = Column(Enum(FollowUpStatus), default=FollowUpStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    sent_at = Column(DateTime, nullable=True)

    thread = relationship("EmailThread", back_populates="follow_ups")
