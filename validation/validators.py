"""
Data Validation Module (Module 4)

Responsibility: protection layer that ensures information is valid before it
enters permanent storage or gets used by the system (missing name, missing
or invalid timestamp, end before start, negative/unreasonable duration,
missing required fields).

Must NOT modify activities, write to the database, communicate with
Telegram, guess missing values, or silently correct serious errors - it
only reports what's wrong and lets the caller decide what to do.

Category validation ("unsupported category") is intentionally not
implemented yet: no part of the system produces a category value (Module 2
explicitly deferred it), so there is nothing real to validate against.
Add it here once a category field actually exists in the data model.

Status: implemented and tested.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

MAX_REASONABLE_DURATION = timedelta(hours=24)


class ValidationError(ValueError):
    """Raised when one or more activity fields fail validation. Carries
    every violation found (not just the first) so callers can report all
    problems at once."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_activity(
    name: Optional[str],
    started_at: Optional[datetime],
    ended_at: Optional[datetime] = None,
) -> None:
    """Raise ValidationError if the given activity fields are not fit to
    enter permanent storage or be used elsewhere in the system."""
    errors: List[str] = []

    if not name or not str(name).strip():
        errors.append("Activity name is required.")

    if started_at is None:
        errors.append("A start timestamp is required.")
    elif not isinstance(started_at, datetime):
        errors.append("Start timestamp must be a datetime.")

    if ended_at is not None and not isinstance(ended_at, datetime):
        errors.append("End timestamp must be a datetime.")

    if (
        isinstance(started_at, datetime)
        and isinstance(ended_at, datetime)
    ):
        if ended_at < started_at:
            errors.append("Activity cannot end before it starts.")
        else:
            duration = ended_at - started_at
            if duration > MAX_REASONABLE_DURATION:
                errors.append(
                    "Activity duration exceeds the maximum reasonable length "
                    f"of {MAX_REASONABLE_DURATION}."
                )

    if errors:
        raise ValidationError(errors)
