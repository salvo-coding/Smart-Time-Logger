from datetime import datetime, timedelta, timezone

import pytest

from activity_manager.manager import Activity, ActivityManager


def make_clock(start: datetime, step: timedelta = timedelta(minutes=1)):
    """Returns a callable clock that advances by `step` on every call,
    so tests get deterministic, strictly increasing timestamps."""
    state = {"now": start - step}

    def _clock() -> datetime:
        state["now"] += step
        return state["now"]

    return _clock


@pytest.fixture
def base_time() -> datetime:
    return datetime(2026, 8, 12, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def manager(base_time) -> ActivityManager:
    return ActivityManager(clock=make_clock(base_time))


# --- normal use cases ---


def test_start_activity_becomes_current(manager, base_time):
    activity = manager.start_activity("Coding")

    assert activity.name == "Coding"
    assert activity.started_at == base_time
    assert activity.ended_at is None
    assert activity.is_active
    assert manager.get_current() == activity


def test_stop_activity_closes_current_and_returns_it(manager):
    manager.start_activity("Coding")
    closed = manager.stop_activity()

    assert closed.name == "Coding"
    assert closed.ended_at is not None
    assert not closed.is_active
    assert manager.get_current() is None


def test_stopped_activity_appears_in_history(manager):
    manager.start_activity("Coding")
    manager.stop_activity()

    history = manager.get_history()
    assert len(history) == 1
    assert history[0].name == "Coding"


def test_multiple_start_stop_cycles_accumulate_history(manager):
    manager.start_activity("Coding")
    manager.stop_activity()
    manager.start_activity("Reading")
    manager.stop_activity()

    history = manager.get_history()
    assert [a.name for a in history] == ["Coding", "Reading"]


# --- auto-close behaviour ---


def test_starting_new_activity_auto_closes_previous(manager):
    first = manager.start_activity("Coding")
    second = manager.start_activity("Reading")

    assert manager.get_current() == second
    history = manager.get_history()
    assert len(history) == 1
    assert history[0].name == "Coding"
    assert history[0].ended_at is not None
    assert history[0].ended_at > first.started_at


def test_auto_close_sets_end_time_before_new_activity_start_time(manager):
    manager.start_activity("Coding")
    manager.start_activity("Reading")

    closed = manager.get_history()[0]
    current = manager.get_current()
    assert closed.ended_at <= current.started_at


# --- invalid inputs ---


def test_start_activity_with_empty_name_raises():
    manager = ActivityManager()
    with pytest.raises(ValueError):
        manager.start_activity("")


def test_start_activity_with_whitespace_only_name_raises():
    manager = ActivityManager()
    with pytest.raises(ValueError):
        manager.start_activity("   ")


def test_start_activity_with_none_name_raises():
    manager = ActivityManager()
    with pytest.raises(ValueError):
        manager.start_activity(None)


def test_activity_name_is_stripped(manager):
    activity = manager.start_activity("  Coding  ")
    assert activity.name == "Coding"


# --- edge cases / failure behaviour ---


def test_stop_activity_with_nothing_active_returns_none(manager):
    assert manager.stop_activity() is None
    assert manager.get_history() == []


def test_get_current_with_nothing_started_returns_none():
    manager = ActivityManager()
    assert manager.get_current() is None


def test_get_history_returns_a_copy_not_internal_state(manager):
    manager.start_activity("Coding")
    manager.stop_activity()

    history = manager.get_history()
    history.append(Activity(name="Fake", started_at=datetime.now(timezone.utc)))

    assert len(manager.get_history()) == 1


def test_activity_is_immutable():
    activity = Activity(name="Coding", started_at=datetime.now(timezone.utc))
    with pytest.raises(Exception):
        activity.name = "Changed"


def test_failed_start_does_not_close_existing_activity(manager):
    manager.start_activity("Coding")
    with pytest.raises(ValueError):
        manager.start_activity("")

    current = manager.get_current()
    assert current is not None
    assert current.name == "Coding"
    assert manager.get_history() == []
