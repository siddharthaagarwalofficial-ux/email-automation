# Email Follow-Up Agent

An AI-powered email follow-up automation system that detects replies, classifies intent, generates context-aware follow-ups, and routes conversations to the right team — built as a working prototype for Root Labs.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Threads   │  │ Analytics │  │ Routing  │  │ Stats Cards   │  │
│  │ List +    │  │ Charts +  │  │ Rules +  │  │ Reply Rate,   │  │
│  │ Detail    │  │ Timelines │  │ Assigns  │  │ Avg Time etc  │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────┴──────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│                                                                  │
│  ┌─────────────────────── API Layer ──────────────────────────┐  │
│  │ /threads  /dashboard  /pipeline  /analytics  /routing      │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│  ┌──────────── AI Pipeline (Orchestrator) ────────────────────┐  │
│  │                                                            │  │
│  │  1. Classify    2. Pause      3. Schedule    4. Draft      │  │
│  │     Replies        FU's         FU's           Emails      │  │
│  │  (Claude API)  (if replied)  (3/7/14 day)  (Claude API)   │  │
│  │                                                            │  │
│  │  5. Auto-Reply Drafts (for positive/more_info)             │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│  ┌──── Services ──────────┼──────────── Connectors ───────────┐  │
│  │ classifier.py          │          ┌──────────────┐         │  │
│  │ drafter.py             │          │ EmailConnector│ (base)  │  │
│  │ sequencer.py           │          ├──────────────┤         │  │
│  │ sync.py                │          │ GmailConnect │         │  │
│  │                        │          │ MockConnector │         │  │
│  └────────────────────────┘          └──────────────┘         │  │
│                           │                                      │
│  ┌────────────────────────┴───────────────────────────────────┐  │
│  │                    SQLite Database                          │  │
│  │  email_threads │ emails │ classifications │ follow_ups     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**1. Connector Abstraction Pattern**
The email source is abstracted behind an `EmailConnector` interface with 4 methods: `connect()`, `get_threads()`, `get_thread()`, `send_email()`. Swap between Gmail and mock data with a single env var (`EMAIL_CONNECTOR=gmail|mock`). This means:
- Development and demos work instantly with realistic mock data
- Gmail integration is a config change, not a code change
- Adding Outlook, SendGrid, or any other source = implement 4 methods

**2. Pipeline-as-a-Single-Call**
The entire AI workflow (classify → pause → schedule → draft → auto-reply) runs as one orchestrated pipeline via `POST /api/pipeline/run`. Each step is also available individually. This makes it easy to:
- Run the full pipeline on a cron schedule in production
- Debug individual steps in isolation
- Add new pipeline stages without touching existing ones

**3. Human-in-the-Loop by Default**
AI-generated drafts are **never auto-sent**. They go through a review queue: `scheduled → draft_ready → approved → sent`. This is a deliberate product decision — outbound emails represent the company's voice and need human review before sending.

**4. Classification with Reasoning**
The classifier returns not just a category but also a confidence score and reasoning. This makes the system auditable and helps the team understand edge cases where the AI might be uncertain.

**5. SQLite for Prototyping**
No external database dependency. The entire state lives in a single file. For production, swap to PostgreSQL by changing `DATABASE_URL` — SQLAlchemy handles the rest.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python + FastAPI | Fast to prototype, async support, excellent for API-first systems |
| AI | Claude API (Sonnet) | Strong classification accuracy, natural follow-up drafting |
| Database | SQLite + SQLAlchemy | Zero-config, portable, ORM makes it swappable |
| Frontend | Next.js + Tailwind CSS | Fast to build, clean dashboard UI |
| Email | Gmail API (+ Mock fallback) | Real OAuth integration with seamless mock fallback |

---

## Features

### Core Requirements
- **Reply Detection & Classification** — Classifies replies into 6 categories (positive, negative, more_info, out_of_office, wrong_person, unsubscribe) with confidence scores
- **Follow-Up Sequencing** — Configurable 3-step sequence (3/7/14 days) that auto-pauses on reply
- **AI-Powered Follow-Up Drafting** — Context-aware drafts that vary angle per sequence (value-add → new hook → final ask)
- **Status Dashboard** — Real-time view of all threads, filters, conversation detail, draft review queue

### Bonus Features
- **Auto-Reply Drafting** — Generates response drafts for positive/more_info replies
- **Meeting Intent Detection** — Surfaces threads where the contact wants to schedule a call as action items
- **Reply Routing** — Routes classified replies to the right team (Partnerships, Product, Outreach, Compliance) with configurable rules
- **Analytics** — Classification breakdown, status distribution, reply time charts, follow-up effectiveness

---

## Setup & Running

### Prerequisites
- Python 3.9+
- Node.js 18+
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### 1. Clone and setup backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Setup frontend

```bash
cd frontend
npm install
```

### 3. Run both servers

```bash
# Terminal 1 — Backend (port 8000)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend (port 3000)
cd frontend
npm run dev
```

### 4. Open the dashboard

Visit **http://localhost:3000**

The app auto-syncs 22 mock email threads on startup. Click **"Run AI Pipeline"** to classify replies and generate follow-up drafts.

### 5. (Optional) Connect to Gmail

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials and download `credentials.json`
4. Place `credentials.json` in the `backend/` directory
5. Set `EMAIL_CONNECTOR=gmail` in `.env`
6. Restart the backend — it will open a browser for OAuth consent on first run

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/sync` | POST | Sync emails from connector into DB |
| `/api/pipeline/run` | POST | Run full AI pipeline (classify → schedule → draft) |
| `/api/pipeline/classify` | POST | Run classification only |
| `/api/pipeline/sequence` | POST | Run sequencing only |
| `/api/pipeline/draft` | POST | Run drafting only |
| `/api/threads/` | GET | List all threads (filterable by status/category) |
| `/api/threads/{id}` | GET | Get thread detail with emails, classification, follow-ups |
| `/api/threads/{id}/follow-ups/{fid}/action` | POST | Approve/reject/edit a follow-up draft |
| `/api/threads/{id}/follow-ups/{fid}/send` | POST | Send an approved follow-up |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/analytics/classification-breakdown` | GET | Reply classification distribution |
| `/api/analytics/status-breakdown` | GET | Thread status distribution |
| `/api/analytics/reply-timeline` | GET | Reply time per thread |
| `/api/analytics/meeting-intents` | GET | Threads with meeting intent detected |
| `/api/analytics/follow-up-effectiveness` | GET | Follow-up conversion by sequence number |
| `/api/routing/rules` | GET | Get routing rules |
| `/api/routing/rules/{category}` | PUT | Update a routing rule |
| `/api/routing/assignments` | GET | Get all classified threads with routing assignments |

---

## Project Structure

```
email-follow-up-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, CORS
│   │   ├── config.py               # Pydantic settings from .env
│   │   ├── database.py             # SQLAlchemy engine + session
│   │   ├── models.py               # ORM models (Thread, Email, Classification, FollowUp)
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── connectors/
│   │   │   ├── base.py             # Abstract EmailConnector interface
│   │   │   ├── gmail.py            # Gmail API implementation
│   │   │   └── mock.py             # Mock data (22 realistic threads)
│   │   ├── services/
│   │   │   ├── classifier.py       # Claude-powered reply classification
│   │   │   ├── drafter.py          # Claude-powered follow-up + auto-reply drafting
│   │   │   ├── sequencer.py        # Pipeline orchestration (classify, schedule, draft, pause)
│   │   │   └── sync.py             # Email sync from connector → DB
│   │   └── routes/
│   │       ├── threads.py          # Thread CRUD + follow-up actions + send
│   │       ├── dashboard.py        # Dashboard stats
│   │       ├── pipeline.py         # AI pipeline triggers
│   │       ├── analytics.py        # Charts and metrics data
│   │       └── routing.py          # Reply routing rules + assignments
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          # Root layout
│       │   └── page.tsx            # Main dashboard (tabbed: Threads, Analytics, Routing)
│       ├── components/
│       │   ├── StatsCards.tsx       # Top-level metrics
│       │   ├── ThreadList.tsx       # Filterable thread list
│       │   ├── ThreadDetail.tsx     # Conversation view + draft review + send
│       │   ├── Analytics.tsx        # Charts and action items
│       │   └── Routing.tsx          # Routing rules and assignments
│       ├── lib/
│       │   └── api.ts              # API client
│       └── types/
│           └── index.ts            # TypeScript types
├── .gitignore
└── README.md
```

---

## Tradeoffs & What I'd Build Next

### Tradeoffs Made
- **SQLite over PostgreSQL** — Zero-config for reviewers. The ORM layer means swapping is a one-line change.
- **Mock data over requiring Gmail setup** — Reviewers can clone-and-run immediately. Gmail connector is fully built and tested separately.
- **Polling over webhooks** — Pipeline runs on-demand via button click. Production would use Gmail push notifications or a cron job.
- **Client-side state over server-sent events** — Dashboard refreshes after actions. Production would use WebSockets for real-time updates.

### What I'd Build Next (with more time)
1. **Background scheduler** — Run the pipeline automatically on a cron (every 15 min) instead of manual trigger
2. **Gmail push notifications** — Replace polling with real-time webhook-based reply detection
3. **Draft editing inline** — Allow editing follow-up drafts directly in the UI before approving
4. **A/B testing for follow-ups** — Generate 2 draft variants per follow-up, track which performs better
5. **Team collaboration** — Multi-user support with role-based access (reviewer, sender, admin)
6. **Slack/Teams integration** — Notify the assigned team when a new reply is classified and routed
7. **Production infra** — PostgreSQL, Redis for job queues, Docker compose for deployment
