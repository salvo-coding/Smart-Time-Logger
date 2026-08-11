from datetime import datetime, timedelta, timezone

from reports.generator import format_duration, generate_report
from database.db import ActivityRecord

UTC = timezone.utc
DAY1 = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)


def record(id_, name, start, end=None):
    return ActivityRecord(id=id_, name=name, started_at=start, ended_at=end)


# --- format_duration: normal and edge cases ---


def test_format_duration_seconds_only():
    assert format_duration(timedelta(seconds=45)) == "45s"


def test_format_duration_minutes_and_seconds():
    assert format_duration(timedelta(minutes=5, seconds=30)) == "5m 30s"


def test_format_duration_hours_and_minutes():
    assert format_duration(timedelta(hours=2, minutes=15)) == "2h 15m"


def test_format_duration_zero():
    assert format_duration(timedelta()) == "0s"


# --- generate_report: normal use cases ---


def test_report_with_no_activities():
    assert generate_report([], "today") == "No activities recorded today."


def test_report_with_a_single_closed_activity():
    activities = [record(1, "Coding", DAY1, DAY1 + timedelta(hours=1))]
    report = generate_report(activities, "today")

    assert "Activities today:" in report
    assert "- Coding: 1h 0m" in report
    assert "Total tracked: 1h 0m" in report
    # Only one closed activity - would be redundant noise.
    assert "Longest session" not in report
    assert "Average duration" not in report


def test_report_with_multiple_closed_activities_includes_analytics():
    activities = [
        record(1, "Coding", DAY1, DAY1 + timedelta(hours=2)),
        record(2, "Reading", DAY1, DAY1 + timedelta(minutes=30)),
    ]
    report = generate_report(activities, "this week")

    assert "Total tracked: 2h 30m" in report
    assert "Longest session: Coding (2h 0m)" in report
    assert "Average duration: 1h 15m" in report


# --- edge cases / failure behaviour ---


def test_report_includes_still_running_activity_without_a_duration():
    activities = [record(1, "Coding", DAY1)]
    report = generate_report(activities, "today")

    assert "- Coding: still running" in report
    assert "Total tracked: 0s" in report


def test_report_with_only_open_activities_omits_analytics_lines():
    activities = [record(1, "Coding", DAY1), record(2, "Reading", DAY1)]
    report = generate_report(activities, "today")

    assert "Longest session" not in report
    assert "Average duration" not in report


def test_report_does_not_mutate_input_list():
    activities = [record(1, "Coding", DAY1, DAY1 + timedelta(hours=1))]
    original = list(activities)

    generate_report(activities, "today")

    assert activities == original
