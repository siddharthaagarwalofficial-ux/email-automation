"""Tests for the pipeline API endpoint and thread routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    EmailThread, Email,
    ThreadStatus, EmailDirection, EmailType,
)
from datetime import datetime, timedelta


@pytest.fixture
def test_app():
    """Create an in-memory test database, override get_db, and return client + session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    session = TestSession()
    client = TestClient(app, raise_server_exceptions=False)

    yield client, session

    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seeded_app(test_app):
    """Seed the test database with sample threads."""
    client, db = test_app

    # Awaiting reply thread (old enough for follow-up)
    t1 = EmailThread(
        recipient_email="creator1@example.com",
        recipient_name="Alice Blogger",
        subject="Collab opportunity",
        status=ThreadStatus.AWAITING_REPLY,
        created_at=datetime.utcnow() - timedelta(days=10),
        updated_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(t1)
    db.flush()

    e1 = Email(
        thread_id=t1.id,
        direction=EmailDirection.OUTBOUND,
        email_type=EmailType.ORIGINAL,
        sender="outreach@rootlabs.in",
        recipient="creator1@example.com",
        subject="Collab opportunity",
        body="Hi Alice, we'd love to partner with you...",
        sent_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(e1)

    # Replied thread
    t2 = EmailThread(
        recipient_email="creator2@example.com",
        recipient_name="Bob Influencer",
        subject="Partnership proposal",
        status=ThreadStatus.REPLIED,
        created_at=datetime.utcnow() - timedelta(days=7),
        updated_at=datetime.utcnow() - timedelta(days=5),
    )
    db.add(t2)
    db.flush()

    e2 = Email(
        thread_id=t2.id,
        direction=EmailDirection.OUTBOUND,
        email_type=EmailType.ORIGINAL,
        sender="outreach@rootlabs.in",
        recipient="creator2@example.com",
        subject="Partnership proposal",
        body="Hi Bob, great content! Let's collaborate...",
        sent_at=datetime.utcnow() - timedelta(days=7),
    )
    db.add(e2)

    e3 = Email(
        thread_id=t2.id,
        direction=EmailDirection.INBOUND,
        email_type=EmailType.REPLY,
        sender="creator2@example.com",
        recipient="outreach@rootlabs.in",
        subject="Re: Partnership proposal",
        body="Sounds great! I'd love to learn more about the compensation. Can you tell me more?",
        sent_at=datetime.utcnow() - timedelta(days=5),
    )
    db.add(e3)

    db.commit()
    return client, db


class TestPipelineEndpoint:
    """Integration tests for the /api/pipeline/run endpoint."""

    def test_pipeline_runs_successfully(self, seeded_app):
        client, _ = seeded_app
        response = client.post("/api/pipeline/run")
        assert response.status_code == 200

        data = response.json()
        assert "classification" in data
        assert "sequencing" in data
        assert "drafting" in data
        assert "auto_replies" in data
        assert "paused" in data

    def test_pipeline_classifies_replied_threads(self, seeded_app):
        client, _ = seeded_app
        response = client.post("/api/pipeline/run")
        data = response.json()
        assert data["classification"]["classified"] >= 1

    def test_pipeline_schedules_follow_ups(self, seeded_app):
        client, _ = seeded_app
        response = client.post("/api/pipeline/run")
        data = response.json()
        assert data["sequencing"]["scheduled"] >= 1

    def test_pipeline_drafts_follow_ups(self, seeded_app):
        client, _ = seeded_app
        response = client.post("/api/pipeline/run")
        data = response.json()
        assert data["drafting"]["drafted"] >= 1

    def test_pipeline_idempotent(self, seeded_app):
        """Running the pipeline twice should not duplicate work."""
        client, _ = seeded_app
        client.post("/api/pipeline/run")
        response = client.post("/api/pipeline/run")
        data = response.json()
        assert data["classification"]["classified"] == 0
        assert data["sequencing"]["scheduled"] == 0
        assert data["drafting"]["drafted"] == 0


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_ok(self, test_app):
        client, _ = test_app
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestThreadsEndpoint:
    """Test the threads listing endpoint."""

    def test_list_threads(self, seeded_app):
        client, _ = seeded_app
        response = client.get("/api/threads/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_filter_by_status(self, seeded_app):
        client, _ = seeded_app
        response = client.get("/api/threads/?status=replied")
        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "replied" for t in data)

    def test_get_single_thread(self, seeded_app):
        client, _ = seeded_app
        response = client.get("/api/threads/1")
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert "follow_ups" in data

    def test_get_nonexistent_thread(self, seeded_app):
        client, _ = seeded_app
        response = client.get("/api/threads/999")
        assert response.status_code == 404
