import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.connectors.base import EmailConnector, RawEmail, RawThread


MOCK_THREADS = [
    # --- NO REPLY threads (need follow-ups) ---
    {
        "recipient": "priya.sharma@beautybrand.in",
        "recipient_name": "Priya Sharma",
        "subject": "Collaboration Opportunity – Root Labs x Your Brand",
        "outbound_body": (
            "Hi Priya,\n\n"
            "I'm reaching out from Root Labs (part of Mosaic Wellness). We've been following your skincare content "
            "and think there's a great fit for a collaboration around our new derma range launching next month.\n\n"
            "We're looking at a mix of reels + stories with a 2-week campaign window. Happy to share more details "
            "if you're open to it.\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 5,
        "reply": None,
    },
    {
        "recipient": "arjun.mehta@fitfluence.com",
        "recipient_name": "Arjun Mehta",
        "subject": "Partnership Pitch – Men's Wellness x FitFluence",
        "outbound_body": (
            "Hey Arjun,\n\n"
            "Loved your recent series on men's fitness routines. At Root Labs, we're building India's largest "
            "men's wellness platform and I think your audience would resonate strongly with our products.\n\n"
            "Would love to explore a content partnership. Are you open to a quick chat this week?\n\nCheers,\nTeam Root Labs"
        ),
        "days_ago": 4,
        "reply": None,
    },
    {
        "recipient": "sneha.iyer@glowup.co",
        "recipient_name": "Sneha Iyer",
        "subject": "Root Labs – Creator Program Invite",
        "outbound_body": (
            "Hi Sneha,\n\n"
            "We're launching an exclusive creator program at Root Labs and your profile came up as a perfect fit. "
            "The program includes early product access, dedicated campaign briefs, and performance-based payouts.\n\n"
            "Would you be interested in learning more?\n\nWarm regards,\nTeam Root Labs"
        ),
        "days_ago": 8,
        "reply": None,
    },
    {
        "recipient": "rohan.gupta@dailydose.in",
        "recipient_name": "Rohan Gupta",
        "subject": "Quick Q – Content Collab with Root Labs",
        "outbound_body": (
            "Hi Rohan,\n\n"
            "Big fan of your daily health tips content. We're scaling our creator partnerships at Root Labs "
            "and think there's a natural alignment with your audience.\n\n"
            "No heavy commitment – just exploring if there's mutual interest. Open to a 15-min call?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 10,
        "reply": None,
    },
    {
        "recipient": "kavya.nair@wellnesswave.com",
        "recipient_name": "Kavya Nair",
        "subject": "Exploring a Partnership – Root Labs",
        "outbound_body": (
            "Hi Kavya,\n\n"
            "Your work on holistic wellness content is exactly the kind of authentic voice we look for at Root Labs. "
            "We'd love to explore a collaboration around our upcoming Ayurvedic range.\n\n"
            "Happy to share product samples and a campaign brief if you're interested.\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 3,
        "reply": None,
    },
    {
        "recipient": "vikram.singh@fitlife.in",
        "recipient_name": "Vikram Singh",
        "subject": "Root Labs x FitLife – Let's Talk",
        "outbound_body": (
            "Hey Vikram,\n\n"
            "We've been tracking the growth of FitLife and are impressed by the community you've built. "
            "Root Labs is looking for distribution partners in the fitness space.\n\n"
            "Would love to explore how we could work together. Free for a call next week?\n\nCheers,\nTeam Root Labs"
        ),
        "days_ago": 6,
        "reply": None,
    },

    # --- POSITIVE REPLY threads ---
    {
        "recipient": "ananya.reddy@skincarejunkie.in",
        "recipient_name": "Ananya Reddy",
        "subject": "Collab Invite – Root Labs Derma Launch",
        "outbound_body": (
            "Hi Ananya,\n\n"
            "We're launching a new dermatologist-backed skincare line at Root Labs and would love to partner "
            "with you for the launch campaign. Your honest review style is exactly what we're looking for.\n\n"
            "Interested in learning more?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 4,
        "reply": {
            "body": (
                "Hi Team Root Labs!\n\n"
                "Thanks for reaching out – I've actually been using some Mosaic products already and love them. "
                "Definitely interested in the derma launch collab. Can you share the campaign brief and timelines? "
                "I'm available for a call on Thursday or Friday this week.\n\nBest,\nAnanya"
            ),
            "days_ago": 2,
        },
    },
    {
        "recipient": "rahul.desai@menswellness.co",
        "recipient_name": "Rahul Desai",
        "subject": "Partnership – Men's Health Content x Root Labs",
        "outbound_body": (
            "Hey Rahul,\n\n"
            "Your content on men's grooming and wellness is top-notch. We're building out our creator network "
            "at Root Labs and would love to have you on board.\n\n"
            "This would be a paid partnership with creative freedom on your end. Interested?\n\nCheers,\nTeam Root Labs"
        ),
        "days_ago": 7,
        "reply": {
            "body": (
                "Hey!\n\n"
                "This sounds great. I've been looking for wellness brand partners that align with my content. "
                "Let's set up a call – I'm free Monday or Tuesday next week. "
                "Also, what's the typical budget range for these partnerships?\n\nRahul"
            ),
            "days_ago": 5,
        },
    },
    {
        "recipient": "meera.joshi@ayurlife.in",
        "recipient_name": "Meera Joshi",
        "subject": "Root Labs Creator Program – Invite",
        "outbound_body": (
            "Hi Meera,\n\n"
            "Your Ayurvedic wellness content resonates deeply with what we're building at Root Labs. "
            "We'd love to invite you to our creator program – early access to products, co-created campaigns, "
            "and competitive payouts.\n\nWould love to chat more.\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 6,
        "reply": {
            "body": (
                "Hi!\n\nI appreciate the invite. I'm very selective about brand partnerships but Root Labs "
                "seems aligned with my values. Let's schedule a meeting to discuss the details – "
                "I'd want to understand the product formulations before committing.\n\nMeera"
            ),
            "days_ago": 4,
        },
    },

    # --- NEGATIVE REPLY threads ---
    {
        "recipient": "deepak.kumar@techfit.io",
        "recipient_name": "Deepak Kumar",
        "subject": "Collaboration – Root Labs x TechFit",
        "outbound_body": (
            "Hi Deepak,\n\n"
            "We think TechFit's audience would be a great match for Root Labs' men's wellness products. "
            "Would you be interested in a sponsored content partnership?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 5,
        "reply": {
            "body": (
                "Hi,\n\n"
                "Thanks for thinking of me, but I'm not taking on any new brand partnerships right now. "
                "My content calendar is fully booked through Q3. Maybe revisit later in the year?\n\nDeepak"
            ),
            "days_ago": 3,
        },
    },
    {
        "recipient": "nisha.patel@organiclife.in",
        "recipient_name": "Nisha Patel",
        "subject": "Root Labs – Natural Wellness Collab",
        "outbound_body": (
            "Hi Nisha,\n\n"
            "Your organic lifestyle content is inspiring. We'd love to explore a partnership around "
            "our natural wellness range.\n\nOpen to a quick conversation?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 6,
        "reply": {
            "body": (
                "Hi Team,\n\n"
                "I appreciate the outreach but I only partner with brands that are 100% organic and cruelty-free certified. "
                "I checked your website and couldn't find these certifications. I'll have to pass for now.\n\nNisha"
            ),
            "days_ago": 4,
        },
    },

    # --- MORE INFO threads ---
    {
        "recipient": "aditya.rao@fitnessfirst.in",
        "recipient_name": "Aditya Rao",
        "subject": "Root Labs – Fitness Creator Partnership",
        "outbound_body": (
            "Hey Aditya,\n\n"
            "We're expanding our creator partnerships at Root Labs, specifically in the fitness vertical. "
            "Your content consistently gets great engagement and we'd love to collaborate.\n\n"
            "Open to hearing more?\n\nCheers,\nTeam Root Labs"
        ),
        "days_ago": 3,
        "reply": {
            "body": (
                "Hey,\n\n"
                "Interesting – can you send me more details? Specifically:\n"
                "- What products would be involved?\n"
                "- What's the expected deliverable count?\n"
                "- What's the compensation structure?\n\n"
                "Once I have these details I can make a call.\n\nAditya"
            ),
            "days_ago": 1,
        },
    },
    {
        "recipient": "pooja.deshmukh@skinglow.co",
        "recipient_name": "Pooja Deshmukh",
        "subject": "Quick Question – Root Labs Skincare Collab",
        "outbound_body": (
            "Hi Pooja,\n\n"
            "We're fans of your skincare routines and reviews. Root Labs is launching a new range "
            "and we'd love your authentic take on it.\n\nInterested in a paid collaboration?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 5,
        "reply": {
            "body": (
                "Hi!\n\n"
                "Thanks for reaching out. I'm potentially interested but I need to know more about the ingredients list "
                "and whether the products are dermatologically tested. Can you send me the product specs? "
                "Also, do you offer exclusivity or is this a non-exclusive arrangement?\n\nPooja"
            ),
            "days_ago": 3,
        },
    },

    # --- OUT OF OFFICE threads ---
    {
        "recipient": "sanjay.kapoor@wellnessco.in",
        "recipient_name": "Sanjay Kapoor",
        "subject": "Partnership Opportunity – Root Labs",
        "outbound_body": (
            "Hi Sanjay,\n\n"
            "We'd love to discuss a potential partnership between WellnessCo and Root Labs. "
            "Our product ranges are complementary and I think there's a strong synergy.\n\n"
            "Free for a call this week?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 4,
        "reply": {
            "body": (
                "Thank you for your email. I am currently out of the office on annual leave and will return on March 15. "
                "I will have limited access to email during this time. For urgent matters, please contact "
                "my colleague Ritu Sharma at ritu@wellnessco.in.\n\nBest regards,\nSanjay Kapoor"
            ),
            "days_ago": 4,
        },
    },
    {
        "recipient": "tanya.bhat@glowgirl.in",
        "recipient_name": "Tanya Bhat",
        "subject": "Root Labs – Beauty Creator Invite",
        "outbound_body": (
            "Hi Tanya,\n\n"
            "Your beauty content is amazing and we'd love to work with you on our upcoming campaign.\n\n"
            "Would you be open to a conversation?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 2,
        "reply": {
            "body": (
                "Hi! I'm currently on a digital detox retreat until March 20 and won't be checking emails regularly. "
                "I'll get back to you when I return. Thanks for your patience!\n\nTanya"
            ),
            "days_ago": 1,
        },
    },

    # --- WRONG PERSON threads ---
    {
        "recipient": "amit.shah@healthplus.in",
        "recipient_name": "Amit Shah",
        "subject": "Creator Partnership – Root Labs",
        "outbound_body": (
            "Hi Amit,\n\n"
            "We've been following your health & wellness content and think there's a great fit "
            "for a collaboration with Root Labs.\n\nWould you be interested?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 5,
        "reply": {
            "body": (
                "Hi,\n\n"
                "I think you have the wrong person. I'm Amit Shah from the finance department at HealthPlus – "
                "I don't create content. You might be looking for Amit Shah from our marketing team. "
                "His email is amit.shah.marketing@healthplus.in.\n\nRegards,\nAmit"
            ),
            "days_ago": 3,
        },
    },

    # --- UNSUBSCRIBE threads ---
    {
        "recipient": "riya.verma@inbox.me",
        "recipient_name": "Riya Verma",
        "subject": "Exciting Opportunity – Root Labs Creator Network",
        "outbound_body": (
            "Hi Riya,\n\n"
            "We're building a creator network at Root Labs and your profile caught our attention. "
            "Would you be interested in learning more about paid collaboration opportunities?\n\n"
            "Best,\nTeam Root Labs"
        ),
        "days_ago": 3,
        "reply": {
            "body": (
                "Please remove me from your mailing list. I did not sign up for this and do not wish to receive "
                "any further emails from your company. If this continues I will report it as spam.\n\nRiya"
            ),
            "days_ago": 2,
        },
    },

    # --- More variety: POSITIVE with meeting intent ---
    {
        "recipient": "karan.malhotra@influencelab.in",
        "recipient_name": "Karan Malhotra",
        "subject": "Root Labs – Influencer Partnership",
        "outbound_body": (
            "Hey Karan,\n\n"
            "We're big fans of your content at Root Labs. We're scaling our influencer program and "
            "would love to have you as a key partner.\n\n"
            "Interested in a paid, long-term collaboration?\n\nCheers,\nTeam Root Labs"
        ),
        "days_ago": 3,
        "reply": {
            "body": (
                "Hey!\n\n"
                "This sounds promising – I've actually been looking for a wellness brand to partner with long-term. "
                "Can we set up a call for Wednesday at 3pm? Or Thursday works too. "
                "My manager Neha (neha@influencelab.in) should be on the call as well to discuss commercials.\n\nKaran"
            ),
            "days_ago": 1,
        },
    },

    # --- POSITIVE but needs routing (product question) ---
    {
        "recipient": "divya.krishnan@beautybox.co",
        "recipient_name": "Divya Krishnan",
        "subject": "Root Labs – Skincare Collab Opportunity",
        "outbound_body": (
            "Hi Divya,\n\n"
            "We love your skincare unboxing content and think our new derma range would be perfect for a collab.\n\n"
            "Would you be open to trying the products and sharing your honest review?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 5,
        "reply": {
            "body": (
                "Hi!\n\n"
                "I'm interested but I have a few product-related questions first:\n"
                "1. Are these products suitable for sensitive skin?\n"
                "2. What's the full ingredient list for the moisturizer?\n"
                "3. Are they dermatologist-tested?\n\n"
                "I only review products I personally trust, so these details matter to me.\n\nDivya"
            ),
            "days_ago": 3,
        },
    },

    # --- Additional NO REPLY for follow-up variety ---
    {
        "recipient": "nikhil.jain@healthhub.in",
        "recipient_name": "Nikhil Jain",
        "subject": "Root Labs – Health Content Partnership",
        "outbound_body": (
            "Hi Nikhil,\n\n"
            "Your evidence-based health content is refreshing. At Root Labs, we value scientific credibility "
            "and think a partnership would be mutually beneficial.\n\n"
            "Would you be open to exploring this?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 15,
        "reply": None,
    },
    {
        "recipient": "swati.mishra@yogaflow.in",
        "recipient_name": "Swati Mishra",
        "subject": "Wellness Collaboration – Root Labs x YogaFlow",
        "outbound_body": (
            "Hi Swati,\n\n"
            "We're exploring partnerships in the yoga and wellness space. Your authentic approach to wellness "
            "content aligns perfectly with Root Labs' mission.\n\n"
            "Would love to discuss a collaboration. Open to a call?\n\nBest,\nTeam Root Labs"
        ),
        "days_ago": 12,
        "reply": None,
    },

    # --- NEGATIVE (polite decline with reason) ---
    {
        "recipient": "varun.thakur@gymrat.co",
        "recipient_name": "Varun Thakur",
        "subject": "Root Labs – Fitness Brand Partnership",
        "outbound_body": (
            "Hey Varun,\n\n"
            "Your gym content is fire. We'd love to partner with you for our men's fitness supplement range.\n\n"
            "Interested?\n\nCheers,\nTeam Root Labs"
        ),
        "days_ago": 4,
        "reply": {
            "body": (
                "Hey,\n\n"
                "Appreciate the offer but I already have an exclusive deal with another supplement brand "
                "so I can't take this on. Non-compete clause. Hope you understand.\n\nVarun"
            ),
            "days_ago": 2,
        },
    },
]


def _build_threads() -> list[RawThread]:
    now = datetime.now(timezone.utc)
    threads = []

    for i, t in enumerate(MOCK_THREADS):
        thread_id = f"mock_thread_{i+1:03d}"
        outbound_date = now - timedelta(days=t["days_ago"])

        messages = [
            RawEmail(
                message_id=f"mock_msg_{i+1:03d}_out",
                thread_id=thread_id,
                sender="outreach@rootlabs.in",
                recipient=t["recipient"],
                subject=t["subject"],
                body=t["outbound_body"],
                date=outbound_date,
            )
        ]

        if t["reply"]:
            reply_date = now - timedelta(days=t["reply"]["days_ago"])
            messages.append(
                RawEmail(
                    message_id=f"mock_msg_{i+1:03d}_in",
                    thread_id=thread_id,
                    sender=t["recipient"],
                    recipient="outreach@rootlabs.in",
                    subject=f"Re: {t['subject']}",
                    body=t["reply"]["body"],
                    date=reply_date,
                    in_reply_to=f"mock_msg_{i+1:03d}_out",
                )
            )

        threads.append(RawThread(thread_id=thread_id, subject=t["subject"], messages=messages))

    return threads


class MockConnector(EmailConnector):
    def __init__(self):
        self._threads: list[RawThread] = []
        self._sent: list[RawEmail] = []

    async def connect(self) -> None:
        self._threads = _build_threads()

    async def get_threads(self, since=None) -> list[RawThread]:
        if since:
            return [
                t for t in self._threads
                if any(m.date >= since for m in t.messages)
            ]
        return self._threads

    async def get_thread(self, thread_id: str):
        for t in self._threads:
            if t.thread_id == thread_id:
                return t
        return None

    async def send_email(self, to: str, subject: str, body: str, thread_id=None) -> str:
        msg_id = f"mock_sent_{uuid.uuid4().hex[:8]}"
        msg = RawEmail(
            message_id=msg_id,
            thread_id=thread_id or f"mock_thread_new_{uuid.uuid4().hex[:8]}",
            sender="outreach@rootlabs.in",
            recipient=to,
            subject=subject,
            body=body,
            date=datetime.now(timezone.utc),
        )
        self._sent.append(msg)

        if thread_id:
            for t in self._threads:
                if t.thread_id == thread_id:
                    t.messages.append(msg)
                    break

        return msg_id
