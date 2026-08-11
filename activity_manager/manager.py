"""
Activity Manager Module (Module 3)

Responsibility: manage activity state - what activity is currently active,
when an activity begins, when it ends, and what happens when another
activity starts (auto-closing the previous one).

Must NOT talk to Telegram directly, generate charts, calculate weekly
statistics, decide how reports look, or execute raw SQL everywhere. State
is held in memory for now; Module 5 (database) will provide persistence
later without needing to change this module's public interface.

Status: implemented and tested.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable, List, Optional


@dataclass(frozen=True)
class Activity:
    name: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActivityManager:
    """Tracks the single currently-active activity and a history of closed
    activities. Starting a new activity while one is active auto-closes the
    previous one first."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now) -> None:
        self._clock = clock
        self._current: Optional[Activity] = None
        self._history: List[Activity] = []

    def start_activity(self, name: str) -> Activity:
        """Start a new activity, auto-closing whatever was previously
        active. Raises ValueError if name is empty or whitespace-only."""
        if not name or not name.strip():
            raise ValueError("Activity name must not be empty")

        if self._current is not None:
            self._close_current()

        activity = Activity(name=name.strip(), started_at=self._clock())
        self._current = activity
        return activity

    def stop_activity(self) -> Optional[Activity]:
        """Close the current activity and return it, or None if nothing is
        currently active."""
        if self._current is None:
            return None
        return self._close_current()

    def get_current(self) -> Optional[Activity]:
        return self._current

    def get_history(self) -> List[Activity]:
        """Closed activities in the order they ended. Returns a copy so
        callers cannot mutate internal state."""
        return list(self._history)

    def _close_current(self) -> Activity:
        closed = replace(self._current, ended_at=self._clock())
        self._history.append(closed)
        self._current = None
        return closed
