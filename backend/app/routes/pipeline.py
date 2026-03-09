import logging

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/run")
def run_pipeline(db: Session = Depends(get_db)):
    """Run the full AI pipeline: classify replies → pause follow-ups → schedule new follow-ups → draft emails → auto-reply drafts."""

    results = {}

    # Step 1: Classify any unclassified replies
    try:
        results["classification"] = run_classification(db)
    except Exception as e:
        logger.error(f"Classification step failed: {e}")
        results["classification"] = {"error": str(e)}

    # Step 2: Cancel follow-ups for threads that got replies
    try:
        results["paused"] = pause_followups_for_replied(db)
    except Exception as e:
        logger.error(f"Pause step failed: {e}")
        results["paused"] = {"error": str(e)}

    # Step 3: Schedule follow-ups for no-reply threads
    try:
        results["sequencing"] = run_sequencing(db)
    except Exception as e:
        logger.error(f"Sequencing step failed: {e}")
        results["sequencing"] = {"error": str(e)}

    # Step 4: Generate AI drafts for scheduled follow-ups
    try:
        results["drafting"] = run_drafting(db)
    except Exception as e:
        logger.error(f"Drafting step failed: {e}")
        results["drafting"] = {"error": str(e)}

    # Step 5: Draft auto-replies for positive/more_info replies
    try:
        results["auto_replies"] = run_auto_replies(db)
    except Exception as e:
        logger.error(f"Auto-reply step failed: {e}")
        results["auto_replies"] = {"error": str(e)}

    return results


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
