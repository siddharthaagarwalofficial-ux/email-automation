# Loom Walkthrough Script (5 min max)

---

## Pre-Recording Checklist
Before you hit record:
1. ✅ Backend running: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000`
2. ✅ Frontend running: `cd frontend && npm run dev`
3. ✅ Open **http://localhost:3000** in Chrome — make sure data is loaded (22 threads visible)
4. ✅ Open the **README.md** in GitHub (https://github.com/siddharthaagarwalofficial-ux/email-automation) — have the architecture diagram ready to show
5. ✅ Open **VSCode/editor** with `backend/app/services/classifier.py` ready to show
6. ✅ Open a **terminal** with `cd backend && source .venv/bin/activate` ready to run tests
7. ✅ Close Slack, notifications, anything distracting
8. ✅ Use Loom desktop app (not browser extension) for smoother recording

---

## 0:00–0:30 — Problem Framing (30s)
**[Screen: Dashboard at localhost:3000]**

SAY:
> "The biggest pain point in outbound outreach isn't the first email — it's everything after. Who replied? What did they mean? When should I follow up? What should I say? Right now this is all manual — threads fall through the cracks, follow-ups are generic, and intent gets lost. This system automates that entire workflow end-to-end."

---

## 0:30–1:30 — Architecture Walkthrough (60s)
**[Screen: Switch to GitHub README → scroll to architecture diagram]**

SAY:
> "Let me walk you through the architecture."

Point to each layer as you explain:

1. **Connector layer** → "Email sources are abstracted behind an interface — right now it's running on realistic mock data, but switching to Gmail is a single env var change. Adding Outlook or SendGrid means implementing just 4 methods."

2. **AI Pipeline** → "The core pipeline runs 5 steps in sequence: classify the reply, pause follow-ups if someone replied, schedule new follow-ups, draft AI-generated emails, and generate auto-reply drafts."

3. **Human-in-the-loop** → "Critically, nothing is ever auto-sent. Every draft goes through a review queue — scheduled, draft ready, approved, then sent. This is a deliberate product decision."

4. **Background scheduler** → "The pipeline auto-runs every 60 seconds in the background, so it works autonomously. But you can also trigger it manually from the dashboard."

KEY CALLOUT:
> "If your team picked this up tomorrow, you could add a new email source by implementing 4 methods, or add a new pipeline step without touching existing code."

---

## 1:30–3:30 — Live Demo (120s)
**[Screen: Switch to localhost:3000 dashboard]**

### Stats Bar (10s)
> "22 email threads synced — 8 awaiting reply, 14 have replied. 63.6% reply rate. The background scheduler has already classified everything automatically."

### Run Pipeline (15s)
- Click **"Run AI Pipeline"** button
> "I can also trigger the pipeline manually — it's idempotent, so running it twice won't duplicate anything."

### Thread Filters (15s)
- Click through **All / Awaiting Reply / Replied / Follow-up Scheduled** filters
> "Filters let you zero in on threads by status."

### Replied Thread Detail (20s)
- Click on a **replied thread** (e.g., one classified as "positive")
> "Here's a thread where the contact replied positively. You can see the full conversation, the classification badge with confidence score, and the AI's reasoning for why it chose this category."

### Follow-up Draft Review (25s)
- Click on an **awaiting-reply thread** that has follow-up drafts
> "For threads without replies, the system auto-scheduled a 3-step follow-up sequence at 3, 7, and 14 days. Each draft uses a different strategy — the first adds value, the second changes the angle, the third is a direct final ask."

### Inline Editing (20s)
- Click **"Edit Draft"** on a draft_ready follow-up
- Make a small edit to the body
- Click **"Save Changes"**
> "You can edit any draft inline before approving — tweak the subject, rewrite the body, make it sound like you."

### Approve & Send (15s)
- Click **"Approve & Queue"** on a draft
- Then click **"Send Now"**
> "Approve queues it, then you send when ready. Full human control over every outbound message."

### Analytics Tab (20s)
- Click the **Analytics** tab
> "Analytics shows classification breakdown, reply time distribution, follow-up effectiveness by sequence number, and meeting intent detection — threads where the contact wants to schedule a call are surfaced as action items."

### Routing Tab (15s)
- Click the **Routing** tab
> "Routing rules automatically assign classified replies to the right team — Partnerships handles positive replies, Product handles feature requests, Compliance handles unsubscribes. These rules are configurable."

---

## 3:30–4:15 — Code Quality & AI Integration (45s)
**[Screen: Switch to VSCode / editor]**

### AI Prompts (20s)
- Show `classifier.py` — scroll to the Claude prompt
> "The classifier prompt returns structured JSON — category, confidence score, reasoning, and meeting intent detection. It's not a black box."

### Graceful Degradation (10s)
> "If the Claude API is unavailable, the system falls back to a keyword-based classifier and template-based drafter — the app never breaks, it just runs in a simpler mode."

### Test Suite (15s)
**[Screen: Switch to terminal]**
- Run `pytest tests/ -v`
> "58 tests covering the full pipeline — classification, drafting, sequencing, and integration tests for every API endpoint. All green."

---

## 4:15–5:00 — What I'd Build Next (45s)
**[Screen: Switch back to dashboard]**

SAY:
> "With more time, here's what I'd build next:
>
> **First — Gmail push notifications** instead of polling. Real-time webhook-based reply detection.
>
> **Second — A/B testing for follow-ups.** Generate 2 draft variants per follow-up, track which gets better response rates.
>
> **Third — Slack integration.** Notify the assigned team the moment a reply is classified and routed.
>
> **Fourth — Production infra.** PostgreSQL, Redis job queues, Docker Compose. The SQLAlchemy ORM layer means the Postgres swap is a one-line config change.
>
> Every piece of this system is modular enough to extend without rewriting. This is a real system I'd ship. Happy to dive deeper on any part."

---

## Recording Tips
- 🎤 **Energy**: Speak like you're showing a colleague something cool, not reading a script
- ⏱️ **Pace**: Slightly faster than normal conversation — you have 5 minutes, use them well
- 🖱️ **Mouse**: Move slowly and deliberately so viewers can follow
- 🚫 **Don't**: Over-explain code line-by-line — focus on product thinking and design decisions
- ✅ **Do**: Pause for 1 second on each important screen so viewers can absorb it
- 💪 **Ending**: End with confidence. Don't trail off. Land the "Happy to dive deeper" line firmly.
