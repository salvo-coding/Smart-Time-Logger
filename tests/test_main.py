"""
Integration tests for the Module 1 -> Module 2 -> Module 3 wiring in
main.py: a real Telegram update flows through TelegramInterface._handle_text
into the real command_handler (which calls the real input_parser and a real
ActivityManager), and back out as a reply - no mocked on_message in between.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from activity_manager.manager import ActivityManager
from main import HELP_TEXT, NOT_YET_AVAILABLE, create_command_handler
from telegram_interface.bot import TelegramInterface
from telegram_interface.config import TelegramConfig


@pytest.fixture
def dummy_config() -> TelegramConfig:
    return TelegramConfig(bot_token="123456:TEST-TOKEN", authorized_user_id=111)


@pytest.fixture
def manager() -> ActivityManager:
    return ActivityManager()


@pytest.fixture
def interface(dummy_config, manager) -> TelegramInterface:
    return TelegramInterface(config=dummy_config, on_message=create_command_handler(manager))


@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.error = None
    return ctx


def make_update(user_id=111, chat_id=999, text="hello", message_id=1):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = chat_id

    message = MagicMock()
    message.message_id = message_id
    message.text = text
    message.reply_text = AsyncMock()

    update.message = message
    return update


# --- commands with static replies ---


@pytest.mark.parametrize(
    "text,expected_reply",
    [
        ("/start", HELP_TEXT),
        ("/help", HELP_TEXT),
        ("banana", "Unrecognized command: 'banana'\nSend /help for a list of commands."),
        ("/today", NOT_YET_AVAILABLE),
        ("/week", NOT_YET_AVAILABLE),
    ],
)
async def test_static_replies(interface, context, text, expected_reply):
    update = make_update(user_id=111, text=text)

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with(expected_reply)


# --- activity_manager-backed commands ---


async def test_start_activity_starts_and_replies(interface, context, manager):
    update = make_update(text="/start Coding")

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with("Started 'Coding'.")
    assert manager.get_current().name == "Coding"


async def test_starting_new_activity_auto_closes_previous_and_mentions_it(interface, context):
    await interface._handle_text(make_update(text="/start Coding"), context)
    update = make_update(text="/start Reading")

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with("Stopped 'Coding'. Started 'Reading'.")


async def test_stop_with_nothing_active_replies_accordingly(interface, context):
    update = make_update(text="/stop")

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with("No activity is currently running.")


async def test_stop_after_start_reports_tracked_duration(interface, context):
    await interface._handle_text(make_update(text="/start Coding"), context)
    update = make_update(text="/stop")

    await interface._handle_text(update, context)

    reply = update.message.reply_text.await_args.args[0]
    assert reply.startswith("Stopped 'Coding' (tracked")


async def test_current_with_nothing_active_replies_accordingly(interface, context):
    update = make_update(text="/current")

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with("No activity is currently running.")


async def test_current_after_start_reports_activity_and_elapsed_time(interface, context):
    await interface._handle_text(make_update(text="/start Coding"), context)
    update = make_update(text="/current")

    await interface._handle_text(update, context)

    reply = update.message.reply_text.await_args.args[0]
    assert reply.startswith("Currently tracking 'Coding'")


# --- authorization boundary ---


async def test_unauthorized_user_never_reaches_the_parser(interface, context, manager):
    update = make_update(user_id=999, text="/start Coding")

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with("You are not authorized to use this bot.")
    assert manager.get_current() is None
