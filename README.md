# Smart Time Logger

A private, single-user Telegram bot that logs check-in/check-out activity
events to a local SQLite database, and generates daily/weekly/monthly
reports and charts to help understand where time is actually going.

See `CLAUDE.md` for development principles and workflow.

## Status

Module 1 (Telegram interface) is implemented and tested. Modules 2-7 are
placeholder stubs, to be built one at a time. Module 8 (logging) has a
minimal cross-cutting implementation that Module 1 depends on.

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

## Verifying Module 1 works

1. Run the automated test suite:

   ```
   pytest
   ```

   All tests should pass with zero real network calls made.

2. Start the bot (`python main.py`) and open it in Telegram by its
   `@username`.
3. Send `/start` — the bot should reply beginning with `Received: '/start'`
   (command processing is not implemented yet; that's Module 2's job).
4. Send a photo or sticker — the bot should reply
   "I can only handle text messages right now." and log a WARNING in
   `logs/app.log`.
5. If a second Telegram account is available, message the bot from it —
   the bot should reply "You are not authorized to use this bot." and log
   a WARNING.
6. Inspect `logs/app.log` and confirm the expected INFO/WARNING/ERROR
   events appear, and that your bot token never appears anywhere in the
   file (`grep -i <token> logs/app.log` should return nothing).
