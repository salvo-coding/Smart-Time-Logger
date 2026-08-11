from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from telegram_interface.messages import IncomingMessage


def test_incoming_message_is_immutable():
    message = IncomingMessage(
        telegram_user_id=1,
        chat_id=2,
        message_id=3,
        text="hello",
        received_at=datetime.now(timezone.utc),
    )

    with pytest.raises(FrozenInstanceError):
        message.text = "changed"
