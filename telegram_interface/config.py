from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .exceptions import ConfigError


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    authorized_user_id: int


def load_config(env_path: str | None = None) -> TelegramConfig:
    load_dotenv(dotenv_path=env_path)

    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ConfigError("BOT_TOKEN is missing or empty. Set it in your .env file.")

    raw_user_id = os.environ.get("AUTHORIZED_USER_ID", "").strip()
    if not raw_user_id:
        raise ConfigError(
            "AUTHORIZED_USER_ID is missing or empty. Set it in your .env file."
        )

    try:
        authorized_user_id = int(raw_user_id)
    except ValueError as exc:
        raise ConfigError(
            "AUTHORIZED_USER_ID must be a numeric Telegram user ID."
        ) from exc

    return TelegramConfig(bot_token=bot_token, authorized_user_id=authorized_user_id)
