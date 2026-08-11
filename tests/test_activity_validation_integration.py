"""
Integration check across Module 3 (activity_manager), Module 4
(validation), and Module 5 (database): confirms that ActivityRecords
surfaced by ActivityManager - which is itself backed by Database, and
Database validates every write via validate_activity() - still pass
validation when re-checked directly. This is now a real, wired-together
pipeline rather than just compatible shapes.
"""

from datetime import datetime, timezone

import pytest

from activity_manager.manager import ActivityManager
from database.db import Database
from validation.validators import validate_activity


@pytest.fixture
def manager():
    database = Database(db_path=":memory:")
    yield ActivityManager(database=database)
    database.close()


def test_open_activity_from_manager_passes_validation(manager):
    activity = manager.start_activity("Coding")

    validate_activity(name=activity.name, started_at=activity.started_at, ended_at=activity.ended_at)


def test_closed_activity_from_manager_passes_validation(manager):
    manager.start_activity("Coding")
    closed = manager.stop_activity()

    validate_activity(name=closed.name, started_at=closed.started_at, ended_at=closed.ended_at)


def test_auto_closed_activity_from_manager_passes_validation(manager):
    manager.start_activity("Coding")
    manager.start_activity("Reading")
    closed = manager.get_history()[0]

    validate_activity(name=closed.name, started_at=closed.started_at, ended_at=closed.ended_at)


def test_manager_rejects_bad_input_before_it_ever_reaches_the_database(manager):
    with pytest.raises(ValueError):
        manager.start_activity("")
