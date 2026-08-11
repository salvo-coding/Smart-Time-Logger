import pytest

from telegram_interface.config import TelegramConfig, load_config
from telegram_interface.exceptions import ConfigError


def _clear_env(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("AUTHORIZED_USER_ID", raising=False)


def test_load_config_reads_valid_env(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "42")

    config = load_config(env_path=str(tmp_path / "nonexistent.env"))

    assert config == TelegramConfig(bot_token="123456:ABCDEF", authorized_user_id=42)


def test_load_config_missing_token_raises_config_error(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setenv("AUTHORIZED_USER_ID", "42")

    with pytest.raises(ConfigError):
        load_config(env_path=str(tmp_path / "nonexistent.env"))


def test_load_config_missing_authorized_user_id_raises_config_error(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")

    with pytest.raises(ConfigError):
        load_config(env_path=str(tmp_path / "nonexistent.env"))


def test_load_config_non_numeric_authorized_user_id_raises_config_error(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEF")
    monkeypatch.setenv("AUTHORIZED_USER_ID", "not-a-number")

    with pytest.raises(ConfigError):
        load_config(env_path=str(tmp_path / "nonexistent.env"))
