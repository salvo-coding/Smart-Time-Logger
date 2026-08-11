"""
Database & Persistence Module (Module 5)

Responsibility: store and retrieve persistent time-tracking data in SQLite,
the single source of truth (insert activities, get current activity, get
today's/this week's activities).

Must NOT interpret Telegram commands, calculate productivity scores,
generate charts, decide whether an activity is good or bad, or contain
user-interface logic.

Every write goes through Module 4's validate_activity() first, so invalid
data can never reach permanent storage.

Status: implemented and tested.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from validation.validators import validate_activity


@dataclass(frozen=True)
class ActivityRecord:
    id: int
    name: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


def _to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class Database:
    """SQLite-backed store of activity records - the single source of
    truth for persisted time-tracking data."""

    def __init__(self, db_path: str = "data/time_logger.db") -> None:
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT
            )
            """
        )
        self._connection.commit()

    def insert_activity(
        self, name: str, started_at: datetime, ended_at: Optional[datetime] = None
    ) -> ActivityRecord:
        validate_activity(name=name, started_at=started_at, ended_at=ended_at)
        name = name.strip()

        cursor = self._connection.execute(
            "INSERT INTO activities (name, started_at, ended_at) VALUES (?, ?, ?)",
            (name, _to_iso(started_at), _to_iso(ended_at) if ended_at is not None else None),
        )
        self._connection.commit()
        return ActivityRecord(id=cursor.lastrowid, name=name, started_at=started_at, ended_at=ended_at)

    def close_activity(self, activity_id: int, ended_at: datetime) -> ActivityRecord:
        row = self._connection.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"No activity with id {activity_id}")

        started_at = _from_iso(row["started_at"])
        validate_activity(name=row["name"], started_at=started_at, ended_at=ended_at)

        self._connection.execute(
            "UPDATE activities SET ended_at = ? WHERE id = ?", (_to_iso(ended_at), activity_id)
        )
        self._connection.commit()
        return ActivityRecord(id=activity_id, name=row["name"], started_at=started_at, ended_at=ended_at)

    def get_current_activity(self) -> Optional[ActivityRecord]:
        row = self._connection.execute(
            "SELECT * FROM activities WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def get_closed_activities(self) -> List[ActivityRecord]:
        rows = self._connection.execute(
            "SELECT * FROM activities WHERE ended_at IS NOT NULL ORDER BY started_at ASC"
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_activities_between(self, start: datetime, end: datetime) -> List[ActivityRecord]:
        rows = self._connection.execute(
            "SELECT * FROM activities WHERE started_at >= ? AND started_at < ? ORDER BY started_at ASC",
            (_to_iso(start), _to_iso(end)),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_today_activities(self, now: Optional[datetime] = None) -> List[ActivityRecord]:
        now = now or datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self.get_activities_between(start, end)

    def get_this_week_activities(self, now: Optional[datetime] = None) -> List[ActivityRecord]:
        now = now or datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = start_of_day - timedelta(days=start_of_day.weekday())  # Monday
        end = start + timedelta(days=7)
        return self.get_activities_between(start, end)

    def close(self) -> None:
        self._connection.close()

    def _row_to_record(self, row: sqlite3.Row) -> ActivityRecord:
        return ActivityRecord(
            id=row["id"],
            name=row["name"],
            started_at=_from_iso(row["started_at"]),
            ended_at=_from_iso(row["ended_at"]) if row["ended_at"] is not None else None,
        )
