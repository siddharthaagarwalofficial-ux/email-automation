"""Tests for the keyword-based fallback classifier."""

import pytest

from app.services.classifier import _fallback_classify, classify_reply


class TestFallbackClassifier:
    """Test the regex-based fallback classifier for all 6 categories."""

    def test_positive_interested(self):
        result = _fallback_classify("That sounds great! I'd love to collaborate.")
        assert result["category"] == "positive"
        assert result["confidence"] > 0.5
        assert result["has_meeting_intent"] is False

    def test_positive_looking_forward(self):
        result = _fallback_classify("Looking forward to working together!")
        assert result["category"] == "positive"

    def test_positive_count_me_in(self):
        result = _fallback_classify("Count me in, this sounds exciting!")
        assert result["category"] == "positive"

    def test_negative_not_interested(self):
        result = _fallback_classify("Thanks but I'm not interested at this time.")
        assert result["category"] == "negative"
        assert result["confidence"] >= 0.7

    def test_negative_decline(self):
        result = _fallback_classify("I'll have to respectfully decline this offer.")
        assert result["category"] == "negative"

    def test_negative_pass(self):
        result = _fallback_classify("I'll pass on this one, thanks.")
        assert result["category"] == "negative"

    def test_out_of_office_auto_reply(self):
        result = _fallback_classify(
            "I'm currently out of the office and will return on Jan 15th. "
            "I will have limited access to email."
        )
        assert result["category"] == "out_of_office"
        assert result["confidence"] >= 0.8

    def test_out_of_office_vacation(self):
        result = _fallback_classify("On vacation until next Monday. Will reply when I'm back.")
        assert result["category"] == "out_of_office"

    def test_wrong_person(self):
        result = _fallback_classify(
            "I think you have the wrong person. You might want to reach out to the marketing team."
        )
        assert result["category"] == "wrong_person"

    def test_wrong_person_no_longer_at(self):
        result = _fallback_classify("I'm no longer at this company. Try reaching someone else.")
        assert result["category"] == "wrong_person"

    def test_unsubscribe(self):
        result = _fallback_classify("Please unsubscribe me from this mailing list.")
        assert result["category"] == "unsubscribe"
        assert result["confidence"] >= 0.85

    def test_unsubscribe_stop_emailing(self):
        result = _fallback_classify("Stop emailing me please.")
        assert result["category"] == "unsubscribe"

    def test_more_info_tell_me_more(self):
        result = _fallback_classify("Can you tell me more about the compensation structure?")
        assert result["category"] == "more_info"

    def test_more_info_pricing(self):
        result = _fallback_classify("What's the pricing like? Can you share more details?")
        assert result["category"] == "more_info"

    def test_more_info_default(self):
        """Ambiguous reply defaults to more_info with low confidence."""
        result = _fallback_classify("OK sure, let me think about it.")
        assert result["category"] == "more_info"
        assert result["confidence"] <= 0.6

    def test_meeting_intent_detected(self):
        result = _fallback_classify("Sounds great! Let's schedule a call next week.")
        assert result["category"] == "positive"
        assert result["has_meeting_intent"] is True

    def test_meeting_intent_zoom(self):
        result = _fallback_classify("Can we hop on a Zoom call to discuss?")
        assert result["has_meeting_intent"] is True

    def test_no_meeting_intent(self):
        result = _fallback_classify("Not interested, thanks.")
        assert result["has_meeting_intent"] is False

    def test_result_shape(self):
        """Verify the result dict has all required keys."""
        result = _fallback_classify("Hello")
        assert "category" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "has_meeting_intent" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_priority_ooo_over_positive(self):
        """OOO keywords should take priority over positive keywords."""
        result = _fallback_classify(
            "I'd love to collaborate but I'm currently out of the office."
        )
        assert result["category"] == "out_of_office"

    def test_priority_unsubscribe_over_negative(self):
        """Unsubscribe takes priority over generic negative."""
        result = _fallback_classify(
            "Not interested. Please stop emailing me and unsubscribe me."
        )
        assert result["category"] == "unsubscribe"
