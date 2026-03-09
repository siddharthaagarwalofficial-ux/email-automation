from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.sequencer import (
    run_classification,
    run_sequencing,
    run_drafting,
    run_auto_replies,
    pause_followups_for_replied,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/run")
def run_pipeline(db: Session = Depends(get_db)):
    """Run the full AI pipeline: classify replies → pause follow-ups → schedule new follow-ups → draft emails → auto-reply drafts."""

    # Step 1: Classify any unclassified replies
    classification_result = run_classification(db)

    # Step 2: Cancel follow-ups for threads that got replies
    pause_result = pause_followups_for_replied(db)

    # Step 3: Schedule follow-ups for no-reply threads
    sequencing_result = run_sequencing(db)

    # Step 4: Generate AI drafts for scheduled follow-ups
    drafting_result = run_drafting(db)

    # Step 5: Draft auto-replies for positive/more_info replies
    auto_reply_result = run_auto_replies(db)

    return {
        "classification": classification_result,
        "paused": pause_result,
        "sequencing": sequencing_result,
        "drafting": drafting_result,
        "auto_replies": auto_reply_result,
    }


@router.post("/classify")
def run_classify_only(db: Session = Depends(get_db)):
    """Run just the classification step."""
    return run_classification(db)


@router.post("/sequence")
def run_sequence_only(db: Session = Depends(get_db)):
    """Run just the sequencing step."""
    return run_sequencing(db)


@router.post("/draft")
def run_draft_only(db: Session = Depends(get_db)):
    """Run just the drafting step."""
    return run_drafting(db)
