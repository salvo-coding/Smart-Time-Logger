from datetime import datetime, timedelta, timezone

import pytest

from validation.validators import MAX_REASONABLE_DURATION, ValidationError, validate_activity

NOW = datetime(2026, 8, 12, 9, 0, 0, tzinfo=timezone.utc)


# --- normal use cases ---


def test_valid_activity_with_no_end_time_passes():
    validate_activity(name="Coding", started_at=NOW)


def test_valid_closed_activity_passes():
    validate_activity(name="Coding", started_at=NOW, ended_at=NOW + timedelta(hours=1))


def test_zero_duration_activity_is_valid():
    validate_activity(name="Coding", started_at=NOW, ended_at=NOW)


def test_activity_name_with_surrounding_whitespace_is_valid():
    validate_activity(name="  Coding  ", started_at=NOW)


# --- invalid inputs ---


def test_missing_name_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name=None, started_at=NOW)
    assert any("name" in e.lower() for e in excinfo.value.errors)


def test_empty_name_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="", started_at=NOW)
    assert any("name" in e.lower() for e in excinfo.value.errors)


def test_whitespace_only_name_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="   ", started_at=NOW)
    assert any("name" in e.lower() for e in excinfo.value.errors)


def test_missing_start_timestamp_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="Coding", started_at=None)
    assert any("start timestamp" in e.lower() for e in excinfo.value.errors)


def test_non_datetime_start_timestamp_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="Coding", started_at="not a datetime")
    assert any("datetime" in e.lower() for e in excinfo.value.errors)


def test_non_datetime_end_timestamp_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="Coding", started_at=NOW, ended_at="not a datetime")
    assert any("datetime" in e.lower() for e in excinfo.value.errors)


def test_end_before_start_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="Coding", started_at=NOW, ended_at=NOW - timedelta(minutes=1))
    assert any("end before" in e.lower() for e in excinfo.value.errors)


def test_unreasonably_long_duration_raises():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(
            name="Coding", started_at=NOW, ended_at=NOW + MAX_REASONABLE_DURATION + timedelta(minutes=1)
        )
    assert any("maximum reasonable length" in e.lower() for e in excinfo.value.errors)


def test_duration_exactly_at_the_limit_is_valid():
    validate_activity(name="Coding", started_at=NOW, ended_at=NOW + MAX_REASONABLE_DURATION)


# --- edge cases / failure behaviour ---


def test_multiple_violations_are_all_reported_at_once():
    with pytest.raises(ValidationError) as excinfo:
        validate_activity(name="", started_at=None)

    assert len(excinfo.value.errors) == 2


def test_validation_error_is_a_value_error():
    assert issubclass(ValidationError, ValueError)


def test_validation_never_mutates_or_guesses_inputs():
    # No return value, no side effects - it only raises or does nothing.
    result = validate_activity(name="Coding", started_at=NOW)
    assert result is None
