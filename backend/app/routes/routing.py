from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmailThread, Classification, EmailDirection, ReplyCategory

router = APIRouter(prefix="/api/routing", tags=["routing"])

# Default routing rules — configurable
ROUTING_RULES: dict[str, dict] = {
    "positive": {"assignee": "partnerships@rootlabs.in", "label": "Partnerships Team"},
    "negative": {"assignee": "outreach@rootlabs.in", "label": "Outreach Team"},
    "more_info": {"assignee": "product@rootlabs.in", "label": "Product Team"},
    "out_of_office": {"assignee": "outreach@rootlabs.in", "label": "Outreach Team"},
    "wrong_person": {"assignee": "outreach@rootlabs.in", "label": "Outreach Team"},
    "unsubscribe": {"assignee": "compliance@rootlabs.in", "label": "Compliance Team"},
}


class RoutingRule(BaseModel):
    category: str
    assignee: str
    label: str


@router.get("/rules", response_model=list[RoutingRule])
def get_routing_rules():
    """Get current routing rules."""
    return [
        RoutingRule(category=cat, assignee=rule["assignee"], label=rule["label"])
        for cat, rule in ROUTING_RULES.items()
    ]


@router.put("/rules/{category}")
def update_routing_rule(category: str, rule: RoutingRule):
    """Update a routing rule."""
    ROUTING_RULES[category] = {"assignee": rule.assignee, "label": rule.label}
    return {"status": "updated", "category": category}


@router.get("/assignments")
def get_assignments(db: Session = Depends(get_db)):
    """Get all classified threads with their routing assignments."""
    classifications = db.query(Classification).all()

    assignments = []
    for c in classifications:
        thread = c.thread
        rule = ROUTING_RULES.get(c.category.value, ROUTING_RULES["more_info"])

        reply = next((e for e in thread.emails if e.direction == EmailDirection.INBOUND), None)

        assignments.append({
            "thread_id": thread.id,
            "recipient": thread.recipient_name or thread.recipient_email,
            "recipient_email": thread.recipient_email,
            "subject": thread.subject,
            "category": c.category.value,
            "assigned_to": rule["assignee"],
            "team": rule["label"],
            "reply_snippet": reply.body[:150] + "..." if reply and len(reply.body) > 150 else (reply.body if reply else ""),
            "has_meeting_intent": c.has_meeting_intent,
        })

    return assignments
