from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from logging_utils.logger import get_logger

from .auth import is_authorized
from .config import TelegramConfig
from .exceptions import BotStartupError
from .messages import IncomingMessage, IncomingMessageHandler


class TelegramInterface:
    """Pure communication doorway between Telegram and the rest of the system.

    Authenticates the single authorized user, forwards well-formed text
    messages to an injected handler, and sends replies back. Contains no
    business logic - duration calculation, storage, and analytics live in
    later modules.
    """

    def __init__(
        self,
        config: TelegramConfig,
        on_message: IncomingMessageHandler,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._config = config
        self._on_message = on_message
        self._logger = logger or get_logger(__name__)
        self._application = ApplicationBuilder().token(config.bot_token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        self._application.add_handler(
            MessageHandler(filters.TEXT | filters.COMMAND, self._handle_text)
        )
        self._application.add_handler(
            MessageHandler(~filters.TEXT & ~filters.COMMAND, self._handle_unsupported)
        )
        self._application.add_error_handler(self._handle_error)

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        user_id = user.id if user else None
        chat_id = chat.id if chat else None
        message_id = message.message_id if message else None

        self._logger.info(
            "Telegram message received (user_id=%s, chat_id=%s, message_id=%s)",
            user_id,
            chat_id,
            message_id,
        )

        text = message.text if message else None
        if not text or not text.strip():
            self._logger.warning("Empty message received (user_id=%s)", user_id)
            await self._safe_reply(message, "I didn't receive any text - try /help.")
            return

        if user_id is None or not is_authorized(user_id, self._config.authorized_user_id):
            self._logger.warning("Unauthorized Telegram user rejected (user_id=%s)", user_id)
            await self._safe_reply(message, "You are not authorized to use this bot.")
            return

        self._logger.info("User authenticated (user_id=%s)", user_id)

        incoming = IncomingMessage(
            telegram_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            received_at=datetime.now(timezone.utc),
        )

        try:
            reply_text = await self._on_message(incoming)
        except Exception:
            self._logger.exception("Downstream handler failed while processing message")
            reply_text = "Something went wrong processing your message."

        await self._safe_reply(message, reply_text)

    async def _handle_unsupported(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = user.id if user else None
        self._logger.warning("Unsupported message type received (user_id=%s)", user_id)
        await self._safe_reply(update.message, "I can only handle text messages right now.")

    async def _handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        error = context.error
        self._logger.error(
            "Telegram API request failed: %s",
            type(error).__name__ if error else "unknown error",
        )

    async def _safe_reply(self, message, text: str) -> None:
        if message is None:
            return
        try:
            await message.reply_text(text)
            self._logger.info("Response sent successfully")
        except TelegramError as exc:
            self._logger.error(
                "Telegram API request failed while sending response: %s",
                type(exc).__name__,
            )

    async def verify_connection(self) -> None:
        """Fails fast with BotStartupError if the token is invalid or the
        Telegram API is unreachable, instead of hanging in run_polling()."""
        try:
            await self._application.bot.get_me()
        except TelegramError as exc:
            self._logger.error(
                "Telegram API request failed during startup verification: %s",
                type(exc).__name__,
            )
            raise BotStartupError(
                "Could not verify connection to the Telegram API. "
                "Check your bot token and network connection."
            ) from exc

    def run(self) -> None:
        self._application.run_polling()
