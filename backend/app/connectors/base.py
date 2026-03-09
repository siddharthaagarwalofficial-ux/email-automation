from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RawEmail:
    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body: str
    date: datetime
    in_reply_to: Optional[str] = None


@dataclass
class RawThread:
    thread_id: str
    subject: str
    messages: list[RawEmail]


class EmailConnector(ABC):
    """Abstract interface for email sources. Swap between Gmail and mock."""

    @abstractmethod
    async def connect(self) -> None:
        """Initialize the connection."""
        pass

    @abstractmethod
    async def get_threads(self, since: Optional[datetime] = None) -> list[RawThread]:
        """Fetch all outbound threads, optionally since a given date."""
        pass

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[RawThread]:
        """Fetch a single thread by ID."""
        pass

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str, thread_id: Optional[str] = None) -> str:
        """Send an email. Returns the message ID."""
        pass
