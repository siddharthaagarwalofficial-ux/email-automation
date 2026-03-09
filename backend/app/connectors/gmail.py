import base64
import email
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import settings
from app.connectors.base import EmailConnector, RawEmail, RawThread

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailConnector(EmailConnector):
    def __init__(self):
        self.service = None
        self.user_email = None

    async def connect(self) -> None:
        creds = None
        import os

        if os.path.exists(settings.gmail_token_path):
            creds = Credentials.from_authorized_user_file(settings.gmail_token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.gmail_credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(settings.gmail_token_path, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        profile = self.service.users().getProfile(userId="me").execute()
        self.user_email = profile["emailAddress"]

    async def get_threads(self, since: Optional[datetime] = None) -> list[RawThread]:
        query = "in:sent"
        if since:
            query += f" after:{since.strftime('%Y/%m/%d')}"

        results = self.service.users().threads().list(
            userId="me", q=query, maxResults=50
        ).execute()

        threads = []
        for t in results.get("threads", []):
            raw_thread = await self.get_thread(t["id"])
            if raw_thread:
                threads.append(raw_thread)

        return threads

    async def get_thread(self, thread_id: str) -> Optional[RawThread]:
        try:
            thread_data = self.service.users().threads().get(
                userId="me", id=thread_id, format="full"
            ).execute()
        except Exception:
            return None

        messages = []
        subject = ""

        for msg in thread_data.get("messages", []):
            raw_email = self._parse_message(msg)
            if raw_email:
                messages.append(raw_email)
                if not subject:
                    subject = raw_email.subject

        if not messages:
            return None

        return RawThread(thread_id=thread_id, subject=subject, messages=messages)

    def _parse_message(self, msg: dict) -> Optional[RawEmail]:
        headers = {h["name"].lower(): h["value"] for h in msg["payload"]["headers"]}

        sender = headers.get("from", "")
        recipient = headers.get("to", "")
        subject = headers.get("subject", "")
        date_str = headers.get("date", "")
        in_reply_to = headers.get("in-reply-to")
        message_id = msg["id"]

        try:
            date = email.utils.parsedate_to_datetime(date_str)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
        except Exception:
            date = datetime.now(timezone.utc)

        body = self._extract_body(msg["payload"])

        return RawEmail(
            message_id=message_id,
            thread_id=msg["threadId"],
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            date=date,
            in_reply_to=in_reply_to,
        )

    def _extract_body(self, payload: dict) -> str:
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        parts = payload.get("parts", [])
        for part in parts:
            if part["mimeType"] == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

        for part in parts:
            if part["mimeType"] == "text/html" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

        for part in parts:
            nested = self._extract_body(part)
            if nested:
                return nested

        return ""

    async def send_email(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> str:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_body = {"raw": raw}

        if thread_id:
            send_body["threadId"] = thread_id

        sent = self.service.users().messages().send(
            userId="me", body=send_body
        ).execute()

        return sent["id"]
