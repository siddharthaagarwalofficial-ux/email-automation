import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.connectors.base import EmailConnector
from app.connectors.mock import MockConnector
from app.services.sync import sync_threads
from app.services.sequencer import (
    run_classification,
    run_sequencing,
    run_drafting,
    run_auto_replies,
    pause_followups_for_replied,
)
from app.routes import threads, dashboard, pipeline, analytics, routing

logger = logging.getLogger(__name__)

SCHEDULER_INTERVAL_SECONDS = 60  # Run pipeline every 60 seconds


async def _background_pipeline(connector):
    """Background task that periodically syncs emails and runs the AI pipeline."""
    while True:
        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)
        try:
            db = SessionLocal()
            try:
                # Sync new emails
                sync_result = await sync_threads(connector, db)
                if sync_result["created"] or sync_result["updated"]:
                    logger.info(
                        f"[Scheduler] Synced: {sync_result['created']} created, "
                        f"{sync_result['updated']} updated"
                    )

                # Run pipeline steps
                c = run_classification(db)
                p = pause_followups_for_replied(db)
                s = run_sequencing(db)
                d = run_drafting(db)
                a = run_auto_replies(db)

                actions = []
                if c.get("classified"): actions.append(f"{c['classified']} classified")
                if p.get("cancelled"): actions.append(f"{p['cancelled']} paused")
                if s.get("scheduled"): actions.append(f"{s['scheduled']} scheduled")
                if d.get("drafted"): actions.append(f"{d['drafted']} drafted")
                if a.get("auto_replies_drafted"): actions.append(f"{a['auto_replies_drafted']} auto-replies")

                if actions:
                    logger.info(f"[Scheduler] Pipeline: {', '.join(actions)}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[Scheduler] Error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB and sync emails
    init_db()

    connector = _get_connector()
    await connector.connect()
    app.state.connector = connector

    # Initial sync
    db = SessionLocal()
    try:
        result = await sync_threads(connector, db)
        print(f"Initial sync: {result['created']} created, {result['updated']} updated")
    finally:
        db.close()

    # Start background scheduler
    scheduler_task = asyncio.create_task(_background_pipeline(connector))
    logger.info(f"[Scheduler] Started — running pipeline every {SCHEDULER_INTERVAL_SECONDS}s")

    yield

    # Shutdown: cancel scheduler
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        logger.info("[Scheduler] Stopped")


def _get_connector() -> EmailConnector:
    if settings.email_connector == "gmail":
        from app.connectors.gmail import GmailConnector
        return GmailConnector()
    return MockConnector()


app = FastAPI(
    title="Email Follow-Up Agent",
    description="AI-powered email follow-up automation system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threads.router)
app.include_router(dashboard.router)
app.include_router(pipeline.router)
app.include_router(analytics.router)
app.include_router(routing.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "connector": settings.email_connector}


@app.post("/api/sync")
async def trigger_sync():
    db = SessionLocal()
    try:
        result = await sync_threads(app.state.connector, db)
        return result
    finally:
        db.close()
