import json
import logging
import re

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an email reply classifier for a B2B outreach team. You will be given an original outbound email and a reply to it. Classify the reply into exactly one category.

CATEGORIES:
- positive: The person is interested, wants to collaborate, or is open to next steps
- negative: The person is declining, not interested, or explicitly saying no
- more_info: The person is asking for more details before making a decision
- out_of_office: Auto-reply or manual message indicating they are away/unavailable
- wrong_person: The reply indicates the email was sent to the wrong person
- unsubscribe: The person wants to be removed from the mailing list or stop receiving emails

Also determine:
- has_meeting_intent: true if the reply explicitly mentions scheduling a call, meeting, or specific time slots

ORIGINAL EMAIL:
Subject: {subject}
From: {sender}
Body:
{original_body}

REPLY:
From: {reply_sender}
Body:
{reply_body}

Respond with ONLY valid JSON in this exact format:
{{"category": "<one of: positive, negative, more_info, out_of_office, wrong_person, unsubscribe>", "confidence": <float 0.0-1.0>, "reasoning": "<one sentence explaining why>", "has_meeting_intent": <true or false>}}"""


client = None


def _get_client() -> anthropic.Anthropic:
    global client
    if client is None:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return client


# ---------------------------------------------------------------------------
# Keyword-based fallback classifier (used when Claude API is unavailable)
# ---------------------------------------------------------------------------

_POSITIVE_KW = re.compile(
    r"\b(interested|love to|sounds great|let'?s do|excited|count me in|happy to|"
    r"looking forward|open to|would love|definitely|sign me up|let'?s talk|"
    r"collaboration sounds|partner up|on board)\b",
    re.IGNORECASE,
)
_NEGATIVE_KW = re.compile(
    r"\b(not interested|no thanks|decline|pass on|can'?t take|don'?t think|"
    r"not a good fit|non-compete|not right now|won'?t be able|respectfully decline|"
    r"not for us|politely decline)\b",
    re.IGNORECASE,
)
_OOO_KW = re.compile(
    r"\b(out of office|on leave|auto-?reply|currently away|limited access|"
    r"returning on|back on|vacation|out of the office|away from)\b",
    re.IGNORECASE,
)
_WRONG_KW = re.compile(
    r"\b(wrong person|not the right person|not my department|"
    r"someone else|redirect|forward this to|not me|no longer at)\b",
    re.IGNORECASE,
)
_UNSUB_KW = re.compile(
    r"\b(unsubscribe|stop emailing|remove me|take me off|opt out|"
    r"don'?t email|no more emails|stop sending)\b",
    re.IGNORECASE,
)
_INFO_KW = re.compile(
    r"\b(more details|more info|what exactly|can you share|"
    r"tell me more|pricing|how does|what kind|specifics|"
    r"what would|could you explain|details on)\b",
    re.IGNORECASE,
)
_MEETING_KW = re.compile(
    r"\b(schedule|call|meeting|calendar|availability|slot|"
    r"zoom|google meet|next week|this week|let'?s chat|"
    r"free on|available on|set up a|book a|hop on)\b",
    re.IGNORECASE,
)


def _fallback_classify(reply_body: str) -> dict:
    """Rule-based fallback when LLM is unavailable."""
    body = reply_body.lower()

    # Check in priority order
    if _OOO_KW.search(body):
        cat, conf, reason = "out_of_office", 0.85, "Auto-detected out-of-office keywords"
    elif _UNSUB_KW.search(body):
        cat, conf, reason = "unsubscribe", 0.90, "Unsubscribe intent detected via keywords"
    elif _WRONG_KW.search(body):
        cat, conf, reason = "wrong_person", 0.80, "Wrong-person indicators found in reply"
    elif _NEGATIVE_KW.search(body):
        cat, conf, reason = "negative", 0.80, "Negative/declining language detected"
    elif _POSITIVE_KW.search(body):
        cat, conf, reason = "positive", 0.75, "Positive/interested language detected"
    elif _INFO_KW.search(body):
        cat, conf, reason = "more_info", 0.70, "Information-seeking language detected"
    else:
        cat, conf, reason = "more_info", 0.50, "No strong signals; defaulting to more_info"

    meeting = bool(_MEETING_KW.search(body))

    return {
        "category": cat,
        "confidence": conf,
        "reasoning": f"[Fallback classifier] {reason}",
        "has_meeting_intent": meeting,
    }


def classify_reply(
    subject: str,
    sender: str,
    original_body: str,
    reply_sender: str,
    reply_body: str,
) -> dict:
    """Classify an email reply using Claude, with keyword-based fallback."""

    # Try the LLM first
    try:
        prompt = CLASSIFICATION_PROMPT.format(
            subject=subject,
            sender=sender,
            original_body=original_body,
            reply_sender=reply_sender,
            reply_body=reply_body,
        )

        response = _get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Parse JSON from response, handling potential markdown wrapping
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)

        # Validate
        valid_categories = {"positive", "negative", "more_info", "out_of_office", "wrong_person", "unsubscribe"}
        if result.get("category") not in valid_categories:
            result["category"] = "more_info"
            result["confidence"] = 0.5

        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.8))))
        result["has_meeting_intent"] = bool(result.get("has_meeting_intent", False))
        result.setdefault("reasoning", "")

        return result

    except Exception as e:
        logger.warning(f"LLM classification failed, using fallback: {e}")
        return _fallback_classify(reply_body)
