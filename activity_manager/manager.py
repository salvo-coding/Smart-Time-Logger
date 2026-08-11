"""
Activity Manager Module (Module 3)

Responsibility: manage activity state - what activity is currently active,
when an activity begins, when it ends, and what happens when another
activity starts (auto-closing the previous one).

Must NOT talk to Telegram directly, generate charts, calculate weekly
statistics, decide how reports look, or execute raw SQL directly - all
persistence is delegated to the injected Database (Module 5), which is the
single source of truth. This class contains no SQL.

Status: implemented and tested.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, List, Optional

from database.db import ActivityRecord, Database


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActivityManager:
    """Coordinates activity state on top of a Database: what's currently
    active, and auto-closing the previous activity when a new one starts."""

    def __init__(self, database: Database, clock: Callable[[], datetime] = _utc_now) -> None:
        self._database = database
        self._clock = clock

    def start_activity(self, name: str) -> ActivityRecord:
        """Start a new activity, auto-closing whatever was previously
        active. Raises ValueError if name is empty or whitespace-only."""
        if not name or not name.strip():
            raise ValueError("Activity name must not be empty")
        name = name.strip()

        previous = self._database.get_current_activity()
        if previous is not None:
            self._database.close_activity(previous.id, ended_at=self._clock())

        return self._database.insert_activity(name=name, started_at=self._clock())

    def stop_activity(self) -> Optional[ActivityRecord]:
        """Close the current activity and return it, or None if nothing is
        currently active."""
        current = self._database.get_current_activity()
        if current is None:
            return None
        return self._database.close_activity(current.id, ended_at=self._clock())

    def get_current(self) -> Optional[ActivityRecord]:
        return self._database.get_current_activity()

    def get_history(self) -> List[ActivityRecord]:
        return self._database.get_closed_activities()

    def get_today(self) -> List[ActivityRecord]:
        return self._database.get_today_activities(now=self._clock())

    def get_this_week(self) -> List[ActivityRecord]:
        return self._database.get_this_week_activities(now=self._clock())
