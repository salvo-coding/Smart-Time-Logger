"""
The contract between Module 1 (Telegram interface) and Module 2 (input
parser). Defined now so Module 1 never needs refactoring once Module 2 is
built against it.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable


@dataclass(frozen=True)
class IncomingMessage:
    telegram_user_id: int
    chat_id: int
    message_id: int
    text: str
    received_at: datetime  # UTC


IncomingMessageHandler = Callable[[IncomingMessage], Awaitable[str]]
