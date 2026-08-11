# Smart Time Logger

A private, single-user Telegram bot that logs check-in/check-out activity
events to a local SQLite database, and generates daily/weekly/monthly
reports and charts to help understand where time is actually going.

See `CLAUDE.md` for development principles and workflow.

## Status

Modules 1 (Telegram interface), 2 (input parser), 3 (activity manager), 4
(validation), and 5 (database) are implemented and tested. Modules 6-7 are
placeholder stubs, to be built one at a time. Module 8 (logging) has a
minimal cross-cutting implementation that Module 1 depends on.

Activity state now persists to a local SQLite database (`data/time_logger.db`,
gitignored) and survives a bot restart. `ActivityManager` no longer holds
state in memory itself - it delegates all reads/writes to `Database`, which
validates every record through Module 4 before it's written. `/today` and
`/week` now return real data.

Modules 6 (analytics) and 7 (reports/charts) are not built yet, so `/today`
and `/week` show a simple list-and-total, not calculated metrics or charts.

## Setup

### 1. Install dependencies

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Create a Telegram bot

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts (choose a name and a username
   ending in `bot`).
3. BotFather will reply with a bot token that looks like
   `123456789:ABCDEFghijklmnopqrstuvwxyz`. Copy it.

### 3. Find your Telegram user ID

1. Open Telegram and search for **@userinfobot**.
2. Send it any message. It replies with your numeric user ID.
3. This is the only ID the bot will accept messages from.

### 4. Configure environment variables

```
cp .env.example .env
```

Edit `.env` and fill in the values from steps 2 and 3:

```
BOT_TOKEN=<your bot token>
AUTHORIZED_USER_ID=<your numeric Telegram user ID>
```

`.env` is gitignored and must never be committed.

## Running the bot

```
source .venv/bin/activate
python main.py
```

On startup the bot verifies its connection to the Telegram API before
polling. If the token is wrong, it fails fast with a clear error instead
of hanging.

## Verifying Modules 1, 2, 3, 4 & 5 work

1. Run the automated test suite:

   ```
   pytest
   ```

   All tests should pass with zero real network calls made.

2. Start the bot (`python main.py`) and open it in Telegram by its
   `@username`.
3. Send `/start` (no activity name) — the bot should reply with the help
   text listing all commands.
4. Send `/start Coding` — the bot should reply `Started 'Coding'.`
5. Send `/current` — the bot should reply
   `Currently tracking 'Coding' (... so far).`
6. Send `/start Reading` — the bot should reply
   `Stopped 'Coding'. Started 'Reading'.` (auto-close of the previous
   activity).
7. Send `/stop` — the bot should reply `Stopped 'Reading' (tracked ...).`
8. Send `/stop` again — the bot should reply
   `No activity is currently running.`
9. Send `/today` — the bot should list both activities with durations and
   a total.
10. Stop the bot (Ctrl+C) and start it again with `python main.py`, then
    send `/today` again — the same activities should still be there,
    confirming persistence across a restart.
11. Send something unrecognized, e.g. `banana` — the bot should reply
    `Unrecognized command: 'banana'` and point to `/help`.
12. Send a photo or sticker — the bot should reply
    "I can only handle text messages right now." and log a WARNING in
    `logs/app.log`.
13. If a second Telegram account is available, message the bot from it —
    the bot should reply "You are not authorized to use this bot." and log
    a WARNING.
14. Inspect `logs/app.log` and confirm the expected INFO/WARNING/ERROR
    events appear, and that your bot token never appears anywhere in the
    file (`grep -i <token> logs/app.log` should return nothing).
