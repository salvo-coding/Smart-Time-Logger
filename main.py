import asyncio

from logging_utils.logger import get_logger
from telegram_interface.bot import TelegramInterface
from telegram_interface.config import load_config
from telegram_interface.messages import IncomingMessage


async def placeholder_handler(message: IncomingMessage) -> str:
    """Temporary stand-in for the Module 2+ pipeline (not part of Module 1).
    Replace this once input_parser/activity_manager are implemented."""
    return f"Received: {message.text!r}\nCommand processing is not implemented yet."


def main() -> None:
    config = load_config()
    logger = get_logger("main")
    interface = TelegramInterface(config=config, on_message=placeholder_handler, logger=logger)
    asyncio.run(interface.verify_connection())
    logger.info("Telegram connection verified, starting polling")
    interface.run()


if __name__ == "__main__":
    main()
