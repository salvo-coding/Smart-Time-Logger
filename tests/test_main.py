"""
Integration tests for the Module 1 -> Module 2 wiring in main.py: a real
Telegram update flows through TelegramInterface._handle_text into the real
command_handler (which calls the real input_parser), and back out as a
reply - no mocked on_message in between.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from main import HELP_TEXT, command_handler
from telegram_interface.bot import TelegramInterface
from telegram_interface.config import TelegramConfig


@pytest.fixture
def dummy_config() -> TelegramConfig:
    return TelegramConfig(bot_token="123456:TEST-TOKEN", authorized_user_id=111)


@pytest.fixture
def interface(dummy_config) -> TelegramInterface:
    return TelegramInterface(config=dummy_config, on_message=command_handler)


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


@pytest.mark.parametrize(
    "text,expected_reply",
    [
        ("/start", HELP_TEXT),
        ("/start Coding", "Understood: START_ACTIVITY (Coding)\nExecution is not implemented yet (Module 3+)."),
        ("/stop", "Understood: STOP_ACTIVITY\nExecution is not implemented yet (Module 3+)."),
        ("/current", "Understood: SHOW_CURRENT\nExecution is not implemented yet (Module 3+)."),
        ("/today", "Understood: SHOW_TODAY\nExecution is not implemented yet (Module 3+)."),
        ("/week", "Understood: SHOW_WEEK\nExecution is not implemented yet (Module 3+)."),
        ("/help", HELP_TEXT),
        ("banana", "Unrecognized command: 'banana'\nSend /help for a list of commands."),
    ],
)
async def test_full_pipeline_reply_for_authorized_user(interface, context, text, expected_reply):
    update = make_update(user_id=111, text=text)

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with(expected_reply)


async def test_unauthorized_user_never_reaches_the_parser(interface, context):
    update = make_update(user_id=999, text="/start Coding")

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with("You are not authorized to use this bot.")
