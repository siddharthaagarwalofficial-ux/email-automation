import json
import anthropic

from app.config import settings

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


def classify_reply(
    subject: str,
    sender: str,
    original_body: str,
    reply_sender: str,
    reply_body: str,
) -> dict:
    """Classify an email reply using Claude. Returns dict with category, confidence, reasoning, has_meeting_intent."""

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
