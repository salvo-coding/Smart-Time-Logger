from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_interface.config import TelegramConfig


@pytest.fixture
def dummy_config() -> TelegramConfig:
    return TelegramConfig(bot_token="123456:TEST-TOKEN", authorized_user_id=111)


@pytest.fixture
def make_update():
    def _make_update(
        user_id=111,
        chat_id=999,
        text="hello",
        message_id=1,
        has_photo=False,
    ):
        update = MagicMock()
        update.effective_user.id = user_id
        update.effective_chat.id = chat_id

        message = MagicMock()
        message.message_id = message_id
        message.text = text
        message.reply_text = AsyncMock()
        message.photo = ["fake-photo"] if has_photo else []

        update.message = message
        return update

    return _make_update


@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.error = None
    return ctx
