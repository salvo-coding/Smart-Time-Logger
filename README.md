# Smart Time Logger

A private, single-user Telegram bot that logs check-in/check-out activity
events to a local SQLite database, and generates daily/weekly/monthly
reports and charts to help understand where time is actually going.

See `CLAUDE.md` for development principles and workflow.

## Status

Modules 1 (Telegram interface), 2 (input parser), 3 (activity manager), and
4 (validation) are implemented and tested. Modules 5-7 are placeholder
stubs, to be built one at a time. Module 8 (logging) has a minimal
cross-cutting implementation that Module 1 depends on.

Validation is not yet wired into the live bot - there's no database insert
path to protect yet. It's ready for Module 5 to call before persisting a
record; in the meantime, `tests/test_activity_validation_integration.py`
confirms real ActivityManager output passes it.

Activity state is currently in-memory only and is lost on restart - Module
5 (database) will add persistence. `/today` and `/week` reply that they
aren't available yet until that module exists.

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

## Verifying Modules 1, 2 & 3 work

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
9. Send `/today` or `/week` — the bot should reply that it isn't available
   yet (needs Module 5, the database).
10. Send something unrecognized, e.g. `banana` — the bot should reply
    `Unrecognized command: 'banana'` and point to `/help`.
11. Send a photo or sticker — the bot should reply
    "I can only handle text messages right now." and log a WARNING in
    `logs/app.log`.
12. If a second Telegram account is available, message the bot from it —
    the bot should reply "You are not authorized to use this bot." and log
    a WARNING.
13. Inspect `logs/app.log` and confirm the expected INFO/WARNING/ERROR
    events appear, and that your bot token never appears anywhere in the
    file (`grep -i <token> logs/app.log` should return nothing).
