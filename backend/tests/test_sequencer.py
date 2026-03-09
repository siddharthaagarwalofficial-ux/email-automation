"""Tests for the sequencing engine."""

import pytest
from datetime import datetime, timedelta

from app.models import (
    EmailThread, Email, Classification, FollowUp,
    ThreadStatus, EmailDirection, EmailType, ReplyCategory, FollowUpStatus,
)
from app.services.sequencer import (
    run_classification,
    run_sequencing,
    run_drafting,
    run_auto_replies,
    pause_followups_for_replied,
)


class TestRunClassification:
    """Test the classification step of the pipeline."""

    def test_classifies_replied_threads(self, replied_thread, db):
        result = run_classification(db)
        assert result["classified"] >= 1

        # Verify classification was created
        classification = db.query(Classification).filter_by(thread_id=replied_thread.id).first()
        assert classification is not None
        assert classification.category is not None
        assert 0.0 <= classification.confidence <= 1.0

    def test_skips_already_classified(self, replied_thread, db):
        """Threads with existing classifications should be skipped."""
        # First run classifies
        run_classification(db)
        # Second run should find nothing new
        result = run_classification(db)
        assert result["classified"] == 0

    def test_skips_non_replied_threads(self, sample_thread, db):
        """Threads in AWAITING_REPLY status should not be classified."""
        result = run_classification(db)
        assert result["classified"] == 0


class TestRunSequencing:
    """Test the follow-up scheduling logic."""

    def test_schedules_first_follow_up(self, sample_thread, db):
        result = run_sequencing(db)
        assert result["scheduled"] >= 1

        follow_ups = db.query(FollowUp).filter_by(thread_id=sample_thread.id).all()
        assert len(follow_ups) == 1
        assert follow_ups[0].sequence_number == 1
        assert follow_ups[0].status == FollowUpStatus.SCHEDULED

    def test_does_not_double_schedule(self, sample_thread, db):
        """Should not schedule if there's already a pending follow-up."""
        run_sequencing(db)
        result = run_sequencing(db)
        assert result["scheduled"] == 0

    def test_skips_threads_too_recent(self, db):
        """Thread with recent outbound email should not trigger follow-up yet."""
        thread = EmailThread(
            recipient_email="new@example.com",
            subject="Fresh outreach",
            status=ThreadStatus.AWAITING_REPLY,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(thread)
        db.flush()

        email = Email(
            thread_id=thread.id,
            direction=EmailDirection.OUTBOUND,
            email_type=EmailType.ORIGINAL,
            sender="us@rootlabs.in",
            recipient="new@example.com",
            subject="Fresh outreach",
            body="Hi there!",
            sent_at=datetime.utcnow(),  # Just sent now
        )
        db.add(email)
        db.commit()

        result = run_sequencing(db)
        assert result["scheduled"] == 0

    def test_updates_thread_status(self, sample_thread, db):
        run_sequencing(db)
        db.refresh(sample_thread)
        assert sample_thread.status == ThreadStatus.FOLLOW_UP_1

    def test_closes_after_three_followups(self, sample_thread, db):
        """Thread should be closed after 3 sent follow-ups."""
        for seq in range(1, 4):
            fu = FollowUp(
                thread_id=sample_thread.id,
                sequence_number=seq,
                scheduled_for=datetime.utcnow() - timedelta(days=1),
                status=FollowUpStatus.SENT,
            )
            db.add(fu)
        db.commit()

        run_sequencing(db)
        db.refresh(sample_thread)
        assert sample_thread.status == ThreadStatus.CLOSED


class TestRunDrafting:
    """Test the AI drafting step."""

    def test_drafts_scheduled_follow_ups(self, sample_thread, db):
        # First schedule a follow-up
        run_sequencing(db)

        # Now draft it
        result = run_drafting(db)
        assert result["drafted"] >= 1

        fu = db.query(FollowUp).filter_by(thread_id=sample_thread.id).first()
        assert fu.status == FollowUpStatus.DRAFT_READY
        assert fu.draft_subject is not None
        assert fu.draft_body is not None
        assert len(fu.draft_body) > 10

    def test_skips_already_drafted(self, sample_thread, db):
        run_sequencing(db)
        run_drafting(db)
        # Second run should find nothing new
        result = run_drafting(db)
        assert result["drafted"] == 0


class TestRunAutoReplies:
    """Test auto-reply drafting for classified threads."""

    def test_drafts_auto_reply_for_positive(self, replied_thread, db):
        # Classify the thread
        classification = Classification(
            thread_id=replied_thread.id,
            category=ReplyCategory.POSITIVE,
            confidence=0.9,
            reasoning="Test positive",
            has_meeting_intent=True,
        )
        db.add(classification)
        db.commit()

        result = run_auto_replies(db)
        assert result["auto_replies_drafted"] >= 1

        fu = db.query(FollowUp).filter_by(
            thread_id=replied_thread.id, sequence_number=0
        ).first()
        assert fu is not None
        assert fu.status == FollowUpStatus.DRAFT_READY
        assert fu.draft_body is not None

    def test_skips_negative_replies(self, replied_thread, db):
        classification = Classification(
            thread_id=replied_thread.id,
            category=ReplyCategory.NEGATIVE,
            confidence=0.9,
            reasoning="Test negative",
            has_meeting_intent=False,
        )
        db.add(classification)
        db.commit()

        result = run_auto_replies(db)
        assert result["auto_replies_drafted"] == 0

    def test_skips_if_auto_reply_exists(self, replied_thread, db):
        """Should not create duplicate auto-replies."""
        classification = Classification(
            thread_id=replied_thread.id,
            category=ReplyCategory.POSITIVE,
            confidence=0.9,
            reasoning="Test",
            has_meeting_intent=False,
        )
        db.add(classification)
        db.commit()

        run_auto_replies(db)
        result = run_auto_replies(db)
        assert result["auto_replies_drafted"] == 0


class TestPauseFollowupsForReplied:
    """Test cancellation of follow-ups when a reply is received."""

    def test_cancels_pending_followups(self, sample_thread, db):
        # Create a follow-up
        fu = FollowUp(
            thread_id=sample_thread.id,
            sequence_number=1,
            scheduled_for=datetime.utcnow(),
            status=FollowUpStatus.SCHEDULED,
        )
        db.add(fu)
        # Mark thread as replied
        sample_thread.status = ThreadStatus.REPLIED
        db.commit()

        result = pause_followups_for_replied(db)
        assert result["cancelled"] >= 1

        db.refresh(fu)
        assert fu.status == FollowUpStatus.CANCELLED

    def test_leaves_sent_followups_alone(self, sample_thread, db):
        """Already-sent follow-ups should not be cancelled."""
        fu = FollowUp(
            thread_id=sample_thread.id,
            sequence_number=1,
            scheduled_for=datetime.utcnow(),
            status=FollowUpStatus.SENT,
            sent_at=datetime.utcnow(),
        )
        db.add(fu)
        sample_thread.status = ThreadStatus.REPLIED
        db.commit()

        result = pause_followups_for_replied(db)
        assert result["cancelled"] == 0
