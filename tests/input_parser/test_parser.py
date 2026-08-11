from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from input_parser.parser import Command, CommandType, parse_command
from telegram_interface.messages import IncomingMessage


def make_message(text: str) -> IncomingMessage:
    return IncomingMessage(
        telegram_user_id=111,
        chat_id=999,
        message_id=1,
        text=text,
        received_at=datetime.now(timezone.utc),
    )


# --- normal use cases ---


def test_start_with_activity_name():
    command = parse_command(make_message("/start Coding"))
    assert command == Command(type=CommandType.START_ACTIVITY, activity_name="Coding", raw_text="/start Coding")


def test_start_with_multi_word_activity_name():
    command = parse_command(make_message("/start Deep Work Session"))
    assert command.type == CommandType.START_ACTIVITY
    assert command.activity_name == "Deep Work Session"


def test_stop():
    command = parse_command(make_message("/stop"))
    assert command.type == CommandType.STOP_ACTIVITY
    assert command.activity_name is None


def test_current():
    assert parse_command(make_message("/current")).type == CommandType.SHOW_CURRENT


def test_today():
    assert parse_command(make_message("/today")).type == CommandType.SHOW_TODAY


def test_week():
    assert parse_command(make_message("/week")).type == CommandType.SHOW_WEEK


def test_month():
    assert parse_command(make_message("/month")).type == CommandType.SHOW_MONTH


def test_help():
    assert parse_command(make_message("/help")).type == CommandType.HELP


# --- edge cases ---


def test_bare_start_with_no_activity_name_falls_back_to_help():
    command = parse_command(make_message("/start"))
    assert command.type == CommandType.HELP


def test_start_with_only_whitespace_after_falls_back_to_help():
    command = parse_command(make_message("/start    "))
    assert command.type == CommandType.HELP


def test_commands_are_case_insensitive():
    assert parse_command(make_message("/START Coding")).type == CommandType.START_ACTIVITY
    assert parse_command(make_message("/Stop")).type == CommandType.STOP_ACTIVITY


def test_surrounding_whitespace_is_ignored():
    command = parse_command(make_message("   /stop   "))
    assert command.type == CommandType.STOP_ACTIVITY


def test_extra_args_on_no_arg_commands_are_ignored():
    command = parse_command(make_message("/stop right now"))
    assert command.type == CommandType.STOP_ACTIVITY


def test_bot_mention_suffix_is_stripped():
    command = parse_command(make_message("/start@smarttimeloggerbot Coding"))
    assert command.type == CommandType.START_ACTIVITY
    assert command.activity_name == "Coding"


def test_bot_mention_suffix_stripped_on_no_arg_command():
    command = parse_command(make_message("/stop@smarttimeloggerbot"))
    assert command.type == CommandType.STOP_ACTIVITY


def test_extra_internal_whitespace_before_activity_name_is_trimmed():
    command = parse_command(make_message("/start   Coding"))
    assert command.activity_name == "Coding"


# --- invalid inputs / failure behaviour ---


def test_unrecognized_slash_command_is_unknown():
    command = parse_command(make_message("/frobnicate"))
    assert command.type == CommandType.UNKNOWN
    assert command.raw_text == "/frobnicate"


def test_plain_text_without_slash_is_unknown():
    command = parse_command(make_message("hello there"))
    assert command.type == CommandType.UNKNOWN


def test_empty_text_is_unknown():
    command = parse_command(make_message(""))
    assert command.type == CommandType.UNKNOWN


def test_whitespace_only_text_is_unknown():
    command = parse_command(make_message("   "))
    assert command.type == CommandType.UNKNOWN


# --- Command properties ---


def test_command_is_immutable():
    command = Command(type=CommandType.HELP)
    with pytest.raises(FrozenInstanceError):
        command.type = CommandType.STOP_ACTIVITY
