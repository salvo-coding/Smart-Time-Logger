from datetime import datetime, timezone

from activity_manager.manager import ActivityManager
from database.db import Database
from input_parser.parser import Command, CommandType, parse_command
from logging_utils.logger import get_logger
from reports.generator import format_duration, generate_report
from telegram_interface.bot import TelegramInterface
from telegram_interface.config import load_config
from telegram_interface.messages import IncomingMessage, IncomingMessageHandler

HELP_TEXT = (
    "Smart Time Logger commands:\n"
    "/start <activity name> - start tracking an activity\n"
    "/stop - stop the current activity\n"
    "/current - show the current activity\n"
    "/today - show today's activities\n"
    "/week - show this week's activities\n"
    "/month - show this month's activities\n"
    "/help - show this message"
)


def create_command_handler(manager: ActivityManager) -> IncomingMessageHandler:
    """Builds the on_message handler for TelegramInterface, closing over an
    ActivityManager instance shared across all messages for this bot run."""

    async def command_handler(message: IncomingMessage) -> str:
        command: Command = parse_command(message)

        if command.type == CommandType.HELP:
            return HELP_TEXT

        if command.type == CommandType.UNKNOWN:
            return f"Unrecognized command: {command.raw_text!r}\nSend /help for a list of commands."

        if command.type == CommandType.START_ACTIVITY:
            previous = manager.get_current()
            activity = manager.start_activity(command.activity_name)
            reply = f"Started '{activity.name}'."
            if previous is not None:
                reply = f"Stopped '{previous.name}'. " + reply
            return reply

        if command.type == CommandType.STOP_ACTIVITY:
            closed = manager.stop_activity()
            if closed is None:
                return "No activity is currently running."
            duration = closed.ended_at - closed.started_at
            return f"Stopped '{closed.name}' (tracked {format_duration(duration)})."

        if command.type == CommandType.SHOW_CURRENT:
            current = manager.get_current()
            if current is None:
                return "No activity is currently running."
            elapsed = datetime.now(timezone.utc) - current.started_at
            return f"Currently tracking '{current.name}' ({format_duration(elapsed)} so far)."

        if command.type == CommandType.SHOW_TODAY:
            return generate_report(manager.get_today(), "today")

        if command.type == CommandType.SHOW_WEEK:
            return generate_report(manager.get_this_week(), "this week")

        if command.type == CommandType.SHOW_MONTH:
            return generate_report(manager.get_this_month(), "this month")

        raise AssertionError(f"Unhandled command type: {command.type}")

    return command_handler


def main() -> None:
    config = load_config()
    logger = get_logger("main")
    database = Database()
    manager = ActivityManager(database=database)
    interface = TelegramInterface(
        config=config, on_message=create_command_handler(manager), logger=logger
    )
    logger.info("Starting polling")
    interface.run()


if __name__ == "__main__":
    main()
