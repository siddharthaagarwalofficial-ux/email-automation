"""Tests for the template-based fallback drafter."""

import pytest

from app.services.drafter import (
    _fallback_draft_follow_up,
    _fallback_draft_auto_reply,
)


class TestFallbackFollowUpDrafter:
    """Test the template-based follow-up drafter."""

    def test_follow_up_1_returns_valid_draft(self):
        result = _fallback_draft_follow_up(
            recipient_name="Jane Creator",
            subject="Wellness collab opportunity",
            sequence_number=1,
        )
        assert "subject" in result
        assert "body" in result
        assert "Jane" in result["body"]
        assert "Wellness collab opportunity" in result["subject"]

    def test_follow_up_2_different_from_1(self):
        r1 = _fallback_draft_follow_up("Jane", "Collab", 1)
        r2 = _fallback_draft_follow_up("Jane", "Collab", 2)
        assert r1["body"] != r2["body"]
        assert r1["subject"] != r2["subject"]

    def test_follow_up_3_is_final(self):
        result = _fallback_draft_follow_up("Jane", "Collab", 3)
        assert "last" in result["body"].lower() or "last" in result["subject"].lower()

    def test_fallback_sequence_out_of_range(self):
        """Sequence > 3 should fall back to template 1."""
        result = _fallback_draft_follow_up("Jane", "Test", 5)
        assert "subject" in result
        assert "body" in result
        assert len(result["body"]) > 10

    def test_no_name_uses_there(self):
        """Empty name should use 'there' as fallback."""
        result = _fallback_draft_follow_up("", "Test Subject", 1)
        assert "there" in result["body"]

    def test_first_name_extraction(self):
        """Should use only the first name from a full name."""
        result = _fallback_draft_follow_up("Jane Michelle Creator", "Test", 1)
        assert "Jane" in result["body"]
        assert "Michelle" not in result["body"]

    def test_subject_contains_original(self):
        """Follow-up subject should reference the original subject."""
        result = _fallback_draft_follow_up("Jane", "Amazing Product Collab", 2)
        assert "Amazing Product Collab" in result["subject"]


class TestFallbackAutoReplyDrafter:
    """Test the template-based auto-reply drafter."""

    def test_positive_auto_reply(self):
        result = _fallback_draft_auto_reply(
            recipient_name="Alex Partner",
            subject="Partnership Opportunity",
            category="positive",
        )
        assert "subject" in result
        assert "body" in result
        assert "Alex" in result["body"]

    def test_more_info_auto_reply(self):
        result = _fallback_draft_auto_reply(
            recipient_name="Sam Reviewer",
            subject="Collab Details",
            category="more_info",
        )
        assert "subject" in result
        assert "body" in result
        assert "Sam" in result["body"]

    def test_unknown_category_falls_back(self):
        """Unknown category should use the more_info template."""
        result = _fallback_draft_auto_reply("Test", "Test", "unknown_cat")
        assert "subject" in result
        assert "body" in result
        assert len(result["body"]) > 10

    def test_positive_mentions_call(self):
        """Positive auto-reply should suggest a call or meeting."""
        result = _fallback_draft_auto_reply("Jane", "Collab", "positive")
        body_lower = result["body"].lower()
        assert "call" in body_lower or "chat" in body_lower

    def test_more_info_contains_details(self):
        """More info reply should include partnership details."""
        result = _fallback_draft_auto_reply("Jane", "Collab", "more_info")
        body_lower = result["body"].lower()
        assert "product" in body_lower or "compensation" in body_lower or "content" in body_lower
