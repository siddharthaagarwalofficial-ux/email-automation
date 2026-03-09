from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.connectors.base import EmailConnector
from app.connectors.mock import MockConnector
from app.services.sync import sync_threads
from app.routes import threads, dashboard, pipeline, analytics, routing


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

    yield


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
