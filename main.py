import asyncio

from input_parser.parser import Command, CommandType, parse_command
from logging_utils.logger import get_logger
from telegram_interface.bot import TelegramInterface
from telegram_interface.config import load_config
from telegram_interface.messages import IncomingMessage

HELP_TEXT = (
    "Smart Time Logger commands:\n"
    "/start <activity name> - start tracking an activity\n"
    "/stop - stop the current activity\n"
    "/current - show the current activity\n"
    "/today - show today's activities\n"
    "/week - show this week's activities\n"
    "/help - show this message"
)


async def command_handler(message: IncomingMessage) -> str:
    """Temporary stand-in for the Module 3+ pipeline (not part of Module 2).
    Parses the command but cannot act on it until activity_manager and
    database are implemented."""
    command: Command = parse_command(message)

    if command.type == CommandType.HELP:
        return HELP_TEXT
    if command.type == CommandType.UNKNOWN:
        return f"Unrecognized command: {command.raw_text!r}\nSend /help for a list of commands."

    detail = f" ({command.activity_name})" if command.activity_name else ""
    return f"Understood: {command.type.name}{detail}\nExecution is not implemented yet (Module 3+)."


def main() -> None:
    config = load_config()
    logger = get_logger("main")
    interface = TelegramInterface(config=config, on_message=command_handler, logger=logger)
    asyncio.run(interface.verify_connection())
    logger.info("Telegram connection verified, starting polling")
    interface.run()


if __name__ == "__main__":
    main()
