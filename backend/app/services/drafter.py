import json
import anthropic

from app.config import settings

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


def draft_follow_up(
    recipient_name: str,
    recipient_email: str,
    subject: str,
    original_body: str,
    previous_followups: list[dict],
    sequence_number: int,
) -> dict:
    """Draft a follow-up email using Claude. Returns dict with subject and body."""

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


def draft_auto_reply(
    subject: str,
    original_body: str,
    reply_body: str,
    category: str,
) -> dict:
    """Draft an auto-reply to a received email. Returns dict with subject and body."""

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
