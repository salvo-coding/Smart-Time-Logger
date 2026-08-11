"""
Reports & Charts Module (Module 7)

Responsibility: turn analytics output into human-readable daily/weekly/
monthly reports (activities listed, total tracked time, longest session,
average duration for a given period).

Must NOT modify raw time records, perform core duration calculations
itself (that's Module 6's job), interact directly with SQLite, or make
behavioural judgments.

Two things named in this module's original scope are intentionally not
implemented:

- Chart images: would need a new dependency (e.g. matplotlib) and a way
  for telegram_interface to send photos, not just text - a real scope and
  architecture decision left for a future pass rather than made silently
  here.
- Category-based breakdowns ("time by category", "productive vs
  non-productive", "weekly category comparison"): no part of the system
  has a category field - deferred back in Module 2, same reasoning as
  Modules 4 and 6.

Status: implemented and tested.
"""

from __future__ import annotations

from datetime import timedelta
from typing import List

from analytics.engine import summarize
from database.db import ActivityRecord


def format_duration(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def generate_report(activities: List[ActivityRecord], label: str) -> str:
    """Human-readable summary of activities for a period, e.g.
    label="today", "this week", "this month"."""
    if not activities:
        return f"No activities recorded {label}."

    lines = [f"Activities {label}:"]
    for activity in activities:
        if activity.ended_at is not None:
            duration = activity.ended_at - activity.started_at
            lines.append(f"- {activity.name}: {format_duration(duration)}")
        else:
            lines.append(f"- {activity.name}: still running")

    summary = summarize(activities)
    lines.append(f"Total tracked: {format_duration(summary.total_tracked_time)}")
    if summary.closed_count > 1:
        longest = summary.longest_session
        longest_duration = longest.ended_at - longest.started_at
        lines.append(f"Longest session: {longest.name} ({format_duration(longest_duration)})")
        lines.append(f"Average duration: {format_duration(summary.average_duration)}")
    return "\n".join(lines)
