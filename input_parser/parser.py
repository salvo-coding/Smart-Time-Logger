"""
Input Parser Module (Module 2)

Responsibility: convert a telegram_interface.messages.IncomingMessage into a
standardized Command (START_ACTIVITY, STOP_ACTIVITY, SHOW_CURRENT,
SHOW_TODAY, SHOW_WEEK, HELP).

Must NOT touch the database, close activities, calculate durations,
generate reports, or talk to Telegram directly.

Recognized syntax (case-insensitive, leading/trailing whitespace ignored):
    /start <activity name>   -> START_ACTIVITY (bare /start with no name
                                 falls back to HELP, matching what Telegram
                                 auto-sends when a user first opens the bot)
    /stop                    -> STOP_ACTIVITY
    /current                 -> SHOW_CURRENT
    /today                   -> SHOW_TODAY
    /week                    -> SHOW_WEEK
    /help                    -> HELP
    anything else            -> UNKNOWN

Status: implemented and tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from telegram_interface.messages import IncomingMessage


class CommandType(Enum):
    START_ACTIVITY = auto()
    STOP_ACTIVITY = auto()
    SHOW_CURRENT = auto()
    SHOW_TODAY = auto()
    SHOW_WEEK = auto()
    HELP = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Command:
    type: CommandType
    activity_name: Optional[str] = None
    raw_text: str = ""


_NO_ARG_COMMANDS = {
    "/stop": CommandType.STOP_ACTIVITY,
    "/current": CommandType.SHOW_CURRENT,
    "/today": CommandType.SHOW_TODAY,
    "/week": CommandType.SHOW_WEEK,
    "/help": CommandType.HELP,
}


def parse_command(message: IncomingMessage) -> Command:
    """Convert an IncomingMessage into a standardized Command."""
    text = message.text.strip()
    if not text:
        return Command(type=CommandType.UNKNOWN, raw_text=message.text)

    first_word, _, rest = text.partition(" ")
    command_word = _strip_bot_mention(first_word).lower()
    rest = rest.strip()

    if command_word == "/start":
        if rest:
            return Command(type=CommandType.START_ACTIVITY, activity_name=rest, raw_text=text)
        return Command(type=CommandType.HELP, raw_text=text)

    command_type = _NO_ARG_COMMANDS.get(command_word)
    if command_type is not None:
        return Command(type=command_type, raw_text=text)

    return Command(type=CommandType.UNKNOWN, raw_text=text)


def _strip_bot_mention(command_word: str) -> str:
    """Strip a trailing '@botusername' Telegram sometimes appends to slash
    commands, e.g. '/start@smarttimeloggerbot' -> '/start'."""
    at_index = command_word.find("@")
    return command_word[:at_index] if at_index != -1 else command_word
