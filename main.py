from datetime import datetime, timedelta, timezone
from typing import List

from activity_manager.manager import ActivityManager
from analytics.engine import summarize
from database.db import ActivityRecord, Database
from input_parser.parser import Command, CommandType, parse_command
from logging_utils.logger import get_logger
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
    "/help - show this message"
)


def _format_duration(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _format_activity_list(activities: List[ActivityRecord], label: str) -> str:
    if not activities:
        return f"No activities recorded {label}."

    lines = [f"Activities {label}:"]
    for activity in activities:
        if activity.ended_at is not None:
            duration = activity.ended_at - activity.started_at
            lines.append(f"- {activity.name}: {_format_duration(duration)}")
        else:
            lines.append(f"- {activity.name}: still running")

    summary = summarize(activities)
    lines.append(f"Total tracked: {_format_duration(summary.total_tracked_time)}")
    if summary.closed_count > 1:
        longest = summary.longest_session
        longest_duration = longest.ended_at - longest.started_at
        lines.append(f"Longest session: {longest.name} ({_format_duration(longest_duration)})")
        lines.append(f"Average duration: {_format_duration(summary.average_duration)}")
    return "\n".join(lines)


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
            return f"Stopped '{closed.name}' (tracked {_format_duration(duration)})."

        if command.type == CommandType.SHOW_CURRENT:
            current = manager.get_current()
            if current is None:
                return "No activity is currently running."
            elapsed = datetime.now(timezone.utc) - current.started_at
            return f"Currently tracking '{current.name}' ({_format_duration(elapsed)} so far)."

        if command.type == CommandType.SHOW_TODAY:
            return _format_activity_list(manager.get_today(), "today")

        if command.type == CommandType.SHOW_WEEK:
            return _format_activity_list(manager.get_this_week(), "this week")

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
