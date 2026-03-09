# Loom Walkthrough Script (5 min max)

## 0:00–0:30 — Problem Framing
"The biggest pain point in outbound outreach isn't the first email — it's everything after. Tracking who replied, classifying intent, knowing when to follow up, and drafting contextual messages is all manual. Threads fall through the cracks. This system automates that entire workflow."

## 0:30–1:30 — Architecture Walkthrough
Show the README architecture diagram and explain:

- **Connector layer**: Abstracted email source — mock data for demo, Gmail API for production. One env var to switch.
- **AI Pipeline**: Single-call orchestrator that runs 5 steps: classify → pause → schedule → draft → auto-reply
- **Human-in-the-loop**: Drafts are never auto-sent. They go through review → approve → send.
- **Modular routes**: Threads, Analytics, Routing, Pipeline — each is independent and extensible.

Key callout: "If your team picked this up tomorrow, you could add a new email source by implementing 4 methods, or add a new pipeline step without touching existing code."

## 1:30–3:30 — Live Demo
Walk through the dashboard:

1. **Stats bar** — "22 threads synced, 8 awaiting reply, 14 replied, 63.6% reply rate"
2. **Click 'Run AI Pipeline'** — Show it classifying all 14 replies, scheduling follow-ups, and generating drafts
3. **Thread list** — Show filters working (Awaiting Reply, Replied, Follow-up)
4. **Click a replied thread** — Show the conversation, classification badge (e.g., "Positive, 95% confidence"), and reasoning
5. **Click an awaiting-reply thread** — Show the AI-generated follow-up draft with approve/reject buttons
6. **Approve a draft → click Send** — Show the full lifecycle
7. **Analytics tab** — Show classification breakdown, reply time chart, meeting intent action items
8. **Routing tab** — Show how replies are auto-routed to the right team

## 3:30–4:30 — AI Integration Deep-Dive
Show the actual prompt in `classifier.py`:

- "The classifier returns structured JSON with category, confidence, reasoning, and meeting intent detection."
- "For follow-up drafting, each sequence number has a different strategy — #1 adds value, #2 changes the angle, #3 is the final direct ask."
- "Auto-replies are drafted for positive and more_info categories, ready for human review."

## 4:30–5:00 — What's Next
"With more time, I'd add:
- Background scheduler to run the pipeline automatically every 15 minutes
- Gmail push notifications instead of polling
- A/B testing for follow-up drafts to optimize response rates
- Slack notifications when a reply is classified and routed

This is designed as a foundation — every piece is modular enough to extend without rewriting."

---

## Tips for Recording
- Have the dashboard open at localhost:3000 with the backend running
- Run the pipeline BEFORE recording so data is populated, OR run it live for dramatic effect
- Keep energy up, speak concisely, don't over-explain code — focus on product thinking
- End with confidence: "This is a real system I'd ship. Happy to dive deeper on any part."
