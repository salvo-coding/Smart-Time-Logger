class ConfigError(Exception):
    """Raised when required Telegram configuration is missing or malformed."""


class BotStartupError(Exception):
    """Raised when the bot cannot verify its connection to the Telegram API."""
