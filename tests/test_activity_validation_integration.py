"""
Integration check between Module 3 (activity_manager) and Module 4
(validation): confirms that real Activity records produced by
ActivityManager are shaped correctly for validate_activity, before
Module 5 (database) wires the two together for real at insert time.
"""

from datetime import datetime, timedelta, timezone

import pytest

from activity_manager.manager import ActivityManager
from validation.validators import ValidationError, validate_activity


def test_open_activity_from_manager_passes_validation():
    manager = ActivityManager()
    activity = manager.start_activity("Coding")

    validate_activity(name=activity.name, started_at=activity.started_at, ended_at=activity.ended_at)


def test_closed_activity_from_manager_passes_validation():
    manager = ActivityManager()
    manager.start_activity("Coding")
    closed = manager.stop_activity()

    validate_activity(name=closed.name, started_at=closed.started_at, ended_at=closed.ended_at)


def test_auto_closed_activity_from_manager_passes_validation():
    manager = ActivityManager()
    manager.start_activity("Coding")
    manager.start_activity("Reading")
    closed = manager.get_history()[0]

    validate_activity(name=closed.name, started_at=closed.started_at, ended_at=closed.ended_at)


def test_manager_rejects_bad_input_before_validation_module_even_runs():
    manager = ActivityManager()
    with pytest.raises(ValueError):
        manager.start_activity("")
