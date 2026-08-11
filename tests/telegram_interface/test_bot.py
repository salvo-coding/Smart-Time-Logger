import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.error import InvalidToken, NetworkError, TimedOut

from telegram_interface.bot import TelegramInterface
from telegram_interface.exceptions import BotStartupError
from telegram_interface.messages import IncomingMessage


@pytest.fixture
def on_message():
    return AsyncMock(return_value="handled")


@pytest.fixture
def interface(dummy_config, on_message):
    return TelegramInterface(config=dummy_config, on_message=on_message)


async def test_authorized_text_message_is_forwarded_and_replied(
    interface, make_update, context, on_message, caplog
):
    update = make_update(user_id=111, text="/start")

    with caplog.at_level(logging.INFO):
        await interface._handle_text(update, context)

    on_message.assert_awaited_once()
    forwarded = on_message.await_args.args[0]
    assert isinstance(forwarded, IncomingMessage)
    assert forwarded.telegram_user_id == 111
    assert forwarded.text == "/start"
    update.message.reply_text.assert_awaited_once_with("handled")
    assert "message received" in caplog.text.lower()
    assert "user authenticated" in caplog.text.lower()
    assert "response sent" in caplog.text.lower()


async def test_unauthorized_user_is_rejected_and_not_forwarded(
    interface, make_update, context, on_message, caplog
):
    update = make_update(user_id=999, text="hello")

    with caplog.at_level(logging.WARNING):
        await interface._handle_text(update, context)

    on_message.assert_not_awaited()
    update.message.reply_text.assert_awaited_once_with(
        "You are not authorized to use this bot."
    )
    assert "unauthorized" in caplog.text.lower()


async def test_empty_message_does_not_crash_or_forward(
    interface, make_update, context, on_message
):
    update = make_update(text="   ")

    await interface._handle_text(update, context)

    on_message.assert_not_awaited()
    update.message.reply_text.assert_awaited_once()


async def test_unsupported_content_photo_is_handled(
    interface, make_update, context, on_message, caplog
):
    update = make_update(has_photo=True, text=None)

    with caplog.at_level(logging.WARNING):
        await interface._handle_unsupported(update, context)

    on_message.assert_not_awaited()
    update.message.reply_text.assert_awaited_once_with(
        "I can only handle text messages right now."
    )
    assert "unsupported" in caplog.text.lower()


async def test_reply_send_failure_is_logged_not_raised(
    interface, make_update, context, on_message, caplog
):
    update = make_update()
    update.message.reply_text.side_effect = NetworkError("boom")

    with caplog.at_level(logging.ERROR):
        await interface._handle_text(update, context)

    assert "telegram api request failed" in caplog.text.lower()


async def test_error_handler_logs_network_error_without_raising(interface, context, caplog):
    context.error = TimedOut()

    with caplog.at_level(logging.ERROR):
        await interface._handle_error(None, context)

    assert "telegram api request failed" in caplog.text.lower()


def test_run_calls_run_polling(interface, monkeypatch):
    mock_run_polling = MagicMock()
    monkeypatch.setattr(interface._application, "run_polling", mock_run_polling)

    interface.run()

    mock_run_polling.assert_called_once()


def test_run_invalid_token_raises_bot_startup_error(interface, dummy_config, caplog, monkeypatch):
    monkeypatch.setattr(
        interface._application, "run_polling", MagicMock(side_effect=InvalidToken("bad token"))
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BotStartupError):
            interface.run()

    assert dummy_config.bot_token not in caplog.text


def test_run_network_error_raises_bot_startup_error(interface, monkeypatch):
    monkeypatch.setattr(
        interface._application, "run_polling", MagicMock(side_effect=NetworkError("unreachable"))
    )

    with pytest.raises(BotStartupError):
        interface.run()


async def test_downstream_handler_exception_does_not_crash_bot(
    interface, make_update, context, on_message
):
    on_message.side_effect = ValueError("boom")
    update = make_update()

    await interface._handle_text(update, context)

    update.message.reply_text.assert_awaited_once_with(
        "Something went wrong processing your message."
    )


async def test_two_sequential_messages_handled_independently(
    interface, make_update, context, on_message
):
    update_a = make_update(user_id=111, chat_id=1, message_id=10, text="first")
    update_b = make_update(user_id=111, chat_id=1, message_id=11, text="second")

    await interface._handle_text(update_a, context)
    await interface._handle_text(update_b, context)

    assert on_message.await_count == 2
    first_msg = on_message.await_args_list[0].args[0]
    second_msg = on_message.await_args_list[1].args[0]
    assert first_msg.text == "first"
    assert second_msg.text == "second"
    assert first_msg.message_id == 10
    assert second_msg.message_id == 11
