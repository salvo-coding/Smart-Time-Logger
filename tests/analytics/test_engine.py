from datetime import datetime, timedelta, timezone

import pytest

from analytics.engine import (
    activity_count,
    average_duration,
    daily_totals,
    longest_session,
    summarize,
    total_tracked_time,
)
from database.db import ActivityRecord

UTC = timezone.utc


def record(id_, name, start, end=None):
    return ActivityRecord(id=id_, name=name, started_at=start, ended_at=end)


DAY1 = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)
DAY2 = datetime(2026, 8, 11, 9, 0, tzinfo=UTC)


# --- normal use cases ---


def test_total_tracked_time_sums_closed_activities():
    activities = [
        record(1, "Coding", DAY1, DAY1 + timedelta(hours=1)),
        record(2, "Reading", DAY1, DAY1 + timedelta(minutes=30)),
    ]
    assert total_tracked_time(activities) == timedelta(hours=1, minutes=30)


def test_activity_count_counts_all_activities_including_open():
    activities = [
        record(1, "Coding", DAY1, DAY1 + timedelta(hours=1)),
        record(2, "Reading", DAY1),
    ]
    assert activity_count(activities) == 2


def test_average_duration_of_closed_activities():
    activities = [
        record(1, "Coding", DAY1, DAY1 + timedelta(hours=1)),
        record(2, "Reading", DAY1, DAY1 + timedelta(hours=3)),
    ]
    assert average_duration(activities) == timedelta(hours=2)


def test_longest_session_returns_the_longest_closed_activity():
    short = record(1, "Coding", DAY1, DAY1 + timedelta(minutes=10))
    long = record(2, "Reading", DAY1, DAY1 + timedelta(hours=2))
    assert longest_session([short, long]) == long


def test_daily_totals_groups_by_calendar_day():
    activities = [
        record(1, "Coding", DAY1, DAY1 + timedelta(hours=1)),
        record(2, "Reading", DAY2, DAY2 + timedelta(hours=2)),
    ]
    totals = daily_totals(activities)
    assert totals[DAY1.date()] == timedelta(hours=1)
    assert totals[DAY2.date()] == timedelta(hours=2)


def test_summarize_returns_a_consistent_bundle():
    activities = [
        record(1, "Coding", DAY1, DAY1 + timedelta(hours=1)),
        record(2, "Reading", DAY1, DAY1 + timedelta(hours=3)),
    ]
    summary = summarize(activities)
    assert summary.activity_count == 2
    assert summary.closed_count == 2
    assert summary.total_tracked_time == timedelta(hours=4)
    assert summary.average_duration == timedelta(hours=2)
    assert summary.longest_session.name == "Reading"


# --- edge cases / invalid inputs ---


def test_empty_activity_list_produces_zero_metrics():
    assert total_tracked_time([]) == timedelta()
    assert activity_count([]) == 0
    assert average_duration([]) is None
    assert longest_session([]) is None
    assert daily_totals([]) == {}


def test_open_activity_is_excluded_from_duration_metrics():
    open_activity = record(1, "Coding", DAY1)  # no ended_at - still running
    assert total_tracked_time([open_activity]) == timedelta()
    assert average_duration([open_activity]) is None
    assert longest_session([open_activity]) is None
    assert daily_totals([open_activity]) == {}
    # but it still counts as an activity
    assert activity_count([open_activity]) == 1


def test_mix_of_open_and_closed_only_counts_closed_for_duration():
    closed = record(1, "Coding", DAY1, DAY1 + timedelta(hours=1))
    open_activity = record(2, "Reading", DAY1)
    activities = [closed, open_activity]

    assert total_tracked_time(activities) == timedelta(hours=1)
    assert activity_count(activities) == 2
    assert average_duration(activities) == timedelta(hours=1)


def test_zero_duration_activity_counts_as_closed():
    zero = record(1, "Coding", DAY1, DAY1)
    assert total_tracked_time([zero]) == timedelta()
    assert average_duration([zero]) == timedelta()
    assert longest_session([zero]) == zero


# --- immutability / failure behaviour ---


def test_analytics_does_not_mutate_input_list():
    activities = [record(1, "Coding", DAY1, DAY1 + timedelta(hours=1))]
    original = list(activities)

    summarize(activities)

    assert activities == original


def test_analytics_summary_is_immutable():
    summary = summarize([])
    with pytest.raises(Exception):
        summary.activity_count = 5
