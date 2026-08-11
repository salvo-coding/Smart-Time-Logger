from datetime import datetime, timedelta, timezone

import pytest

from database.db import ActivityRecord, Database
from validation.validators import ValidationError

UTC = timezone.utc


@pytest.fixture
def db():
    database = Database(db_path=":memory:")
    yield database
    database.close()


# --- normal use cases ---


def test_insert_activity_returns_a_record_with_an_id(db):
    started = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)
    record = db.insert_activity(name="Coding", started_at=started)

    assert record.id is not None
    assert record.name == "Coding"
    assert record.started_at == started
    assert record.ended_at is None
    assert record.is_active


def test_get_current_activity_returns_the_open_one(db):
    started = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)
    record = db.insert_activity(name="Coding", started_at=started)

    assert db.get_current_activity() == record


def test_close_activity_sets_end_time_and_clears_current(db):
    started = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)
    ended = started + timedelta(hours=1)
    record = db.insert_activity(name="Coding", started_at=started)

    closed = db.close_activity(record.id, ended_at=ended)

    assert closed.ended_at == ended
    assert not closed.is_active
    assert db.get_current_activity() is None


def test_closed_activities_appear_in_get_closed_activities(db):
    started = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)
    record = db.insert_activity(name="Coding", started_at=started)
    db.close_activity(record.id, ended_at=started + timedelta(minutes=30))

    closed = db.get_closed_activities()
    assert len(closed) == 1
    assert closed[0].name == "Coding"


def test_data_persists_across_separate_connections_to_the_same_file(tmp_path):
    db_path = str(tmp_path / "time_logger.db")
    started = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)

    first = Database(db_path=db_path)
    first.insert_activity(name="Coding", started_at=started)
    first.close()

    second = Database(db_path=db_path)
    current = second.get_current_activity()
    second.close()

    assert current is not None
    assert current.name == "Coding"


# --- invalid inputs ---


def test_insert_activity_with_empty_name_raises_validation_error(db):
    with pytest.raises(ValidationError):
        db.insert_activity(name="", started_at=datetime(2026, 8, 12, 9, 0, tzinfo=UTC))


def test_insert_activity_with_end_before_start_raises_validation_error(db):
    started = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)
    with pytest.raises(ValidationError):
        db.insert_activity(name="Coding", started_at=started, ended_at=started - timedelta(minutes=5))


def test_close_activity_with_unknown_id_raises_value_error(db):
    with pytest.raises(ValueError):
        db.close_activity(999, ended_at=datetime(2026, 8, 12, 9, 0, tzinfo=UTC))


def test_invalid_insert_does_not_write_a_row(db):
    with pytest.raises(ValidationError):
        db.insert_activity(name="", started_at=datetime(2026, 8, 12, 9, 0, tzinfo=UTC))

    assert db.get_current_activity() is None
    assert db.get_closed_activities() == []


# --- edge cases ---


def test_get_current_activity_with_empty_database_returns_none(db):
    assert db.get_current_activity() is None


def test_today_activities_excludes_yesterday_and_tomorrow(db):
    now = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    db.insert_activity(name="Yesterday", started_at=yesterday, ended_at=yesterday + timedelta(minutes=10))
    db.insert_activity(name="Today", started_at=now, ended_at=now + timedelta(minutes=10))
    db.insert_activity(name="Tomorrow", started_at=tomorrow, ended_at=tomorrow + timedelta(minutes=10))

    today_activities = db.get_today_activities(now=now)
    assert [a.name for a in today_activities] == ["Today"]


def test_this_week_activities_starts_on_monday(db):
    # 2026-08-12 is a Wednesday.
    wednesday = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
    last_monday = datetime(2026, 8, 10, 8, 0, tzinfo=UTC)
    previous_sunday = datetime(2026, 8, 9, 8, 0, tzinfo=UTC)

    db.insert_activity(name="PreviousWeek", started_at=previous_sunday, ended_at=previous_sunday + timedelta(minutes=5))
    db.insert_activity(name="ThisWeek", started_at=last_monday, ended_at=last_monday + timedelta(minutes=5))

    this_week = db.get_this_week_activities(now=wednesday)
    assert [a.name for a in this_week] == ["ThisWeek"]


def test_this_month_activities_excludes_previous_and_next_month(db):
    mid_august = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    end_of_july = datetime(2026, 7, 31, 23, 0, tzinfo=UTC)
    start_of_september = datetime(2026, 9, 1, 0, 30, tzinfo=UTC)

    db.insert_activity(name="July", started_at=end_of_july, ended_at=end_of_july + timedelta(minutes=5))
    db.insert_activity(name="August", started_at=mid_august, ended_at=mid_august + timedelta(minutes=5))
    db.insert_activity(
        name="September", started_at=start_of_september, ended_at=start_of_september + timedelta(minutes=5)
    )

    this_month = db.get_this_month_activities(now=mid_august)
    assert [a.name for a in this_month] == ["August"]


def test_this_month_handles_december_year_rollover(db):
    mid_december = datetime(2026, 12, 15, 12, 0, tzinfo=UTC)
    start_of_january = datetime(2027, 1, 1, 0, 30, tzinfo=UTC)

    db.insert_activity(name="December", started_at=mid_december, ended_at=mid_december + timedelta(minutes=5))
    db.insert_activity(
        name="January", started_at=start_of_january, ended_at=start_of_january + timedelta(minutes=5)
    )

    this_month = db.get_this_month_activities(now=mid_december)
    assert [a.name for a in this_month] == ["December"]


def test_activity_record_is_immutable():
    record = ActivityRecord(id=1, name="Coding", started_at=datetime.now(UTC))
    with pytest.raises(Exception):
        record.ended_at = datetime.now(UTC)
