import json
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

DRAFT_PROMPT = """You are a professional email copywriter for Root Labs, a wellness/health company (part of Mosaic Wellness). You write follow-up emails for outbound outreach to creators, influencers, and potential partners.

Write a follow-up email that:
1. References the original email naturally (don't just say "following up on my last email")
2. Varies the angle based on the follow-up number
3. Sounds like a real human, not a template
4. Is concise (3-5 short paragraphs max)
5. Has a clear, low-friction CTA

FOLLOW-UP STRATEGY BY SEQUENCE:
- Follow-up #1 (3 days): Add new value — share a relevant insight, social proof, or specific benefit they'd get
- Follow-up #2 (7 days): Change the angle — try a different hook, ask a question, or offer something concrete (samples, data, case study)
- Follow-up #3 (14 days): Final attempt — be direct, acknowledge the silence, make it easy to say yes or no

CONTEXT:
Recipient: {recipient_name} ({recipient_email})
Original Subject: {subject}
Original Email:
{original_body}

{previous_followups}

This is follow-up #{sequence_number}.

Respond with ONLY valid JSON:
{{"subject": "<follow-up subject line>", "body": "<the full email body>"}}"""

AUTO_REPLY_PROMPT = """You are a professional email copywriter for Root Labs. A contact has replied to our outreach email. Draft an appropriate response based on their reply.

GUIDELINES:
- Be warm, professional, and concise
- If they asked for more info, provide relevant details about the collaboration
- If they want to schedule a meeting, propose specific times
- If they have product questions, offer to connect them with the product team
- Keep it to 2-3 short paragraphs

ORIGINAL OUTREACH:
Subject: {subject}
Body:
{original_body}

THEIR REPLY:
{reply_body}

REPLY CLASSIFICATION: {category}

Respond with ONLY valid JSON:
{{"subject": "<reply subject line>", "body": "<the full email body>"}}"""


client = None


def _get_client() -> anthropic.Anthropic:
    global client
    if client is None:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return client


# ---------------------------------------------------------------------------
# Template-based fallback drafters (used when Claude API is unavailable)
# ---------------------------------------------------------------------------

_FOLLOW_UP_TEMPLATES = {
    1: {
        "subject": "Re: {subject} — quick thought",
        "body": (
            "Hi {first_name},\n\n"
            "I wanted to circle back on my earlier note. I know your inbox "
            "is probably busy, so I'll keep this short.\n\n"
            "Since I last reached out, we've partnered with several creators "
            "in the wellness space who've seen great engagement with our products. "
            "I think there's a genuine fit here.\n\n"
            "Would you be open to a quick 15-minute chat this week? Happy to "
            "work around your schedule.\n\n"
            "Best,\nTeam Root Labs"
        ),
    },
    2: {
        "subject": "Re: {subject} — different angle",
        "body": (
            "Hi {first_name},\n\n"
            "I realize my earlier emails might not have landed at the right time. "
            "Let me try a different approach.\n\n"
            "We'd love to send you a sample kit — no strings attached. Many of "
            "our creator partners tell us the products speak for themselves. "
            "If it resonates with your audience, we can talk next steps.\n\n"
            "Interested? Just reply with your mailing address and we'll ship "
            "it out this week.\n\n"
            "Cheers,\nTeam Root Labs"
        ),
    },
    3: {
        "subject": "Re: {subject} — last note from me",
        "body": (
            "Hi {first_name},\n\n"
            "I don't want to clutter your inbox, so this will be my last "
            "follow-up on this thread.\n\n"
            "If the timing isn't right or this isn't a fit, no worries at all — "
            "I completely understand. But if you're even slightly curious, "
            "I'd love a quick reply (even a one-liner is fine!).\n\n"
            "Either way, thanks for your time and keep up the great content.\n\n"
            "All the best,\nTeam Root Labs"
        ),
    },
}

_AUTO_REPLY_TEMPLATES = {
    "positive": {
        "subject": "Re: {subject} — great to hear!",
        "body": (
            "Hi {first_name},\n\n"
            "That's wonderful to hear! We're excited about the possibility "
            "of working together.\n\n"
            "I'd love to set up a quick call to discuss the details — our "
            "creator partnerships typically include product seeding, content "
            "collaboration, and competitive compensation.\n\n"
            "Would any time this week work for a 20-minute chat? Happy to "
            "send a calendar invite whenever works best.\n\n"
            "Looking forward to it!\nTeam Root Labs"
        ),
    },
    "more_info": {
        "subject": "Re: {subject} — more details inside",
        "body": (
            "Hi {first_name},\n\n"
            "Great question! Here's a quick overview of how our creator "
            "partnerships work:\n\n"
            "• Product seeding: We send our full range for you to try\n"
            "• Content: 1-2 posts/stories per month featuring the products\n"
            "• Compensation: Competitive flat fee + affiliate revenue share\n"
            "• Timeline: Typically a 3-month initial collaboration\n\n"
            "Happy to jump on a call to discuss the specifics and answer "
            "any other questions. Would next week work?\n\n"
            "Best,\nTeam Root Labs"
        ),
    },
}


def _fallback_draft_follow_up(
    recipient_name: str, subject: str, sequence_number: int,
) -> dict:
    """Template-based follow-up when LLM is unavailable."""
    template = _FOLLOW_UP_TEMPLATES.get(sequence_number, _FOLLOW_UP_TEMPLATES[1])
    first_name = recipient_name.split()[0] if recipient_name else "there"
    return {
        "subject": template["subject"].format(subject=subject),
        "body": template["body"].format(first_name=first_name),
    }


def _fallback_draft_auto_reply(
    recipient_name: str, subject: str, category: str,
) -> dict:
    """Template-based auto-reply when LLM is unavailable."""
    template = _AUTO_REPLY_TEMPLATES.get(category, _AUTO_REPLY_TEMPLATES["more_info"])
    first_name = recipient_name.split()[0] if recipient_name else "there"
    return {
        "subject": template["subject"].format(subject=subject),
        "body": template["body"].format(first_name=first_name),
    }


def draft_follow_up(
    recipient_name: str,
    recipient_email: str,
    subject: str,
    original_body: str,
    previous_followups: list[dict],
    sequence_number: int,
) -> dict:
    """Draft a follow-up email using Claude, with template fallback."""

    try:
        prev_text = ""
        if previous_followups:
            prev_text = "PREVIOUS FOLLOW-UPS SENT:\n"
            for fu in previous_followups:
                prev_text += f"\nFollow-up #{fu['sequence_number']}:\nSubject: {fu['subject']}\nBody:\n{fu['body']}\n"

        prompt = DRAFT_PROMPT.format(
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            subject=subject,
            original_body=original_body,
            previous_followups=prev_text,
            sequence_number=sequence_number,
        )

        response = _get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        return {"subject": result.get("subject", f"Re: {subject}"), "body": result.get("body", "")}

    except Exception as e:
        logger.warning(f"LLM drafting failed, using template fallback: {e}")
        return _fallback_draft_follow_up(recipient_name, subject, sequence_number)


def draft_auto_reply(
    subject: str,
    original_body: str,
    reply_body: str,
    category: str,
    recipient_name: str = "",
) -> dict:
    """Draft an auto-reply using Claude, with template fallback."""

    try:
        prompt = AUTO_REPLY_PROMPT.format(
            subject=subject,
            original_body=original_body,
            reply_body=reply_body,
            category=category,
        )

        response = _get_client().messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        return {"subject": result.get("subject", f"Re: {subject}"), "body": result.get("body", "")}

    except Exception as e:
        logger.warning(f"LLM auto-reply failed, using template fallback: {e}")
        return _fallback_draft_auto_reply(recipient_name, subject, category)
