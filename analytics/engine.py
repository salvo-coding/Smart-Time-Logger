"""
Analytics Engine Module (Module 6)

Responsibility: turn raw activity records into useful metrics - total
tracked time, number of activities, average activity duration, longest
session, and daily totals.

Must NOT change historical records, communicate with Telegram directly,
generate chart images itself, guess missing time, or alter activity
categories without instruction.

Category-dependent metrics ("time by category", "most common category",
"productive/wasted time") are intentionally not implemented yet: no part
of the system produces a category value - Module 2 explicitly deferred it,
and neither ActivityRecord (Module 5) nor validate_activity (Module 4) has
a category field. Add them here once a category field actually exists in
the data model.

Only closed activities (ended_at is not None) contribute to
duration-based metrics - an activity still in progress has no known end
time, and guessing one is explicitly out of scope for this module.

Status: implemented and tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from database.db import ActivityRecord


def _closed(activities: List[ActivityRecord]) -> List[ActivityRecord]:
    return [activity for activity in activities if activity.ended_at is not None]


def _duration(activity: ActivityRecord) -> timedelta:
    return activity.ended_at - activity.started_at


def total_tracked_time(activities: List[ActivityRecord]) -> timedelta:
    return sum((_duration(a) for a in _closed(activities)), timedelta())


def activity_count(activities: List[ActivityRecord]) -> int:
    return len(activities)


def average_duration(activities: List[ActivityRecord]) -> Optional[timedelta]:
    closed = _closed(activities)
    if not closed:
        return None
    return total_tracked_time(activities) / len(closed)


def longest_session(activities: List[ActivityRecord]) -> Optional[ActivityRecord]:
    closed = _closed(activities)
    if not closed:
        return None
    return max(closed, key=_duration)


def daily_totals(activities: List[ActivityRecord]) -> Dict[date, timedelta]:
    """Total tracked time per calendar day (UTC date of started_at)."""
    totals: Dict[date, timedelta] = {}
    for activity in _closed(activities):
        day = activity.started_at.date()
        totals[day] = totals.get(day, timedelta()) + _duration(activity)
    return totals


@dataclass(frozen=True)
class AnalyticsSummary:
    activity_count: int
    closed_count: int
    total_tracked_time: timedelta
    average_duration: Optional[timedelta]
    longest_session: Optional[ActivityRecord]
    daily_totals: Dict[date, timedelta]


def summarize(activities: List[ActivityRecord]) -> AnalyticsSummary:
    closed = _closed(activities)
    return AnalyticsSummary(
        activity_count=len(activities),
        closed_count=len(closed),
        total_tracked_time=total_tracked_time(activities),
        average_duration=average_duration(activities),
        longest_session=longest_session(activities),
        daily_totals=daily_totals(activities),
    )
