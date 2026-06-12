# Notes

A personal Markdown notes app. Keep notes, tag them, search them, and pin some to a date so you can browse them on a calendar.

Each user has their own private space. Every note is a Markdown document with a live preview while editing.

## What's inside

- Log in / register (single-user-per-account — no sharing).
- CRUD for notes with Markdown preview.
- Tags with filtering.
- Full-text search across title and body.
- Optional date on a note + a calendar view.

## Run it

Requirements: Docker with Compose.

```bash
make up          # start db + backend + frontend
make seed        # (optional) create a demo user with a few notes
```

Then open <http://localhost:5173>.

Demo credentials (after `make seed`):

- **username:** `demo`
- **password:** `demo1234`

## Telegram reminders

Telegram is optional for local development. Without a bot token the app, seed, tests, and
worker still start; Telegram polling and message delivery are skipped.

To try reminders locally, create a Telegram bot and set:

```bash
export TELEGRAM_BOT_TOKEN=123:abc
export TELEGRAM_BOT_USERNAME=your_bot_username
make up
```

Then open Settings, prepare the Telegram link, send `/start <token>` to the bot, and
enable Telegram reminders.

## Common commands

```bash
make help        # list all targets
make logs        # tail logs
make test        # run backend tests
make down        # stop the stack
make clean       # stop and wipe the database volume
```

## Layout

- `backend/` — FastAPI + SQLAlchemy + Alembic, talks to Postgres.
- `frontend/` — React + Vite.
- `docker-compose.yml` — db + backend + reminder worker + frontend.
